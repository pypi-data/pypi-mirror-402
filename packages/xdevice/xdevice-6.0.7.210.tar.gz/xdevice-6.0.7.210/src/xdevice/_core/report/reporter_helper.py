#!/usr/bin/env python3
# coding=utf-8

#
# Copyright (c) 2020-2022 Huawei Device Co., Ltd.
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
import platform
from dataclasses import dataclass
from typing import Union
from xml.dom import minidom
from xml.etree import ElementTree

from _core.logger import platform_logger
from _core.report.encrypt import check_pub_key_exist
from _core.report.encrypt import do_rsa_decrypt
from _core.report.encrypt import do_rsa_encrypt
from _core.exception import ParamError
from _core.constants import CaseResult
from _core.constants import FilePermission

LOG = platform_logger("ReporterHelper")


@dataclass
class ReportConstant:
    # report name constants
    summary_data_report = "summary_report.xml"
    summary_vision_report = "summary_report.html"
    details_vision_report = "details_report.html"
    failures_vision_report = "failures_report.html"
    passes_vision_report = "passes_report.html"
    ignores_vision_report = "ignores_report.html"
    task_info_record = "task_info.record"
    summary_ini = "summary.ini"
    summary_report_hash = "summary_report.hash"
    task_run_log = "task_log.log"
    module_run_log = "module_run.log"
    report_data_json = "report_data.json"

    # exec_info constants
    platform = "platform"
    test_type = "test_type"
    device_name = "device_name"
    host_info = "host_info"
    test_time = "test_time"
    log_path = "log_path"
    log_path_title = "Log Path"
    execute_time = "execute_time"
    device_label = "device_label"

    # summary constants
    product_info = "productinfo"
    product_info_ = "product_info"
    modules = "modules"
    run_modules = "runmodules"
    run_modules_ = "run_modules"
    name = "name"
    time = "time"
    total = "total"
    tests = "tests"
    passed = "passed"
    errors = "errors"
    disabled = "disabled"
    failures = "failures"
    blocked = "blocked"
    ignored = "ignored"
    completed = "completed"
    unavailable = "unavailable"
    not_run = "notrun"
    message = "message"
    report = "report"
    repeat = "repeat"
    round = "round"
    devices = "devices"
    result_content = "result_content"

    # case result constants
    module_name = "modulename"
    module_name_ = "module_name"
    result = "result"
    result_kind = "result_kind"
    status = "status"
    run = "run"
    true = "true"
    false = "false"
    skip = "skip"
    disable = "disable"
    class_name = "classname"
    level = "level"
    empty_name = "-"

    # time constants
    time_stamp = "timestamp"
    start_time = "starttime"
    end_time = "endtime"
    time_format = "%Y-%m-%d %H:%M:%S"

    # xml tag constants
    failure = "failure"
    test_suites = "testsuites"
    test_suite = "testsuite"
    test_case = "testcase"
    test = "test"

    # report title constants
    failed = "failed"
    error = "error"


