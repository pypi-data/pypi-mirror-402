#!/usr/bin/env python3
"""
NiceCRUD Validation 功能示例

演示如何在 NiceCRUD 中使用各种验证规则：
1. 必填验证
2. 长度验证
3. 数字范围验证
4. 自定义验证函数
5. 字典形式的验证规则
"""

from nicegui import ui
from niceguiext import NiceCRUD, FieldDefinition
import re


def validate_email(value):
    """邮箱格式验证"""
    if not value:
        return None
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_pattern, value):
        return "请输入有效的邮箱地址"
    return None


def validate_phone(value):
    """手机号验证"""
    if not value:
        return None
    phone_pattern = r"^1[3-9]\d{9}$"
    if not re.match(phone_pattern, value):
        return "请输入有效的手机号码"
    return None


# 定义字段，包含各种验证规则
fields = [
    FieldDefinition(
        name="id",
        title="ID",
        type="integer",
        required=True,
        readonly=True,
        show_in_table=True,
    ),
    FieldDefinition(
        name="name",
        title="姓名",
        type="text",
        required=True,  # 必填验证
        max_length=20,  # 最大长度验证
        description="请输入姓名，最多20个字符",
        show_in_table=True,
    ),
    FieldDefinition(
        name="email",
        title="邮箱",
        type="text",
        required=True,
        validation=validate_email,  # 自定义验证函数
        description="请输入有效的邮箱地址",
        show_in_table=True,
    ),
    FieldDefinition(
        name="phone",
        title="手机号",
        type="text",
        required=False,
        validation={  # 字典形式的验证规则
            "手机号格式不正确": lambda value: not value
            or re.match(r"^1[3-9]\d{9}$", value) is not None,
        },
        description="请输入11位手机号码",
        show_in_table=True,
    ),
    FieldDefinition(
        name="age",
        title="年龄",
        type="integer",
        required=True,
        min_value=0,  # 最小值验证
        max_value=150,  # 最大值验证
        description="请输入年龄（0-150）",
        show_in_table=True,
    ),
    FieldDefinition(
        name="salary",
        title="薪资",
        type="number",
        required=False,
        min_value=0,
        max_value=1000000,
        step=100,
        description="请输入薪资（0-1000000）",
        show_in_table=True,
    ),
    FieldDefinition(
        name="bio",
        title="个人简介",
        type="text",
        required=False,
        max_length=500,  # 长度限制
        description="请输入个人简介，最多500个字符",
        show_in_table=False,
    ),
    FieldDefinition(
        name="department",
        title="部门",
        type="text",
        input_type="select",
        selections={
            "tech": "技术部",
            "sales": "销售部",
            "hr": "人事部",
            "finance": "财务部",
        },
        required=True,
        description="请选择部门",
        show_in_table=True,
    ),
    FieldDefinition(
        name="skills",
        title="技能",
        type="text",
        input_type="multiselect",
        selections={
            "python": "Python",
            "javascript": "JavaScript",
            "java": "Java",
            "cpp": "C++",
            "go": "Go",
            "rust": "Rust",
        },
        required=False,
        description="请选择技能",
        show_in_table=True,
    ),
    FieldDefinition(
        name="join_date",
        title="入职日期",
        type="date",
        required=True,
        description="请选择入职日期",
        show_in_table=True,
    ),
]

# 示例数据
sample_data = [
    {
        "id": 1,
        "name": "张三",
        "email": "zhangsan@example.com",
        "phone": "13812345678",
        "age": 28,
        "salary": 15000.0,
        "bio": "资深Python开发工程师，有5年开发经验。",
        "department": "tech",
        "skills": ["python", "javascript"],
        "join_date": "2023-01-15",
    },
    {
        "id": 2,
        "name": "李四",
        "email": "lisi@example.com",
        "phone": "13987654321",
        "age": 25,
        "salary": 12000.0,
        "bio": "前端开发工程师，专注于React和Vue。",
        "department": "tech",
        "skills": ["javascript", "java"],
        "join_date": "2023-03-20",
    },
    {
        "id": 3,
        "name": "王五",
        "email": "wangwu@example.com",
        "phone": "13555666777",
        "age": 32,
        "salary": 20000.0,
        "bio": "销售总监，负责华东区域销售业务。",
        "department": "sales",
        "skills": [],
        "join_date": "2022-08-10",
    },
]


class EmployeeCRUD(NiceCRUD):
    """员工管理 CRUD"""

    def __init__(self):
        super().__init__(
            fields=fields,
            data=sample_data,
            id_field="id",
            heading="员工管理",
        )


@ui.page("/")
def main_page():
    ui.label("NiceCRUD Validation 功能示例").classes("text-2xl font-bold mb-4")

    with ui.card().classes("w-full"):
        ui.markdown("""
        ### 验证功能说明
        
        该示例演示了 NiceCRUD 中的各种验证功能：
        
        1. **必填验证**: 姓名、邮箱、年龄、部门、入职日期为必填字段
        2. **长度验证**: 姓名最多20个字符，个人简介最多500个字符
        3. **数字范围验证**: 年龄范围0-150，薪资范围0-1000000
        4. **邮箱格式验证**: 使用自定义验证函数检查邮箱格式
        5. **手机号验证**: 使用字典形式的验证规则检查手机号格式
        
        ### 使用方法
        
        - 点击"添加新项目"按钮添加新员工
        - 尝试输入不符合验证规则的数据，查看验证错误提示
        - 验证错误会显示在输入框下方，阻止表单提交
        """)

    # 创建 CRUD 组件
    EmployeeCRUD()


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="NiceCRUD Validation 示例", port=8080, show=False)
