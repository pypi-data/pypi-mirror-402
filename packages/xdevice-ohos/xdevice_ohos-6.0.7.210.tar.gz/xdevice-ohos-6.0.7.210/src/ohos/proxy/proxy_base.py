import json
import traceback
import re
import zipfile
import os
import time
from socket import socket

from xdevice import AgentMode
from xdevice import convert_serial
from xdevice import Variables
from xdevice import check_uitest_version
from devicetest.controllers.device import OSBase
from devicetest import RESOURCE_PATH
from devicetest.core.constants import DeviceConstants
from devicetest.utils.time_util import TimeHandler
from devicetest.utils.util import get_local_ip_address
from devicetest.utils.util import compare_version
from devicetest.core.exception import AppInstallError
from devicetest.core.exception import RPCException
from devicetest.core.exception import CreateUiDriverFailError
from devicetest.core.exception import ConnectAccessibilityFailError
from devicetest.error import ErrorCategory
from devicetest.error import ErrorMessage
from devicetest.utils.util import compare_versions_by_product
from ohos.error import ErrorMessage as ohosErrorMessage
from ohos.exception import OHOSRpcHandleError

DEVICETEST_HAP_PACKAGE_NAME = "com.ohos.devicetest"
DEVICETEST_HAP_ENTRY_NAME = "entry"
UITEST_SINGLENESS = "singleness"
EXTENSION_NAME = "--extension-name"
BASE_TIME = "2023-10-01 00:00:00"
AGENT_CLEAR_PATH = ["app", "commons-", "agent", "libagent_antry"]
SUCCESS_CODE = "0"


class HarmonyProxy:
    def __init__(self, obj, attr):
        self.obj = obj
        self.attr = attr

    def __getattr__(self, name):
        def proxy_call(*args, **kwargs):
            if len(args) == 0 and len(kwargs) == 0:
                args = "context", None
            elif len(args) == 1:
                if isinstance(args[0], dict):
                    args = json.dumps(args[0], ensure_ascii=False,
                                      separators=(',', ':'))
                args = "context", args
            elif len(kwargs) != 0:
                args = "context", json.dumps(kwargs, ensure_ascii=False,
                                             separators=(',', ':'))
            self.obj.log.debug("[{}.{}] {}.{}({})".format(
                self.obj.device.device_id, convert_serial(self.obj.device.device_sn),
                self.attr, name, str(args[1])))
            if self.obj.device.oh_module_package is None:
                from ohos.environment.device import Device
                if (isinstance(self.obj.device, Device) and
                        self.obj.device.is_bin and
                        self.attr == "UiTestDeamon"):
                    ret = self.obj._abc_rpc(DeviceConstants.OH_DEVICETEST_BUNDLE_NAME + self.attr, name, kwargs)
                else:
                    ret = self.obj._rpc(DeviceConstants.OH_DEVICETEST_BUNDLE_NAME + self.attr, name, *args)
            else:
                try:
                    # OpenHarmony 动态moudle加载 需要传入bundleName和abilityName
                    self.obj.log.debug(
                        "self.obj.device.module_package :{}, self.obj.device.module_ability_name :{}"
                        .format(self.obj.device.oh_module_package,
                                self.obj.device.module_ablity_name))
                    ret = self.obj._rpc_for_oh_module(
                        self.obj.device.oh_module_package + "." + self.attr, name,
                        self.obj.device.module_ablity_name,
                        *args)
                finally:
                    self.obj.device.set_module_package(None)
                    self.obj.device.set_moudle_ablity_name(None)
            self.obj.log.debug("[{}.{}] Recv: {}".format(self.attr, name, str(ret)))
            if "Can't load class" in str(ret):
                self.obj.log.warning(
                    "please check project.config file, the 'initdevice' maybe False!")
            if str(ret).startswith("false,"):
                return False
            return ret

        return proxy_call


class HarmonyBase(OSBase):

    def __getattr__(self, name):
        base_proxy = HarmonyProxy(self, name)
        setattr(self, name, base_proxy)
        return base_proxy


