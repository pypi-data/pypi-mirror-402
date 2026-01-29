import re
import requests
from jsonpath import jsonpath
from . import global_func
from .caseLog import CaseLogHandler
from .dbClient import DBClient
# 定义脚本中的全局变量
ENV = {}
db = DBClient()

class BaseCase(CaseLogHandler):
    """用例执行基本父类"""

    def __run_script(self, data):
        # 执行前后置脚本，可以在前后置脚本中共享数据
        test = self
        global_var = ENV.get("envs")
        print = self.print_log
        # 定义脚本中的临时变量
        self.env = {}
        # 1、读取前置脚本数据
        setup_scripts = data.get("setup_scripts")
        # 2、执行字符串中有效的python代码
        exec(setup_scripts)

        response = yield

        # 1、读取后置脚本数据
        teardown_scripts = data.get("teardown_scripts")
        # 2、执行字符串中有效的python代码
        exec(teardown_scripts)

        yield

    def __setup_script(self, data):
        """前置脚本处理"""
        self.script_hook = self.__run_script(data)
        next(self.script_hook)

    def __teardown_script(self, data, response):
        """后置脚本处理"""
        self.script_hook.send(response)
        """删除生成器对象"""
        delattr(self, "script_hook")

    def replace_data(self, data):
        """替换测试用例中的变量数据"""
        # 1、定义替换数据的规则
        pattern = r"\${(.+?)}"
        # 2、讲测试用例数据转换为字符串格式
        data = str(data)
        # 3、替换测试用例中的数据
        while re.search(pattern, data):
            # 获取匹配的数据内容
            match_data = re.search(pattern, data)
            key = match_data.group(1)
            # 获取全局变量中的值
            value = ENV.get("envs").get(key)
            # 替换数据
            data = data.replace(match_data.group(), str(value))
        return eval(data)

    def __handle_request_data(self, data):
        """处理请求数据"""
        self.name = data.get("name")
        request_data = {}
        # 1、处理请求url
        if data.get("interface").get("url").startswith("http"):
            request_data["url"] = data.get("interface").get("url")
        else:
            request_data["url"] = ENV.get("base_url") + data.get("interface").get("url")
        request_data["method"] = data.get("interface").get("method")
        # 2、处理请求头
        request_data["headers"] = ENV.get("headers")
        request_data["headers"].update(data.get("headers"))
        # 3、处理请求参数
        request_data["params"] = data.get("request_data").get("params")
        if "application/json" in request_data["headers"].get("Content-Type"):
            request_data["json"] = data.get("request_data").get("json")
        elif "application/x-www-form-urlencoded" in request_data["headers"].get("Content-Type"):
            request_data["data"] = data.get("request_data").get("data")
        elif "multipart/form-data" in request_data["headers"].get("Content-Type"):
            request_data["files"] = data.get("request_data").get("files")
        # 4、替换请求中的变量名 为 具体的变量数据
        request_data = self.replace_data(request_data)
        self.url = request_data["url"]
        self.method = request_data["method"]
        self.request_headers = request_data["headers"]
        return request_data

    def __send_request(self, data):
        """发送请求"""
        request_data = self.__handle_request_data(data)
        self.info_log(request_data)
        response = requests.request(method=request_data.get("method"),
                                    url=request_data.get("url"),
                                    headers=request_data.get("headers"),
                                    params=request_data.get("params"),
                                    data=request_data.get("data"),
                                    json=request_data.get("json"),
                                    files=request_data.get("files"))
        #  获取用例执行的请求和响应信息
        self.request_body = response.request.body
        self.status_code = response.status_code
        self.response_headers = response.headers
        self.response_body = response.text
        self.info_log("请求地址:", self.url)
        self.info_log("请求方法:", self.method)
        self.info_log("请求头:", self.request_headers)
        self.info_log("响应头:", self.response_headers)
        self.info_log("请求体:", self.request_body)
        self.info_log("响应体:", self.response_body)
        return response

    def perform(self, data):
        """执行用例"""
        self.__setup_script(data)
        response = self.__send_request(data)
        self.__teardown_script(data, response)

    def save_env_variable(self, key, value):
        """保存测试运行环境变量"""
        self.info_log(f"保存（临时）环境变量：{key} = {value}")
        self.env[key] = value

    def del_evn_variable(self, key):
        """删除测试运行环境变量"""
        self.info_log(f"删除（临时）环境变量：{key}")
        del self.env[key]

    def save_global_variable(self, key, value):
       """保存测试运行环境的全局变量"""
       self.info_log(f"保存全局变量：{key} = {value}")
       ENV.get("envs")[key] = value

    def del_global_variable(self, key):
        """删除测试运行环境的全局变量"""
        self.info_log(f"删除全局变量：{key}")
        del ENV.get("envs")[key]

    def json_extract(self,obj,ext):
        """通过jsonpath提取一个json数据"""
        self.info_log("----通过jsonpath提取单个数据---")
        res = jsonpath(obj, ext)
        value = res[0] if res else ""
        return value

    def json_extract_list(self,obj,ext):
        """通过jsonpath提取一组json数据"""
        self.info_log("----通过jsonpath提取一组数据---")
        res = jsonpath(obj, ext)
        value = res if res else []
        return value

    def re_extract(self,obj,ext):
        """
        通过正则提取一个数据
        obj: 响应的json数据
        ext: 匹配的正则表达式
        """
        self.info_log("----通过正则提取数据---")
        # 1、判断响应是否为字符串
        if not isinstance(obj,str):
            obj = str(obj)
        # 2、提取匹配正则表达式的第一个数据
        res = re.search(ext,obj)
        value = res.group(1) if res else ""
        return value

    def re_extract_list(self,obj,ext):
        """
        通过正则提取一组数据
        obj: 响应的json数据
        ext: 匹配的正则表达式
        """
        self.info_log("----通过正则提取一组数据---")
        # 1、判断响应是否为字符串
        if not isinstance(obj,str):
            obj = str(obj)
        # 2、提取匹配正则表达式的所有数据
        res = re.findall(ext,obj)
        value = res if res else []
        return value

    def assertion(self,method,expect,actual):
        """
        :param method: 断言比较的方式
        :param expect: 断言的期望结果
        :param actual: 断言的实际结果
        :return:
        """
        # 1、断言的方法
        method_map = {
            "相等": lambda a,b: a == b,
            "相等忽略大小写": lambda a, b: a.lower() == b.lower(),
            "不相等":  lambda a,b: a != b,
            "包含": lambda a,b: a in b,
            "不包含": lambda a,b: a not in b,
            "大于": lambda a,b: a > b,
            "小于": lambda a,b: a < b,
            "大于等于": lambda a,b: a >= b,
            "小于等于": lambda a,b: a <= b,
            "正则匹配": lambda a,b: re.search(a,b)
        }
        # 2、断言操作
        assert_fun = method_map.get(method)
        if assert_fun is None:
            raise Exception("不支持的断言方法")
        else:
            self.debug_log(f"断言比较方法是：{method}")
            self.debug_log(f"预期结果是：{expect}")
            self.debug_log(f"实际结果是：{actual}")
        try:
            assert assert_fun(expect,actual)
        except AssertionError:
            self.error_log(f"断言失败，实际结果({actual}) 不满足({method}) 期望结果({expect})")
            raise AssertionError(f"断言失败，实际结果({actual}) 不满足({method}) 期望结果({expect})")
        else:
            self.info_log(f"断言成功，实际结果({actual}) 满足({method}) 期望结果({expect})")