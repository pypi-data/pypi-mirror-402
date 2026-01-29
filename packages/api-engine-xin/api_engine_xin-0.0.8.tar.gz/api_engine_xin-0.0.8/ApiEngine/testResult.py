from ApiEngine import log
from ApiEngine.BaseCase import BaseCase


class TestResult:
    """测试结果类"""
    def __init__(self, all, name="调试运行"):
        """
        :param all: 测试套件中的用例个数
        :param name: 测试套件的名称
        """
        self.all = all
        self.name = name
        self.success = 0
        self.fail = 0
        self.error = 0
        self.results = []

    def add_success(self, test: BaseCase):
        """
        :param test: 用例对象
        :return:
        """
        self.success += 1
        info = {
            "name": getattr(test, "name",""),
            "url": getattr(test, "url",""),
            "method": getattr(test, "method",""),
            "request_headers": getattr(test, "request_headers",""),
            "request_body": getattr(test, "request_body",""),
            "response_code": getattr(test, "response_code",""),
            "response_headers": getattr(test, "response_headers",""),
            "response_body": getattr(test, "response_body",""),
            "status": "success",
            "log_data": getattr(test, "log_data", ""),
            "run_time": getattr(test,"elapsed_ms","")
        }
        self.results.append(info)

    def add_fail(self, test: BaseCase):
        """
        :param test: 用例对象
        :return:
        """
        self.fail += 1
        info = {
            "name": getattr(test, "name",""),
            "url": getattr(test, "url",""),
            "method": getattr(test, "method",""),
            "request_headers": getattr(test, "request_headers",""),
            "request_body": getattr(test, "request_body",""),
            "response_code": getattr(test, "response_code",""),
            "response_headers": getattr(test, "response_headers",""),
            "response_body": getattr(test, "response_body",""),
            "status": "fail",
            "log_data": getattr(test, "log_data", ""),
            "run_time": getattr(test,"elapsed_ms","")
        }
        self.results.append(info)

    def add_error(self, test: BaseCase, error):
        """
        :param test: 用例对象
        :return:
        """
        self.error += 1
        log.error_log("用例执行错误，错误信息信息：", error)
        info = {
            "name": getattr(test, "name",""),
            "url": getattr(test, "url",""),
            "method": getattr(test, "method",""),
            "request_headers": getattr(test, "request_headers",""),
            "request_body": getattr(test, "request_body",""),
            "response_code": getattr(test, "response_code",""),
            "response_headers": getattr(test, "response_headers",""),
            "response_body": getattr(test, "response_body",""),
            "status": "error",
            "log_data": getattr(test, "log_data", ""),
            "run_time": getattr(test,"elapsed_ms","")
        }
        self.results.append(info)

    def get_result_info(self):
        """
        :return: 测试结果信息
        """
        if self.success == self.all:
            state = "success"
        elif self.fail > 0:
            state = "fail"
        else:
            state = "error"
        info = {
            "name": self.name,
            "all": self.all,
            "success": self.success,
            "fail": self.fail,
            "error": self.error,
            "results": self.results,
            "state": state
        }
        return info