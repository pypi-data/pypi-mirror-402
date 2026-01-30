import time
import re

from xdevice import IProxy
from xdevice import convert_serial
from xdevice import platform_logger
from xdevice import Variables

from ohos.utils import is_rpc_unix_socket_running, is_rpc_socket_running
from ohos.utils import dump_pid_info
from ohos.error import ErrorMessage
from ohos.exception import OHOSDeveloperModeNotTrueError
from ohos.exception import OHOSRpcProcessNotFindError
from ohos.exception import OHOSRpcPortNotFindError
from ohos.exception import HDCFPortError
from ohos.exception import OHOSRpcNotRunningError
from ohos.exception import OHOSProxyInitFailed
from ohos.proxy.proxy_base import OpenHarmony

LOG = platform_logger("DeviceUIProxy")

UITEST_NAME = "uitest"
UITEST_PATH = "/system/bin/uitest"
UITEST_SINGLENESS = "singleness"
EXTENSION_NAME = "--extension-name"
UI_PORT = 8012
SUCCESS_CODE = "0"
SO_PATH = "/data/local/tmp/agent.so"
UNIX_SOCKET_NAME = "uitest_socket"


class UIProxy(IProxy):
    rpc_proxy = None

    def __init__(self):
        self.forward_ports_ui = []
        self.use_unix_socket = False

    def __set_device__(self, device):
        self.device = device

    def __reconnect_proxy__(self):
        re_install = self.check_need_install_bin()
        self.start_ui_rpc(re_install_rpc=re_install, reconnect=True)
        host_port = self.fport_ui_tcp_port()
        try:
            self.rpc_proxy.init(port=host_port, addr=self.device.host, device=self.device)
        except Exception as _:
            time.sleep(3)
            self.rpc_proxy.init(port=host_port, addr=self.device.host, device=self.device)

    def __clean_proxy__(self):
        if self.rpc_proxy:
            self.rpc_proxy.close()
        self.rpc_proxy = None
        if not self.kill_uitest:
            self.stop_ui_rpc(kill_uitest=False)
        else:
            self.stop_ui_rpc(kill_uitest=True)
        self.remove_ui_ports()
        setattr(self.device, "_ui_proxy", None)

    def __init_proxy__(self):
        # check uitest
        try:
            self.check_uitest_status()
            self.start_ui_rpc(re_install_rpc=True)
            host_port = self.fport_ui_tcp_port()
            self.rpc_proxy = OpenHarmony(port=host_port, addr=self.device.host, timeout=self.device.rpc_timeout,
                                         device=self.device)
        except (HDCFPortError, OHOSRpcNotRunningError) as error:
            self.__clean_proxy__()
            raise error
        except Exception as error:
            LOG.error('proxy init error: {}.'.format(str(error)))
            LOG.error("DeviceTest-10012 ui_proxy:%s" % str(error))
            self.__clean_proxy__()
            raise OHOSProxyInitFailed(ErrorMessage.Device.Code_0303029.format(error))
        return self.rpc_proxy

    @property
    def kill_uitest(self):
        task_args = Variables.config.taskargs
        return task_args.get("kill_uitest", "").lower() == "true"

    def check_need_install_bin(self):
        ret = self.device.execute_shell_command("ls -l {}".format(SO_PATH))
        LOG.debug(ret)
        if ret is None or "No such file or directory" in ret:
            return True
        return False

    def get_uitest_proc_pid(self):
        # uitest-singleness
        cmd = 'ps -ef | grep {}'.format(UITEST_SINGLENESS)
        proc_running = self.device.execute_shell_command(cmd).strip()
        proc_running = proc_running.split("\n")
        result = None
        for data in proc_running:
            if UITEST_SINGLENESS in data and "grep" not in data and EXTENSION_NAME not in data:
                data = data.split()
                result = data[1]
        return result

    def check_uitest_status(self):
        uitest_version = self.device.uitest_version
        if not self.device.is_root:
            if "inaccessible or not found" in uitest_version:
                raise OHOSDeveloperModeNotTrueError(ErrorMessage.Device.Code_0303021, device=self.device)
        self.use_unix_socket = self.device.ui_socket_mode
        LOG.info('Check uitest running status.')
        uitest_pid = self.get_uitest_proc_pid()
        LOG.info(f'Finish check uitest running status. Uitest pid: {uitest_pid}')

    def start_ui_rpc(self, re_install_rpc: bool = False, reconnect: bool = False):
        if re_install_rpc:
            try:
                OpenHarmony.init_agent_resource(self.device)
            except ImportError as error:
                LOG.debug(str(error))
                LOG.error('please check devicetest extension module is exist.')
                raise error
            except Exception as error:
                LOG.debug(str(error))
                LOG.error('device init UI RPC error.')
                raise error
        if reconnect:
            LOG.info("Before reconnect ui proxy, try to stop it first.")
            self.stop_ui_rpc(reconnect=reconnect)
        if self.device.is_bin and self.check_ui_rpc_status(check_times=1) == SUCCESS_CODE:
            LOG.info('Harmony ui rpc already start!!!!')
            return
        self.start_uitest()
        time.sleep(1)
        check_result = self.check_ui_rpc_status()
        self.check_exception(check_result)

    def stop_ui_rpc(self, kill_uitest: bool = True, reconnect: bool = False):
        if not self.device.get_recover_state():
            LOG.warning("device state is false, skip stop ui rpc.")
            return
        if not kill_uitest:
            return
        uitest_pid = self.get_uitest_proc_pid()
        LOG.debug("uitest pid: {}".format(uitest_pid))
        if uitest_pid:
            if reconnect:
                dump_pid_info(self.device, uitest_pid, UITEST_NAME)
            cmd = 'kill -9 {}'.format(uitest_pid)
            self.device.execute_shell_command(cmd)

    def is_ui_rpc_running(self) -> bool:
        return True if self.get_uitest_proc_pid() else False

    def check_ui_rpc_status(self, check_server: bool = True, check_times: int = 3) -> str:
        for i in range(check_times):
            if self.is_ui_rpc_running():
                break
            else:
                LOG.debug("check Harmony ui rpc failed {} times. try to check again in 1 seconds".format(i + 1))
                time.sleep(1)
        else:
            return ErrorMessage.Device.Code_0303025.code

        for i in range(check_times):
            if not self.use_unix_socket and is_rpc_socket_running(self.device, UI_PORT, check_server=check_server):
                break
            if self.use_unix_socket and is_rpc_unix_socket_running(self.device, UNIX_SOCKET_NAME):
                break
            else:
                LOG.debug("Harmony ui rpc port is not find {} times. try to find again in 1 seconds".format(i + 1))
                time.sleep(1)
        else:
            return ErrorMessage.Device.Code_0303026.code
        return SUCCESS_CODE

    def start_uitest(self):
        result = self.device.execute_shell_command("{} start-daemon singleness".format(UITEST_PATH))
        LOG.debug('start uitest: {}'.format(result))

    def check_exception(self, error_code: str):
        if error_code == SUCCESS_CODE:
            LOG.info("Harmony ui rpc start success!!!!")
            return
        if error_code == ErrorMessage.Device.Code_0303025.code:
            LOG.error('ui rpc is not running!!!!')
            raise OHOSRpcProcessNotFindError(ErrorMessage.Device.Code_0303025, device=self.device)
        elif error_code == ErrorMessage.Device.Code_0303026.code:
            LOG.error(f"Harmony ui rpc port is not find!!!! Is unix: {self.use_unix_socket}")
            raise OHOSRpcPortNotFindError(ErrorMessage.Device.Code_0303026, device=self.device)

    def fport_ui_tcp_port(self) -> int:
        filter_ports = []
        for i in range(3):
            host_port = self.get_host_ui_port(filter_ports=filter_ports)
            if self.use_unix_socket:
                cmd = "fport tcp:{} localabstract:{}".format(host_port, UNIX_SOCKET_NAME)
            else:
                cmd = "fport tcp:{} tcp:{}".format(host_port, UI_PORT)
            result = self.device.connector_command(cmd)
            if "Fail" not in result:
                LOG.debug(f"hdc fport success, ui proxy host_port: {host_port}")
                return host_port
            filter_ports.append(host_port)
            LOG.debug(f"The {i + 1} time HDC fport tcp port fail.")
            from devicetest.utils.util import check_port_state
            check_port_state(host_port)
        else:
            err_msg = ErrorMessage.Device.Code_0303022
            LOG.error(err_msg)
            raise HDCFPortError(err_msg)

    def get_host_ui_port(self, filter_ports: list = None):
        if filter_ports is None:
            filter_ports = []
        from devicetest.utils.util import get_forward_port
        host = self.device.host
        port = None
        host_port = get_forward_port(self.device, host, port, filter_ports)
        self.remove_ui_ports()
        self.forward_ports_ui.append(host_port)
        LOG.info("tcp forward port: {} for {}".format(host_port, convert_serial(self.device.device_sn)))
        return host_port

    def remove_ui_ports(self):
        for port in self.forward_ports_ui:
            if self.use_unix_socket:
                cmd = "fport rm tcp:{} localabstract:{}".format(port, UNIX_SOCKET_NAME)
            else:
                cmd = "fport rm tcp:{} tcp:{}".format(port, UI_PORT)
            self.device.connector_command(cmd)
        self.forward_ports_ui.clear()


class NativeUIProxy(UIProxy):

    def __init_proxy__(self):
        # check uitest
        try:
            self.check_uitest_status()
            self.start_ui_rpc(re_install_rpc=True)
            self.rpc_proxy = OpenHarmony(port=UI_PORT, addr=self.device.host, timeout=self.device.rpc_timeout,
                                         device=self.device)
        except (HDCFPortError, OHOSRpcNotRunningError) as error:
            self.__clean_proxy__()
            raise error
        except Exception as error:
            LOG.error('proxy init error: {}.'.format(str(error)))
            LOG.error("DeviceTest-10012 ui_proxy:%s" % str(error))
            self.__clean_proxy__()
            raise OHOSProxyInitFailed(ErrorMessage.Device.Code_0303029.format(error))
        return self.rpc_proxy