class DataHelper:
    LINE_BREAK = "\n"
    LINE_BREAK_INDENT = "\n  "
    INDENT = "  "
    DATA_REPORT_SUFFIX = ".xml"

    def __init__(self):
        pass

    @staticmethod
    def parse_data_report(data_report):
        if "<" not in data_report and os.path.exists(data_report):
            with open(data_report, 'r', encoding='UTF-8', errors="ignore") as \
                    file_content:
                data_str = file_content.read()
        else:
            data_str = data_report

        for char_index in range(32):
            if char_index in [10, 13]:  # chr(10): LF, chr(13): CR
                continue
            data_str = data_str.replace(chr(char_index), "")
        try:
            return ElementTree.fromstring(data_str)
        except SyntaxError as error:
            LOG.error("%s %s", data_report, error.args)
            return ElementTree.Element("empty")

    @staticmethod
    def set_element_attributes(element, element_attributes):
        for key, value in element_attributes.items():
            element.set(key, str(value))

    @classmethod
    def initial_element(cls, tag, tail, text):
        element = ElementTree.Element(tag)
        element.tail = tail
        element.text = text
        return element

    def initial_suites_element(self):
        return self.initial_element(ReportConstant.test_suites,
                                    self.LINE_BREAK, self.LINE_BREAK_INDENT)

    def initial_suite_element(self):
        return self.initial_element(ReportConstant.test_suite,
                                    self.LINE_BREAK_INDENT,
                                    self.LINE_BREAK_INDENT + self.INDENT)

    def initial_case_element(self):
        return self.initial_element(ReportConstant.test_case,
                                    self.LINE_BREAK_INDENT + self.INDENT, "")

    def initial_test_element(self):
        return self.initial_element(ReportConstant.test,
                                    self.LINE_BREAK + self.INDENT * 3, "")

    @classmethod
    def update_suite_result(cls, suite, case):
        update_time = round(float(suite.get(
            ReportConstant.time, 0)) + float(
            case.get(ReportConstant.time, 0)), 3)
        suite.set(ReportConstant.time, str(update_time))
        update_tests = str(int(suite.get(ReportConstant.tests, 0)) + 1)
        suite.set(ReportConstant.tests, update_tests)
        if case.findall('failure'):
            update_failures = str(int(suite.get(ReportConstant.failures, 0)) + 1)
            suite.set(ReportConstant.failures, update_failures)

    @classmethod
    def get_summary_result(cls, report_path, file_name, key=None, **kwargs):
        reverse = kwargs.get("reverse", False)
        file_prefix = kwargs.get("file_prefix", None)
        data_reports = cls._get_data_reports(report_path, file_prefix)
        if not data_reports:
            return None
        if key:
            data_reports.sort(key=key, reverse=reverse)
        summary_result = None
        need_update_attributes = [ReportConstant.tests, ReportConstant.errors,
                                  ReportConstant.failures,
                                  ReportConstant.disabled,
                                  ReportConstant.unavailable]
        for data_report in data_reports:
            data_report_element = cls.parse_data_report(data_report)
            if not list(data_report_element):
                continue
            if not summary_result:
                summary_result = data_report_element
                continue
            if not summary_result or not data_report_element:
                continue
            for data_suite in data_report_element:
                for summary_suite in summary_result:
                    if data_suite.get("name", None) == \
                            summary_suite.get("name", None):
                        for data_case in data_suite:
                            for summary_case in summary_suite:
                                if data_case.get("name", None) == \
                                        summary_case.get("name", None):
                                    break
                            else:
                                summary_suite.append(data_case)
                                DataHelper.update_suite_result(summary_result,
                                                               data_case)
                                DataHelper.update_suite_result(summary_suite,
                                                               data_case)
                        break
                else:
                    summary_result.append(data_suite)
                    DataHelper._update_attributes(summary_result, data_suite,
                                                  need_update_attributes)
        if summary_result:
            cls.generate_report(summary_result, file_name)
        return summary_result

    @classmethod
    def _get_data_reports(cls, report_path, file_prefix=None):
        if not os.path.isdir(report_path):
            return []
        data_reports = []
        for root, _, files in os.walk(report_path):
            for file_name in files:
                if not file_name.endswith(cls.DATA_REPORT_SUFFIX):
                    continue
                if file_prefix and not file_name.startswith(file_prefix):
                    continue
                data_reports.append(os.path.join(root, file_name))
        return data_reports

    @classmethod
    def _update_attributes(cls, summary_element, data_element,
                           need_update_attributes):
        for attribute in need_update_attributes:
            updated_value = int(summary_element.get(attribute, 0)) + \
                            int(data_element.get(attribute, 0))
            summary_element.set(attribute, str(updated_value))
        # update time
        updated_time = round(float(summary_element.get(
            ReportConstant.time, 0)) + float(
            data_element.get(ReportConstant.time, 0)), 3)
        summary_element.set(ReportConstant.time, str(updated_time))

    @staticmethod
    def generate_report(element, result_xml):
        is_pub_key_exist = check_pub_key_exist()
        old_element = None
        # 如果存在同名的结果xml文件，先合并新旧测试结果数据，再生成新的结果xml
        if os.path.exists(result_xml):
            if is_pub_key_exist:
                with open(result_xml, "rb") as xml_f:
                    content = xml_f.read()
                result_content = do_rsa_decrypt(content)
                old_element = DataHelper.parse_data_report(result_content)
            else:
                old_element = DataHelper.parse_data_report(result_xml)
        if old_element is not None:
            DataHelper.merge_result_xml(element, old_element)
            element = old_element

        if is_pub_key_exist:
            plain_text = DataHelper.to_string(element)
            try:
                cipher_text = do_rsa_encrypt(plain_text)
            except ParamError as error:
                LOG.error(error, error_no=error.error_no)
                cipher_text = b""
            if platform.system() == "Windows":
                flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_BINARY
            else:
                flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
            file_name_open = os.open(result_xml, flags, FilePermission.mode_755)
            with os.fdopen(file_name_open, "wb") as file_handler:
                file_handler.write(cipher_text)
                file_handler.flush()
        else:
            tree = ElementTree.ElementTree(element)
            tree.write(result_xml, encoding="UTF-8", xml_declaration=True,
                       short_empty_elements=True)
        LOG.info("Generate data report: %s", result_xml)

    @staticmethod
    def to_string(element):
        return str(
            ElementTree.tostring(element, encoding='UTF-8', method='xml'),
            encoding="UTF-8")

    @staticmethod
    def to_pretty_xml(element: Union[str, ElementTree.Element]):
        if isinstance(element, ElementTree.Element):
            element_str = DataHelper.to_string(element)
        else:
            element_str = element
        pretty_xml = minidom.parseString(element_str).toprettyxml(indent='  ', newl='')
        return pretty_xml

    @staticmethod
    def _get_element_attrs(element: ElementTree.Element):
        attr = {
            ReportConstant.time: "0", ReportConstant.tests: "0", ReportConstant.disabled: "0",
            ReportConstant.errors: "0", ReportConstant.failures: "0", ReportConstant.ignored: "0",
            ReportConstant.unavailable: "0"
        }
        for name, default_val in attr.items():
            attr.update({name: element.get(name, default_val).strip() or default_val})
        return attr

    @staticmethod
    def _get_element_testsuite(testsuites: ElementTree.Element):
        result, duplicate_elements = {}, []
        for t in testsuites:
            testsuite_name = t.get(ReportConstant.name, "")
            if testsuite_name not in result.keys():
                result.update({testsuite_name: t})
                continue
            duplicate_elements.append(t)
            DataHelper._merge_testsuite(t, result.get(testsuite_name))
        # 剔除同名的testsuite节点
        for t in duplicate_elements:
            testsuites.remove(t)
        return result

    @staticmethod
    def _merge_attrs(src: dict, dst: dict):
        """merge src to dst"""
        attr = {
            ReportConstant.time: "0", ReportConstant.tests: "0", ReportConstant.disabled: "0",
            ReportConstant.errors: "0", ReportConstant.failures: "0", ReportConstant.ignored: "0",
            ReportConstant.unavailable: "0"
        }
        for name, default_val in attr.items():
            dst_val = str(dst.get(name, default_val)).strip() or default_val
            src_val = str(src.get(name, default_val)).strip() or default_val
            if name in [ReportConstant.time]:
                # 情况1：浮点数求和，并四舍五入
                new_val = round(float(dst_val) + float(src_val), 3)
            else:
                # 情况2：整数求和
                new_val = int(dst_val) + int(src_val)
            dst.update({name: str(new_val)})

    @staticmethod
    def _merge_testsuite(_new: ElementTree.Element, _old: ElementTree.Element):
        """遍历新旧测试套的用例，将用例执行机记录合并到旧结果xml"""
        for new_case in _new:
            new_case_name = new_case.get(ReportConstant.name, "")
            exist_case = None
            for old_case in _old:
                old_case_name = old_case.get(ReportConstant.name, "")
                if old_case_name == new_case_name:
                    exist_case = old_case
                    break
            """用例结果合并策略：新替换旧，pass替换fail
            new_case    old_case    final_case
            pass        pass        new_case
            pass        fail        new_case
            fail        pass        old_case
            fail        fail        new_case
            """
            if exist_case is None:
                _old.append(new_case)
                continue
            merge_case = new_case
            new_case_result, _ = Case.get_case_result(new_case)
            old_case_result, _ = Case.get_case_result(exist_case)
            if new_case_result == CaseResult.failed and old_case_result == CaseResult.passed:
                merge_case = exist_case
            if merge_case == new_case:
                _old.remove(exist_case)
                _old.append(new_case)

        # 重新生成testsuite节点的汇总数据
        testsuite_attr = {
            ReportConstant.time: 0, ReportConstant.tests: len(_old), ReportConstant.disabled: 0,
            ReportConstant.errors: 0, ReportConstant.failures: 0, ReportConstant.ignored: 0,
            ReportConstant.message: _new.get(ReportConstant.message, ""),
            ReportConstant.report: _new.get(ReportConstant.report, "")
        }
        for ele_case in _old:
            case_attr = {
                ReportConstant.time: ele_case.get(ReportConstant.time, "0")
            }
            case_result, _ = Case.get_case_result(ele_case)
            if case_result == CaseResult.failed:
                name = ReportConstant.failures
            elif case_result == CaseResult.blocked:
                name = ReportConstant.disabled
            elif case_result == CaseResult.ignored:
                name = ReportConstant.ignored
            else:
                name = ""
            if name:
                # 表示对应的结果统计+1
                case_attr.update({name: "1"})
            DataHelper._merge_attrs(case_attr, testsuite_attr)
        for k, v in testsuite_attr.items():
            if k in [ReportConstant.unavailable]:
                continue
            _old.set(k, v)

    @staticmethod
    def merge_result_xml(_new: ElementTree.Element, _old: ElementTree.Element):
        """因旧结果xml里的数据是增长的，故将新结果xml里的数据合并到旧结果xml"""
        LOG.debug("merge test result")
        # 合并testsuite节点
        testsuite_dict_new = DataHelper._get_element_testsuite(_new)
        testsuite_dict_old = DataHelper._get_element_testsuite(_old)
        all_testsuite_names = set(list(testsuite_dict_new.keys()) + list(testsuite_dict_old.keys()))
        for name in all_testsuite_names:
            testsuite_new = testsuite_dict_new.get(name)
            testsuite_old = testsuite_dict_old.get(name)
            # 若新结果xml无数据，无需合并数据
            if not testsuite_new:
                continue
            if testsuite_old:
                # 若新旧结果xml均有数据，先合并新旧结果xml的数据，再合并到旧结果xml
                DataHelper._merge_testsuite(testsuite_new, testsuite_old)
            else:
                # 若旧结果xml无数据，直接将新结果xml合并到旧结果xml
                _old.append(testsuite_new)

        # 重新生成testsuites节点的汇总数据
        attr = {
            ReportConstant.time: "0", ReportConstant.tests: "0", ReportConstant.disabled: "0",
            ReportConstant.errors: "0", ReportConstant.failures: "0", ReportConstant.ignored: "0",
            ReportConstant.unavailable: _new.get(ReportConstant.unavailable, "0"),
            ReportConstant.message: _new.get(ReportConstant.message, ""),
            # 不更新开始和结束时间
            ReportConstant.start_time: _new.get(ReportConstant.start_time, ""),
            ReportConstant.end_time: _new.get(ReportConstant.end_time, "")
        }
        for ele_testsuite in _old:
            DataHelper._merge_attrs(DataHelper._get_element_attrs(ele_testsuite), attr)
        for k, v in attr.items():
            _old.set(k, v)


