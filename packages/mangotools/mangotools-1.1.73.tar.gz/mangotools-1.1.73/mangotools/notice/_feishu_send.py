# -*- coding: utf-8 -*-
# @Project: 芒果测试平台
# @Description: 飞书通知封装
# @Time   : 2025-12-10 18:30
# @Author : Qwen
import json
from json import JSONDecodeError

import requests

from ..exceptions import MangoToolsError
from ..exceptions.error_msg import ERROR_MSG_0018
from ..models import FeiShuNoticeModel, TestReportModel


class FeiShuSend:
    def __init__(self,
                 notice_config: FeiShuNoticeModel,
                 test_report: TestReportModel | None = None,
                 domain_name: str = None,
                 content: str = None):
        self.notice_config = notice_config
        self.test_report = test_report
        self.domain_name = domain_name
        self.content = content
        self.headers = {"Content-Type": "application/json"}

    def send_feishu_notification(self):
        if self.content is None:
            # 收集所有有值的行
            lines = [
                "**【芒果测试平台测试报告通知】**",
                f"项目产品：<font color='green'>{self.test_report.project_name}/{self.test_report.product_name}</font>",
                f"测试环境：{self.test_report.test_environment}"
            ]

            # 测试套ID行
            if self.test_report.test_suite_id:
                lines.append(f"测试套ID：{self.test_report.test_suite_id}")
            if self.test_report.task_name:
                lines.append(f"任务名称：{self.test_report.task_name}")

            lines.extend([
                "",
                "--------------------",
                "**执行结果**",
                f"<font color='green'>成功率  : {self.test_report.success_rate}%</font>",
                f"执行用例数：<font color='blue'>{self.test_report.case_sum}</font>",
                f"成功用例数：<font color='green'>{self.test_report.success}</font>",
                f"失败用例数：<font color='red'>{self.test_report.fail}个</font>"
            ])

            # 接口相关统计
            if self.test_report.api_case_sum is not None and self.test_report.api_case_sum > 0:
                lines.append(f"接口用例数：{self.test_report.api_case_sum}")
                if self.test_report.api_fail is not None:
                    lines.append(f"接口失败数：{self.test_report.api_fail}")

            # 前端相关统计
            if self.test_report.ui_case_sum is not None and self.test_report.ui_case_sum > 0:
                lines.append(f"前端用例数：{self.test_report.ui_case_sum}")
                if self.test_report.ui_fail is not None:
                    lines.append(f"前端失败数：{self.test_report.ui_fail}")

            # 单元测试相关统计
            if self.test_report.pytest_case_sum is not None and self.test_report.pytest_case_sum > 0:
                lines.append(f"单元用例数：{self.test_report.pytest_case_sum}")
                if self.test_report.pytest_fail is not None:
                    lines.append(f"单元用例失败数：{self.test_report.pytest_fail}")

            # 执行信息
            lines.extend([
                f"用例执行耗时：<font color='orange'>{self.test_report.execution_duration}</font>",
                f"测试开始时间：<font color='gray'>{self.test_report.test_time}</font>",
                "",
                "非相关负责人员可忽略此消息。"
            ])

            # 平台地址
            if self.domain_name:
                lines.append(f"[测试报告入口]({self.domain_name})")

            # 将所有行连接成最终的内容
            content = "\n".join(lines)
        else:
            content = self.content
        self.send_markdown(content)

    def send_markdown(self, content):
        res = requests.post(
            url=self.notice_config.webhook,
            json={
                "msg_type": "post",
                "content": {
                    "post": {
                        "zh_cn": {
                            "title": "芒果测试平台测试报告",
                            "content": [[
                                {
                                    "tag": "text",
                                    "text": content
                                }
                            ]]
                        }
                    }
                }
            },
            headers=self.headers,
            proxies={'http': None, 'https': None}
        )
        try:
            result = res.json()
            if result.get("code") != 0 and result.get("StatusCode") != 0:
                raise MangoToolsError(*ERROR_MSG_0018)
        except JSONDecodeError:
            raise MangoToolsError(*ERROR_MSG_0018)

    def send_text(self, content):
        """
        发送纯文本消息
        
        参数:
            content (str): 文本内容
        """
        res = requests.post(
            url=self.notice_config.webhook,
            json={
                "msg_type": "text",
                "content": {
                    "text": content
                }
            },
            headers=self.headers,
            proxies={'http': None, 'https': None}
        )
        try:
            result = res.json()
            if result.get("code") != 0 and result.get("StatusCode") != 0:
                raise MangoToolsError(*ERROR_MSG_0018)
        except JSONDecodeError:
            raise MangoToolsError(*ERROR_MSG_0018)

    def send_post(self, title, content_list):
        """
        发送富文本消息
        
        参数:
            title (str): 标题
            content_list (list): 内容列表，每个元素是一个包含tag的字典
        """
        res = requests.post(
            url=self.notice_config.webhook,
            json={
                "msg_type": "post",
                "content": {
                    "post": {
                        "zh_cn": {
                            "title": title,
                            "content": [content_list]
                        }
                    }
                }
            },
            headers=self.headers,
            proxies={'http': None, 'https': None}
        )
        try:
            result = res.json()
            if result.get("code") != 0 and result.get("StatusCode") != 0:
                raise MangoToolsError(*ERROR_MSG_0018)
        except JSONDecodeError:
            raise MangoToolsError(*ERROR_MSG_0018)