class OpenHarmony(HarmonyBase):
    def __init__(self, port=DeviceConstants.PORT, addr=DeviceConstants.HOST,
                 timeout=300, device=None):
        super(OpenHarmony, self).__init__(port, addr, timeout, device)
        self._device = device
        self.log = device.log
        self.last_rpc_fault = None
        self.log.debug('init OpenHarmony root')

    def __getattr__(self, name):
        base_proxy = HarmonyProxy(self, name)
        setattr(self, name, base_proxy)
        return base_proxy

    def _rpc(self, module, method, *args):
        data = {'module': module,
                'method': method,
                'params': args,
                'call': "xdevice",
                'request_id': TimeHandler.get_now_datetime()}

        request = json.dumps(data,
                             ensure_ascii=False,
                             separators=(',', ':'))
        return self._safe_send(request, is_bin=False)

    def _abc_rpc(self, module, method, args):
        data = {'module': module,
                'method': method,
                'params': args,
                'call': "xdevice",
                'request_id': TimeHandler.get_now_datetime()}

        request = json.dumps(data,
                             ensure_ascii=False,
                             separators=(',', ':'))
        return self._safe_send(request, is_bin=True)

    def _rpc_for_oh_module(self, module, method, ability_name, *args):
        data = {'module': module,
                'method': method,
                'ability_name': ability_name,
                'params': args,
                'call': "xdevice",
                'request_id': TimeHandler.get_now_datetime()}

        request = json.dumps(data,
                             ensure_ascii=False,
                             separators=(',', ':'))
        return self._safe_send(request, is_bin=False)

    def rpc_for_hypium(self, request):
        new_request = json.loads(request)
        new_request.update({'call': "xdevice"})
        new_request = json.dumps(new_request, ensure_ascii=False, separators=(',', ':'))
        return self._safe_send(new_request,
                               is_bin=self._device.is_bin
                               if hasattr(self._device, "is_bin") else False)

    def _recv(self, sock: socket, isbyte: bool = False) -> str:
        response = b''
        while True:
            data = sock.recv(1024 * 1024)
            response += data
            if len(data) == 0 or data[-1:] == b'\n':
                break

        if len(response) == 0:
            # Windows上,当客户端在接收消息的时候,服务端被杀,
            # 客户端不会抛异常
            # ,会收到0字节;正常服务器响应空字符串时,客户端接收的是"\n"
            ui_proxy = getattr(self.device, "_ui_proxy", None)
            if ui_proxy:
                raise RPCException(ErrorMessage.Device.Code_0202002)

        if isbyte:
            return response

        response = str(response, encoding="utf-8").strip()

        return response

    def _check_recv_request_id(self, request: str, sock: socket, isbyte: bool = False, is_bin: bool = False):
        """
        :param request: 消息
        :param sock: socket
        :param isbyte: 是否返回byte
        :param is_bin: 是否是bin模式
        :return:
        """
        if is_bin:
            return self._recv(sock=sock, isbyte=isbyte)
        else:
            response: str = self._recv(sock=sock, isbyte=isbyte)
            if isbyte:
                return response
            # 多消息返回需要重新分割
            response_splits = response.split("}\n")
            response_splits = [x + "}" for x in response_splits[:-1]] + [response_splits[-1]]
            # 从最后一条开始找
            response_splits.reverse()

            for res in response_splits:
                try:
                    response_json = json.loads(res)
                    target_request_id = json.loads(request).get("request_id", None)
                    recv_request_id = response_json.get("request_id", None)
                    if recv_request_id == "-1":
                        self.log.debug("recv message: {}".format(res))
                        raise OHOSRpcHandleError(ohosErrorMessage.Device.Code_0303032)
                    if recv_request_id == target_request_id:
                        return res
                    else:
                        self.log.debug("message is {}".format(res))
                        self.log.debug("recv request id {} not equal target request id {}. "
                                       "need to recv again".format(recv_request_id, target_request_id))
                except OHOSRpcHandleError as e:
                    raise e
                except Exception:
                    # loads失败，该消息有问题，非正常消息直接返回
                    return response
            else:
                # 分割后的消息全都不是对应的request id 重新接收
                return self._check_recv_request_id(request=request, sock=sock, isbyte=isbyte, is_bin=is_bin)

    def _send(self, request, sock=None, isbyte=False, is_bin=False):
        """
        ohos重写send方法
        :param request: 消息
        :param sock: socket
        :param isbyte: 是否返回byte
        :param is_bin: 是否是bin模式
        :return:
        :return:
        """
        if sock is None:
            sock = self.sock

        if sock is not None:
            if is_bin:
                sock.sendall(request.encode("utf-8") + b'\n')
            else:
                sock.sendall(("1" + request).encode("utf-8") + b'\n')

            return self._check_recv_request_id(request, sock=sock, isbyte=isbyte, is_bin=is_bin)

        return "false"

    def _safe_send(self, request, sock=None, isbyte=False, is_bin=False):
        local_host = get_local_ip_address()
        if local_host is None:
            local_host = self.device.host
        send_request = json.loads(request)
        send_request["client"] = \
            local_host if local_host is not None else "127.0.0.1"
        send_request = json.dumps(send_request, ensure_ascii=False, separators=(',', ':'))
        try:
            self.log.debug("sendRequest: {}".format(send_request))
            ret = self._send(send_request, sock=sock, isbyte=isbyte, is_bin=is_bin)
            if b'' == ret:
                return b''
            self.log.debug("@recv rpc msg: {}".format(ret))
            self._check_hypium_message(send_request, ret)
        except Exception as e:
            self.log.debug(traceback.format_exc())
            self.log.error("[OpenHarmony] Exception on request to device")
            if self._device is not None:
                if isinstance(e, CreateUiDriverFailError):
                    # 非bin模式下,wukong存不存在都要杀uitest
                    # bin模式下,wukong不存在就报错
                    wukong_exist = self._kill_if_exist_wukong(self._device)
                    if not is_bin:
                        self._kill_uitest(self._device)
                    elif is_bin and not wukong_exist:
                        raise e
                self._wait_accessibility(self._device, request)
                if self._device.reconnecttimes == DeviceConstants.RECONNECT_TIMES:
                    self._device.reconnecttimes = 0
                    error_msg = ErrorMessage.Device.Code_0202001.format("OpenHarmony", DeviceConstants.RECONNECT_TIMES)
                    self.log.error(error_msg)
                    raise RPCException(error_msg) from e

                self.log.debug(
                    "[OpenHarmony] %d times to reconnect rpc socket "
                    "device: %s" % (self._device.reconnecttimes + 1,
                                    self._device.device_id))
                self._device.reconnecttimes += 1
                if self._check_if_request_is_hypium(request, is_bin):
                    self._device.reconnect(proxy=AgentMode.bin)
                else:
                    self._device.reconnect(proxy=AgentMode.hap)
                self.log.debug(
                    "[OpenHarmony] Send request {} again".format(request))
                # bin模式下hypium的接口直接不重发，直接返回, api为driver.create需要重发
                if not self._check_if_request_is_hypium(request, is_bin, check_driver_create=True):
                    self.log.debug("[OpenHarmony] request is not hypium msg or "
                                   "(is hypium msg and api is create driver) need to resend.")
                    ret = self._safe_send(request, sock=sock, isbyte=isbyte, is_bin=is_bin)
                else:
                    self.log.debug("[OpenHarmony] request is hypium msg, no need to resend.")
                    reply = {"exception": "INTERNAL_ERROR Cannot translate frontend object to backend object"}
                    ret = json.dumps(reply, ensure_ascii=False, separators=(',', ':'))
                if b'' == ret:
                    return b''
                self.log.debug("@recv rpc msg: {}".format(str(ret)))
                self._device.reconnecttimes = 0


        if ret == "false":
            ret = False
        if ret == "true":
            ret = True

        return ret

    def _check_if_request_is_hypium(self, request, is_bin=False, check_driver_create: bool = False):
        if not is_bin:
            return False
        send_request = json.loads(request)
        if send_request.get("method", None) == "callHypiumApi":
            if check_driver_create:
                params = send_request.get("params", {})
                if params.get("api", None) == "Driver.create":
                    return False
            return True
        return False

    @classmethod
    def _check_uitest_version(cls, device, base_version):
        uitest_version = device.uitest_version
        return check_uitest_version(uitest_version, base_version)

    @classmethod
    def init_agent_resource(cls, device):
        cls._device = device
        cls.log = device.log
        cls._init_so_resource(device)

    @classmethod
    def _parse_old_version(cls, version: str) -> str:
        matcher = re.search(r'\d{1,3}[.]\d{1,3}[.]\d{1,3}', version)
        device_link = matcher.group(0) if matcher else "0.0.0"
        return device_link

    @classmethod
    def _parse_new_version(cls, version: str) -> str:
        version = version[version.find("#") + 1:]
        return cls._parse_old_version(version)

    @classmethod
    def _init_so_resource(cls, device):
        folder_path = os.path.join(RESOURCE_PATH, 'res', 'prototype', 'native')
        file_postfix = ".so"
        device_agent_path = "/data/local/tmp/agent.so"
        cls.log.debug("{}".format("Init native agent..."))
        cls.log.debug("{}".format(device.arch))
        arch = "arm64"
        if "x86_64" in device.arch:
            file_postfix = ".x86_64_so"
            arch = "x86-64"
        agent_filename = ""
        agent_path = ""
        local_link = ""
        base_version_5_1_1_3 = tuple("5.1.1.3".split("."))
        base_version_5_1_1_2 = tuple("5.1.1.2".split("."))
        uitest_version = device.uitest_version
        if file_postfix == ".x86_64_so":
            cls.log.debug("Using x86 1.1.9 agent version")
            local_link = "1.1.9"
            agent_path = os.path.join(folder_path, "uitest_agent_v1.1.9.x86_64_so")
        elif device.ui_socket_mode:
            # if uitest version greater than 6.0.2.1 use unix socket
            local_link = "1.2.2"
            agent_path = os.path.join(folder_path, f"uitest_agent_v{local_link}.so")
        elif compare_version(uitest_version, base_version_5_1_1_3, r'^\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}'):
            # if uitest version greater than 5.1.1.3 uitest后投屏服务兼容老版本
            local_link = "1.1.10"
            agent_path = os.path.join(folder_path, f"uitest_agent_v{local_link}.so")
        elif compare_version(uitest_version, base_version_5_1_1_2, r'^\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}'):
            # if uitest version equal to 5.1.1.3
            local_link = "1.1.5"
            agent_path = os.path.join(folder_path, f"uitest_agent_v{local_link}.so")
        else:
            # if uitest version less than or equal to 5.1.1.2
            local_link = "1.1.3"
            agent_path = os.path.join(folder_path, f"uitest_agent_v{local_link}.so")
        cls.log.info(f"uitest version: {uitest_version}. Using {local_link} agent version")
        # 获取设备端的版本号
        device_ver_info = cls._device.execute_shell_command(
            "cat {} | grep -a UITEST_AGENT_LIBRARY".format(device_agent_path))
        cls.log.info("{}".format(device_ver_info))
        if "#" in device_ver_info:
            device_link = cls._parse_new_version(device_ver_info)
        else:
            device_link = cls._parse_old_version(device_ver_info)
        need_update = False
        cls.log.info("local agent version {}, device agent version {}".format(local_link, device_link))
        device_link = tuple(device_link.split("."))
        local_link = tuple(local_link.split("."))
        # 如果模式不对直接更新
        if local_link[1] != device_link[1] or device_link < local_link:
            need_update = True

        if not need_update:
            agent_so_arch_info = cls._device.execute_shell_command("file {}".format(device_agent_path))
            cls.log.debug("{}".format(agent_so_arch_info))
            if arch not in agent_so_arch_info:
                cls.log.debug("so arch is not same. need to update!")
                need_update = True

        if need_update:
            cls.log.info("start update agent, path is {}".format(agent_path))
            # if uitest running kill first
            uitest_pid = cls.get_uitest_proc_pid(device)
            if uitest_pid:
                device.execute_shell_command('kill -9 {}'.format(uitest_pid))
            # check if has old link file
            for file in AGENT_CLEAR_PATH:
                cls._device.execute_shell_command("rm /data/local/tmp/{}*".format(file))
            cls._device.push_file(agent_path, device_agent_path)
            cls.log.info("Update agent finish.")
        else:
            cls.log.info("Device agent is up to date!")

    @classmethod
    def get_uitest_proc_pid(cls, device):
        # uitest-singleness
        cmd = 'ps -ef | grep {}'.format(UITEST_SINGLENESS)
        proc_running = device.execute_shell_command(cmd).strip()
        proc_running = proc_running.split("\n")
        result = None
        for data in proc_running:
            if UITEST_SINGLENESS in data and "grep" not in data and EXTENSION_NAME not in data:
                data = data.split()
                result = data[1]
        return result

    @classmethod
    def _kill_if_exist_wukong(cls, device) -> bool:
        # 获取wukong程号然后杀掉,不存在就返回False
        pids_res = device.execute_shell_command("pidof wukong")
        cls.log.debug("wukong pid : {}".format(pids_res))
        if not pids_res:
            return False
        for pid in pids_res.strip().split("\n"):
            device.execute_shell_command("kill -9 {}".format(pid))
        time.sleep(1)
        return True

    @classmethod
    def _kill_uitest(cls, device):
        # 获取uitest程号然后杀掉
        pids_res = device.execute_shell_command("ps -A | grep uitest")
        cls.log.debug("uitest pid : {}".format(pids_res))
        if not pids_res:
            return
        for process in pids_res.strip().split("\n"):
            m = re.match("^(\\s*\\d+\\s+)", process)
            if m:
                pid = m.group(1).strip()
                if pid.isdigit():
                    device.execute_shell_command("kill -9 {}".format(pid))
        time.sleep(1)

    @classmethod
    def _wait_accessibility(cls, device, request: str):
        # 非UI操作不等待
        if not hasattr(device, "is_oh") or not cls._check_ui_action(request):
            return
        # uitest版本大于5.0.0.0不需要等待无障碍
        uitest_version = device.execute_shell_command("/system/bin/uitest --version")
        base_version = tuple("5.0.0.0".split("."))
        if check_uitest_version(uitest_version, base_version):
            return
        # 产品版本大于5.0.0.22不需要等待无障碍
        product_info = device.execute_shell_command("param get const.product.software.version").strip().split(" ")
        if len(product_info) == 2:
            device_version = product_info[1]
            if compare_versions_by_product(device_version, "5.0.0.22"):
                return
        start_time = time.time()  # 获取当前时间
        is_accessibility_alive = False
        while time.time() - start_time < 60:  # 60秒内持续等待无障碍
            # 检测无障碍是否已被拉起
            pids_res = device.execute_shell_command("pidof accessibility")
            cls.log.debug("waiting accessibility")
            if pids_res:
                is_accessibility_alive = True
                cls.log.debug("accessibility pid is {}".format(pids_res))
                break
            time.sleep(2)
        if not is_accessibility_alive:
            raise ConnectAccessibilityFailError(ErrorMessage.Device.Code_0202006)

    @classmethod
    def _check_hypium_message(cls, request, ret):
        try:
            send_request_dict = json.loads(request)
            params = send_request_dict.get("params")
            if not params or not isinstance(ret, str):
                return
            if isinstance(params, dict):
                message_type = params.get("message_type")
            else:
                message_type = None

        except Exception as error:
            cls.log.debug("parse request json error: {}".format(error))
            return

        try:
            datas_dict = json.loads(ret)
            if message_type != "hypium":
                return
            if not isinstance(datas_dict, dict):
                raise RPCException(ErrorMessage.Device.Code_0202010)
        except Exception as error:
            cls.log.debug("parse ret json error: {}".format(error))
            if message_type == "hypium":
                raise RPCException(ErrorMessage.Device.Code_0202010)
            else:
                return

        exception = datas_dict.get("exception")
        if exception and "INTERNAL_ERROR Cannot find backend method" in exception:
            raise CreateUiDriverFailError(ErrorMessage.Device.Code_0202007)
        if exception and "RET_ERR_CONNECTION_EXIST" in exception:
            raise CreateUiDriverFailError(ErrorMessage.Device.Code_0202009)
        for param in params:
            if not param:
                continue
            if "Driver.create" in param:
                if not datas_dict.get("result"):
                    error_msg = ErrorMessage.Device.Code_0202008
                    cls.log.error(error_msg)
                    raise CreateUiDriverFailError(error_msg)

    @classmethod
    def _check_ui_action(cls, request: str):
        # 判断当前请求是否为UI操作
        try:
            if not isinstance(request, str):
                return False
            send_request_dict = json.loads(request)
            module = send_request_dict.get("module")
            if not module:
                return False
        except Exception as error:
            cls.log.debug("parse json error: {}".format(error))
            return False
        return module == "com.ohos.devicetest.hypiumApiHelper" or module == "com.ohos.devicetest.UiTestDeamon"

    def get_last_rpc_fault(self):
        return self.last_rpc_fault
