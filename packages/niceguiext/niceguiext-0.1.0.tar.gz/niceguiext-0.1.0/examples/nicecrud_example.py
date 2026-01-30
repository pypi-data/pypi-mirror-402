#!/usr/bin/env python3
"""
NiceCRUD 基础使用示例

这个示例展示了如何使用 NiceCRUD 组件来创建一个完整的 CRUD 界面。
包含了各种字段类型的定义和基本的增删改查功能。
"""

from typing import List, Dict, Any
from nicegui import ui
from niceguiext.nicecrud import NiceCRUD, FieldDefinition, NiceCRUDConfig, PageData


# 模拟数据存储（实际项目中应该使用数据库）
users_data = [
    {
        "id": 1,
        "name": "张三",
        "email": "zhangsan@example.com",
        "age": 25,
        "department": "tech",
        "active": True,
        "salary": 8000.0,
        "join_date": "2023-01-15",
        "skills": ["python", "javascript"],
    },
    {
        "id": 2,
        "name": "李四",
        "email": "lisi@example.com",
        "age": 30,
        "department": "marketing",
        "active": True,
        "salary": 7000.0,
        "join_date": "2022-06-20",
        "skills": ["design", "marketing"],
    },
    {
        "id": 3,
        "name": "王五",
        "email": "wangwu@example.com",
        "age": 28,
        "department": "hr",
        "active": False,
        "salary": 6500.0,
        "join_date": "2023-03-10",
        "skills": ["hr", "communication"],
    },
]


class UserCRUD(NiceCRUD):
    """用户管理 CRUD 示例"""

    async def query(self, query_values: dict, page: int = 1, page_size: int = 20) -> PageData:
        """查询用户数据"""
        # 模拟数据过滤
        filtered_data = users_data.copy()

        # 根据查询条件过滤
        for field_name, value in query_values.items():
            if value is None or value == "":
                continue

            if field_name == "name":
                filtered_data = [
                    item for item in filtered_data if value.lower() in item.get("name", "").lower()
                ]
            elif field_name == "department":
                filtered_data = [item for item in filtered_data if item.get("department") == value]
            elif field_name == "active":
                filtered_data = [
                    item for item in filtered_data if item.get("active") == (value == "true")
                ]

        # 分页处理
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_data = filtered_data[start_idx:end_idx]

        return PageData(data=page_data, total=len(filtered_data))

    async def create(self, item: Dict[str, Any]):
        """创建新用户"""
        # 生成新的 ID
        max_id = max([user.get("id", 0) for user in users_data], default=0)
        item["id"] = max_id + 1

        # 添加到数据存储
        users_data.append(item)
        ui.notify(f"用户 {item['name']} 创建成功", type="positive")

    async def update(self, item: Dict[str, Any]):
        """更新用户"""
        user_id = item["id"]
        for i, user in enumerate(users_data):
            if user["id"] == user_id:
                users_data[i] = item
                ui.notify(f"用户 {item['name']} 更新成功", type="positive")
                return

        raise ValueError(f"用户 ID {user_id} 不存在")

    async def delete(self, item: Dict[str, Any]):
        """删除用户"""
        user_id = item["id"]
        for i, user in enumerate(users_data):
            if user["id"] == user_id:
                deleted_user = users_data.pop(i)
                ui.notify(f"用户 {deleted_user['name']} 删除成功", type="positive")
                return

        raise ValueError(f"用户 ID {user_id} 不存在")

    async def select_options(self, field_name: str, item: Dict[str, Any]) -> Dict[str, str]:
        """提供字段选择选项"""
        if field_name == "department":
            return {"tech": "技术部", "marketing": "市场部", "hr": "人事部", "finance": "财务部"}
        elif field_name == "skills":
            return {
                "python": "Python",
                "javascript": "JavaScript",
                "design": "设计",
                "marketing": "市场营销",
                "hr": "人力资源",
                "communication": "沟通协调",
            }
        return {}


def create_user_fields() -> List[FieldDefinition]:
    """定义用户字段"""
    return [
        FieldDefinition(
            name="id",
            title="用户ID",
            type="integer",
            readonly=True,
            description="系统自动生成的用户唯一标识",
        ),
        FieldDefinition(
            name="name",
            title="姓名",
            type="text",
            required=True,
            max_length=50,
            show_in_query=True,
            description="用户的真实姓名",
        ),
        FieldDefinition(
            name="email", title="邮箱", type="text", required=True, description="用户的邮箱地址"
        ),
        FieldDefinition(
            name="age",
            title="年龄",
            type="integer",
            min_value=18,
            max_value=65,
            default=25,
            description="用户年龄",
        ),
        FieldDefinition(
            name="department",
            title="部门",
            type="text",
            input_type="select",
            required=True,
            show_in_query=True,
            description="用户所属部门",
        ),
        FieldDefinition(
            name="active",
            title="状态",
            type="tag",
            default=True,
            show_in_query=True,
            selections={"True": "激活|green", "False": "未激活|red"},
            description="用户是否激活",
        ),
        FieldDefinition(
            name="salary",
            title="薪资",
            type="number",
            min_value=0,
            max_value=50000,
            step=100,
            input_type="number",
            description="用户薪资（元）",
        ),
        FieldDefinition(
            name="join_date", title="入职日期", type="date", description="用户入职日期"
        ),
        FieldDefinition(
            name="skills",
            title="技能",
            type="text",
            input_type="multiselect",
            show_in_table=False,
            description="用户掌握的技能",
        ),
    ]


def create_user_config() -> NiceCRUDConfig:
    """创建用户 CRUD 配置"""
    return NiceCRUDConfig(
        id_field="id",
        heading="用户管理",
        add_button_text="添加用户",
        delete_button_text="删除选中用户",
        query_button_text="查询",
        reset_button_text="重置",
        new_item_dialog_heading="添加新用户",
        update_item_dialog_heading="编辑用户信息",
        page_size=10,
        table_type="table",
    )


@ui.page("/")
def main_page():
    """主页面"""
    ui.page_title("NiceCRUD 示例")

    with ui.column().classes("w-full max-w-6xl mx-auto p-4"):
        # 页面标题
        ui.label("NiceCRUD 用户管理示例").classes("text-2xl font-bold mb-4")

        # 说明文档
        with ui.expansion("使用说明", icon="info").classes("mb-4"):
            ui.markdown("""
            ### 功能特性
            
            1. **查询功能**: 可以根据姓名、部门、状态进行筛选查询
            2. **添加用户**: 点击"添加用户"按钮可以创建新用户
            3. **编辑用户**: 点击表格中的行可以编辑用户信息
            4. **删除用户**: 选中用户后点击"删除选中用户"按钮
            5. **分页显示**: 支持分页浏览大量数据
            
            ### 字段类型示例
            
            - **文本字段**: 姓名、邮箱
            - **数字字段**: 年龄、薪资
            - **选择字段**: 部门（单选）
            - **多选字段**: 技能（多选）  
            - **布尔字段**: 状态（激活/非激活）
            - **日期字段**: 入职日期
            - **只读字段**: 用户ID（系统自动生成）
            """)

        # 创建 CRUD 组件
        fields = create_user_fields()
        config = create_user_config()

        # 初始化 CRUD
        UserCRUD(
            fields=fields,
            data=users_data.copy(),  # 传入初始数据
            config=config,
        )


if __name__ in {"__main__", "__mp_main__"}:
    # 运行应用
    ui.run(title="NiceCRUD 示例", host="0.0.0.0", port=8080, show=True, reload=True)
