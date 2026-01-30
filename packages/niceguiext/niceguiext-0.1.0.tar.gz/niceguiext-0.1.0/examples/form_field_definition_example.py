#!/usr/bin/env python3
"""
NiceForm 使用 FieldDefinition 的示例
"""

from datetime import date
from pathlib import Path
from typing import Union

from nicegui import ui

from niceguiext.form import FieldDefinition, FormConfig, NiceForm


@ui.page("/")
async def main():
    """主函数"""

    # 定义表单字段
    fields = [
        FieldDefinition(
            name="name",
            field_type=str,
            title="姓名",
            description="请输入您的姓名",
            required=True,
            default="",
        ),
        FieldDefinition(
            name="age",
            field_type=int,
            title="年龄",
            description="请输入您的年龄",
            min_value=0,
            max_value=120,
            default=25,
        ),
        FieldDefinition(
            name="email",
            field_type=Union[str, type(None)],
            title="邮箱",
            description="请输入您的邮箱地址",
            required=False,
            default=None,
        ),
        FieldDefinition(
            name="gender",
            field_type=str,
            title="性别",
            description="请选择您的性别",
            input_type="select",
            selections={"男": "男", "女": "女", "其他": "其他"},
            default="男",
        ),
        FieldDefinition(
            name="salary",
            field_type=float,
            title="薪资",
            description="请输入您的期望薪资",
            min_value=0.0,
            max_value=100000.0,
            input_type="slider",
            step=1000.0,
            default=10000.0,
        ),
        FieldDefinition(
            name="skills",
            field_type=list[str],
            title="技能",
            description="请输入您的技能，用逗号分隔",
            default=[],
        ),
        FieldDefinition(
            name="is_active",
            field_type=bool,
            title="是否激活",
            description="账户是否激活",
            default=True,
        ),
        FieldDefinition(
            name="birth_date",
            field_type=date,
            title="出生日期",
            description="请选择您的出生日期",
            default=date(1990, 1, 1),
        ),
        FieldDefinition(
            name="profile_path",
            field_type=Union[Path, type(None)],
            title="头像路径",
            description="头像文件路径",
            required=False,
            default=None,
        ),
    ]

    # 表单配置
    config = FormConfig(
        title="用户信息表单",
        submit_button_text="提交",
        reset_button_text="重置",
        column_count=2,
        show_validation_errors=True,
    )

    async def handle_submit(form_data: dict):
        """处理表单提交"""
        print("表单提交数据:", form_data)
        ui.notify(f"提交成功！数据: {form_data}", color="positive")

    def handle_change(field_name: str, form_data: dict):
        """处理字段变化"""
        print(f"字段 {field_name} 变化: {form_data.get(field_name)}")

    # 创建表单
    form = NiceForm(fields=fields, config=config, on_submit=handle_submit, on_change=handle_change)

    # 显示当前表单数据
    ui.separator()
    ui.label("当前表单数据:").classes("text-lg font-bold mt-4")
    data_display = ui.json_editor({"content": {}}).classes("mt-2")

    # 定时更新数据显示
    def update_data_display():
        data_display.run_editor_method("updateContent", form.form_data)

    ui.timer(1.0, update_data_display)


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="FieldDefinition Form Example", port=8084)