@dataclass
class ExecInfo:
    keys = [ReportConstant.platform, ReportConstant.test_type,
            ReportConstant.device_name, ReportConstant.host_info,
            ReportConstant.test_time, ReportConstant.execute_time,
            ReportConstant.device_label]
    test_type = ""
    device_name = ""
    host_info = ""
    test_time = ""
    log_path = ""
    platform = ""
    execute_time = ""
    product_info = dict()
    device_label = ""
    repeat = 1


class Result:

    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.blocked = 0
        self.ignored = 0
        self.unavailable = 0

    def get_total(self):
        return self.total

    def get_passed(self):
        return self.passed


class Suite:
    keys = [ReportConstant.module_name_, ReportConstant.name,
            ReportConstant.time, ReportConstant.total, ReportConstant.passed,
            ReportConstant.failed, ReportConstant.blocked, ReportConstant.ignored]
    module_name = ReportConstant.empty_name
    name = ""
    time = ""
    report = ""

    def __init__(self):
        self.message = ""
        self.result = Result()
        self.cases = []  # need initial to create new object

    def get_cases(self):
        return self.cases

    def set_cases(self, element):
        if not element:
            LOG.debug("%s has no testcase",
                      element.get(ReportConstant.name, ""))
            return

        # get case context and add to self.cases
        for child in element:
            case = Case()
            case.module_name = self.module_name
            for key, value in child.items():
                setattr(case, key, value)
            if len(child) > 0:
                if not getattr(case, ReportConstant.result, "") or \
                        getattr(case, ReportConstant.result, "") == ReportConstant.completed:
                    setattr(case, ReportConstant.result, ReportConstant.false)
                message = child[0].get(ReportConstant.message, "")
                if child[0].text and message != child[0].text:
                    message = "%s\n%s" % (message, child[0].text)
                setattr(case, ReportConstant.message, message)
            self.cases.append(case)
        self.cases.sort(key=lambda x: (
            x.is_failed(), x.is_blocked(), x.is_unavailable(), x.is_passed()),
                        reverse=True)


