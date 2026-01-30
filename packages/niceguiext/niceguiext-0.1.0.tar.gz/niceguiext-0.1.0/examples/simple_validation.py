#!/usr/bin/env python3
"""
简单的 Validation 测试示例
"""

from nicegui import ui


def test_validation():
    """测试验证功能"""

    ui.label("输入验证测试").classes("text-xl font-bold mb-4")

    # 测试必填验证
    ui.label("必填字段测试:")
    ui.input(
        "姓名",
        validation=lambda value: "此字段为必填项"
        if not value or str(value).strip() == ""
        else None,
    ).classes("mb-2")

    # 测试长度验证
    ui.label("长度限制测试 (最多10个字符):")
    ui.input(
        "昵称", validation=lambda value: "最大长度为10字符" if len(str(value)) > 10 else None
    ).classes("mb-2")

    # 测试数字范围验证
    ui.label("数字范围测试 (0-100):")
    ui.number(
        "分数",
        validation=lambda value: "值必须在0-100之间"
        if value is not None and (float(value) < 0 or float(value) > 100)
        else None,
    ).classes("mb-2")

    # 测试邮箱格式验证
    ui.label("邮箱格式验证:")
    import re

    def validate_email(value):
        if not value:
            return None
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, value):
            return "请输入有效的邮箱地址"
        return None

    ui.input("邮箱", validation=validate_email).classes("mb-2")

    # 测试字典形式的验证
    ui.label("字典验证测试 (手机号):")
    phone_validation = {
        "手机号格式不正确": lambda value: not value
        or re.match(r"^1[3-9]\d{9}$", value) is not None,
    }

    def dict_validation(value):
        for error_msg, validation_func in phone_validation.items():
            if not validation_func(value):
                return error_msg
        return None

    ui.input("手机号", validation=dict_validation).classes("mb-4")


@ui.page("/")
def main_page():
    test_validation()


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="简单验证测试", port=8082, show=False)
