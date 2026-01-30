#!/usr/bin/env python3
# coding=utf-8

#
# Copyright (c) 2022 Huawei Device Co., Ltd.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import os
import time

from xdevice import ResourceManager
from ohos.drivers import *
from ohos.drivers.constants import TIME_OUT

__all__ = ["OHRustTestDriver"]

LOG = platform_logger("OHRustTestDriver")


@Plugin(type=Plugin.DRIVER, id=DeviceTestType.oh_rust_test)
class OHRustTestDriver(IDriver):
    def __init__(self):
        self.result = ""
        self.error_message = ""
        self.config = None

    def __check_environment__(self, device_options):
        pass

    def __check_config__(self, config):
        pass

    def __execute__(self, request):
        try:
            LOG.debug("Start to execute open harmony rust test")

            self.config = request.config
            self.config.device = request.config.environment.devices[0]
            self.config.target_test_path = "/system/bin"

            suite_file = request.root.source.source_file
            LOG.debug("Testsuite filePath: {}".format(suite_file))

            if not suite_file:
                LOG.error("test source '{}' not exists".format(
                    request.root.source.source_string))
                return

            self.result = "{}.xml".format(
                os.path.join(request.config.report_path,
                             "result", request.get_module_name()))
            self.config.device.set_device_report_path(request.config.report_path)
            self.config.device.device_log_collector.start_hilog_task()
            self._init_oh_rust()
            self._run_oh_rust(suite_file, request)

        except Exception as exception:
            self.error_message = exception
            if not getattr(exception, "error_no", ""):
                setattr(exception, "error_no", "03409")
            LOG.exception(self.error_message, exc_info=False, error_no="03409")
        finally:
            serial = "{}_{}".format(str(request.config.device.__get_serial__()),
                                    time.time_ns())
            log_tar_file_name = "{}_{}".format(
                request.get_module_name(), str(serial).replace(":", "_"))
            self.config.device.device_log_collector.stop_hilog_task(
                log_tar_file_name,
                module_name=request.get_module_name(),
                repeat=request.config.repeat,
                repeat_round=request.get_repeat_round())

            self.result = check_result_report(
                request.config.report_path, self.result, self.error_message)

    def _init_oh_rust(self):
        self.config.device.connector_command("target mount")
        self.config.device.execute_shell_command(
            "mount -o rw,remount,rw /")

    def _run_oh_rust(self, suite_file, request=None):
        # push testsuite file
        self.config.device.push_file(suite_file, self.config.target_test_path)

        # push resource files
        resource_manager = ResourceManager()
        resource_data_dic, resource_dir = \
            resource_manager.get_resource_data_dic(suite_file)
        resource_manager.process_preparer_data(resource_data_dic,
                                               resource_dir,
                                               self.config.device)
        for listener in request.listeners:
            listener.device_sn = self.config.device.device_sn

        parsers = get_plugin(Plugin.PARSER, CommonParserType.oh_rust)
        if parsers:
            parsers = parsers[:1]
        parser_instances = []
        for parser in parsers:
            parser_instance = parser.__class__()
            parser_instance.suite_name = request.get_module_name()
            parser_instance.listeners = request.listeners
            parser_instances.append(parser_instance)
        handler = ShellHandler(parser_instances)

        command = "cd {}; chmod +x *; ./{}".format(
            self.config.target_test_path, os.path.basename(suite_file))
        self.config.device.execute_shell_command(
            command, timeout=TIME_OUT, receiver=handler, retry=0)
        resource_manager.process_cleaner_data(resource_data_dic, resource_dir,
                                              self.config.device)

    def __result__(self):
        return self.result if os.path.exists(self.result) else ""