class Case:
    module_name = ReportConstant.empty_name
    name = ReportConstant.empty_name
    classname = ReportConstant.empty_name
    status = ""
    result = ""
    message = ""
    time = ""
    report = ""

    def is_passed(self):
        if self.result == ReportConstant.true and \
                (self.status == ReportConstant.run or self.status == ""):
            return True
        if self.result == "" and self.status == ReportConstant.run and \
                self.message == "":
            return True
        return False

    def is_failed(self):
        return self.result == ReportConstant.false and (self.status == ReportConstant.run or self.status == "")

    def is_blocked(self):
        return self.status in [ReportConstant.blocked, ReportConstant.disable,
                               ReportConstant.error]

    def is_unavailable(self):
        return self.status in [ReportConstant.unavailable]

    def is_ignored(self):
        return self.status in [ReportConstant.skip, ReportConstant.not_run]

    def is_completed(self):
        return self.result == ReportConstant.completed

    def get_result(self):
        if self.is_failed():
            return ReportConstant.failed
        if self.is_blocked():
            return ReportConstant.blocked
        if self.is_unavailable():
            return ReportConstant.unavailable
        if self.is_ignored():
            return ReportConstant.ignored
        return ReportConstant.passed

    @staticmethod
    def get_case_result(ele_case):
        error_msg = ele_case.get(ReportConstant.message, "")
        result_kind = ele_case.get(ReportConstant.result_kind, "")
        if result_kind != "":
            return result_kind, error_msg
        result = ele_case.get(ReportConstant.result, "")
        status = ele_case.get(ReportConstant.status, "")
        # 适配HCPTest的测试结果，其用例失败时，会在testcase下新建failure节点，存放错误信息
        if len(ele_case) > 0 and ele_case[0].tag == ReportConstant.failure:
            error_msg = "\n\n".join([failure.get(ReportConstant.message, "") for failure in ele_case])
            return CaseResult.failed, error_msg
        if result == ReportConstant.false and (status == ReportConstant.run or status == ""):
            return CaseResult.failed, error_msg
        if status in [ReportConstant.blocked, ReportConstant.disable, ReportConstant.error]:
            return CaseResult.blocked, error_msg
        if status in [ReportConstant.skip, ReportConstant.not_run]:
            return CaseResult.ignored, error_msg
        if status in [ReportConstant.unavailable]:
            return CaseResult.unavailable, error_msg
        return CaseResult.passed, ""
