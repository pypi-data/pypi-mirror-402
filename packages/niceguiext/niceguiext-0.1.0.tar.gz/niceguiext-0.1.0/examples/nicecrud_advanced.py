#!/usr/bin/env python3
"""
NiceCRUD 高级功能示例

展示 NiceCRUD 的高级功能，包括：
- 自定义验证
- 动态选项加载
- 复杂字段类型
- 网格显示模式
- 自定义样式
"""

import asyncio
from typing import List, Dict, Any
from nicegui import ui
from niceguiext.nicecrud import NiceCRUD, FieldDefinition, NiceCRUDConfig, PageData, ActionConfig


# 模拟异步数据源
class DataService:
    """模拟数据服务"""

    @staticmethod
    async def get_countries():
        """获取国家列表"""
        await asyncio.sleep(0.1)  # 模拟网络延迟
        return {"cn": "中国", "us": "美国", "jp": "日本", "kr": "韩国", "uk": "英国"}

    @staticmethod
    async def get_cities(country: str):
        """根据国家获取城市列表"""
        await asyncio.sleep(0.1)
        cities = {
            "cn": {"bj": "北京", "sh": "上海", "gz": "广州", "sz": "深圳"},
            "us": {"ny": "纽约", "la": "洛杉矶", "sf": "旧金山"},
            "jp": {"tokyo": "东京", "osaka": "大阪"},
            "kr": {"seoul": "首尔", "busan": "釜山"},
            "uk": {"london": "伦敦", "manchester": "曼彻斯特"},
        }
        return cities.get(country, {})


# 员工数据
employees = [
    {
        "id": 1,
        "name": "张三",
        "position": "senior",
        "country": "cn",
        "city": "bj",
        "experience": 5,
        "rating": 4.5,
        "remote": True,
        "tags": ["python", "ai"],
        "notes": "优秀的AI工程师",
    },
    {
        "id": 2,
        "name": "John Smith",
        "position": "junior",
        "country": "us",
        "city": "ny",
        "experience": 2,
        "rating": 3.8,
        "remote": False,
        "tags": ["javascript", "react"],
        "notes": "前端开发新人",
    },
]


class AdvancedEmployeeCRUD(NiceCRUD):
    """高级员工管理 CRUD"""

    async def select_options(self, field_name: str, item: Dict[str, Any]) -> Dict[str, str]:
        """动态加载选项"""
        if field_name == "country":
            return await DataService.get_countries()

        elif field_name == "city":
            # 根据选择的国家动态加载城市
            country = item.get("country", "cn")
            return await DataService.get_cities(country)

        elif field_name == "position":
            return {
                "intern": "实习生",
                "junior": "初级工程师",
                "senior": "高级工程师",
                "lead": "技术主管",
                "manager": "经理",
            }

        elif field_name == "tags":
            return {
                "python": "Python",
                "javascript": "JavaScript",
                "ai": "人工智能",
                "react": "React",
                "vue": "Vue.js",
                "backend": "后端开发",
                "frontend": "前端开发",
                "devops": "运维",
            }

        return {}

    async def query(self, query_values: dict, page: int = 1, page_size: int = 20) -> PageData:
        """查询员工数据"""
        filtered_data = employees.copy()

        for field_name, value in query_values.items():
            if not value:
                continue

            if field_name == "name":
                filtered_data = [
                    item for item in filtered_data if value.lower() in item.get("name", "").lower()
                ]
            elif field_name == "position":
                filtered_data = [item for item in filtered_data if item.get("position") == value]
            elif field_name == "country":
                filtered_data = [item for item in filtered_data if item.get("country") == value]
            elif field_name == "experience":
                try:
                    min_exp = int(value)
                    filtered_data = [
                        item for item in filtered_data if item.get("experience", 0) >= min_exp
                    ]
                except ValueError:
                    pass

        # 分页
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_data = filtered_data[start_idx:end_idx]

        return PageData(data=page_data, total=len(filtered_data))

    async def create(self, item: Dict[str, Any]):
        """创建员工"""
        # 验证逻辑
        if not item.get("name"):
            raise ValueError("姓名不能为空")

        if item.get("experience", 0) < 0:
            raise ValueError("工作经验不能为负数")

        # 生成ID
        max_id = max([emp.get("id", 0) for emp in employees], default=0)
        item["id"] = max_id + 1

        employees.append(item)

    async def update(self, item: Dict[str, Any]):
        """更新员工"""
        emp_id = item["id"]
        for i, emp in enumerate(employees):
            if emp["id"] == emp_id:
                employees[i] = item
                return
        raise ValueError(f"员工 ID {emp_id} 不存在")

    async def delete(self, item_id: str):
        """删除员工"""
        emp_id = int(item_id)
        for i, emp in enumerate(employees):
            if emp["id"] == emp_id:
                employees.pop(i)
                return
        raise ValueError(f"员工 ID {emp_id} 不存在")

    def view_details(self, row_data):
        """查看员工详情"""
        emp_id = row_data.get("obj_id")
        emp_name = row_data.get("name", "未知")
        ui.notify(f"查看员工详情: {emp_name} (ID: {emp_id})", color="info")
        # 这里可以打开详情对话框或跳转到详情页面

    def send_email(self, row_data):
        """发送邮件给员工"""
        emp_name = row_data.get("name", "未知")
        ui.notify(f"正在发送邮件给 {emp_name}...", color="positive")
        # 这里可以实现实际的邮件发送逻辑

    def toggle_status(self, row_data):
        """切换员工状态"""
        row_data.get("obj_id")
        emp_name = row_data.get("name", "未知")
        ui.notify(f"切换员工 {emp_name} 的状态", color="warning")
        # 这里可以实现状态切换逻辑


def create_advanced_fields() -> List[FieldDefinition]:
    """创建高级字段定义"""
    return [
        FieldDefinition(name="id", title="员工ID", type="integer", readonly=True),
        FieldDefinition(
            name="name",
            title="姓名",
            type="text",
            required=True,
            max_length=50,
            show_in_query=True,
            description="员工姓名",
        ),
        FieldDefinition(
            name="position",
            title="职位",
            type="text",
            input_type="select",
            required=True,
            show_in_query=True,
            description="员工职位级别",
        ),
        FieldDefinition(
            name="country",
            title="国家",
            type="text",
            input_type="select",
            required=True,
            show_in_query=True,
            description="工作国家",
        ),
        FieldDefinition(
            name="city",
            title="城市",
            type="text",
            input_type="select",
            required=True,
            description="工作城市（根据国家动态加载）",
        ),
        FieldDefinition(
            name="experience",
            title="工作经验",
            type="integer",
            min_value=0,
            max_value=50,
            default=0,
            show_in_query=True,
            description="工作年限",
        ),
        FieldDefinition(
            name="rating",
            title="评分",
            type="number",
            input_type="slider",
            min_value=1.0,
            max_value=5.0,
            step=0.1,
            default=3.0,
            description="绩效评分（1-5分）",
        ),
        FieldDefinition(
            name="remote", title="远程工作", type="boolean", description="是否支持远程工作"
        ),
        FieldDefinition(
            name="tags",
            title="技能标签",
            type="text",
            input_type="multiselect",
            description="员工技能标签",
        ),
        FieldDefinition(
            name="date",
            title="入职日期",
            type="date",
            description="入职日期",
        ),
        FieldDefinition(name="notes", title="备注", type="text", description="其他备注信息"),
    ]


def create_advanced_config() -> NiceCRUDConfig:
    """创建高级配置"""
    return NiceCRUDConfig(
        id_field="id",
        heading="高级员工管理系统",
        add_button_text="添加员工",
        delete_button_text="删除选中",
        query_button_text="搜索",
        reset_button_text="重置",
        new_item_dialog_heading="添加新员工",
        update_item_dialog_heading="编辑员工信息",
        page_size=5,
        table_type="table",
        # 自定义操作按钮
        actions=[
            ActionConfig(label="详情", call="view_details", color="info", tooltip="查看员工详情"),
            ActionConfig(
                label="邮件",
                call=lambda e: ui.notify(f"查看员工详情: {e}"),
                color="positive",
                tooltip="发送邮件",
            ),
        ],
        # 自定义样式
        class_heading="text-3xl font-bold text-blue-600 mb-6",
        class_subheading="text-xl font-semibold text-gray-700",
        class_card="bg-gradient-to-r from-blue-50 to-indigo-50 shadow-lg rounded-lg",
        class_card_selected="bg-gradient-to-r from-blue-100 to-indigo-100 shadow-xl",
        class_card_header="bg-gradient-to-r from-blue-600 to-indigo-600 text-white",
    )


@ui.page("/")
def advanced_page():
    """高级功能展示页面"""
    ui.page_title("NiceCRUD 高级功能示例")

    # 添加自定义CSS
    ui.add_head_html("""
    <style>
        .gradient-bg {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .card-hover:hover {
            transform: translateY(-2px);
            transition: all 0.3s ease;
        }
    </style>
    """)

    with ui.column().classes("w-full max-w-7xl mx-auto p-6"):
        # 页面头部
        with ui.row().classes("w-full gradient-bg rounded-lg p-6 mb-6 text-white"):
            with ui.column():
                ui.label("🚀 NiceCRUD 高级功能演示").classes("text-3xl font-bold")
                ui.label("展示动态选项、自定义验证、复杂字段类型等高级特性").classes(
                    "text-lg opacity-90"
                )

        # 功能说明
        with ui.expansion("🎯 高级功能说明", icon="info").classes("mb-6 card-hover"):
            with ui.grid(columns=2).classes("gap-4"):
                with ui.card().classes("p-4"):
                    ui.label("🔄 动态选项加载").classes("font-bold text-blue-600")
                    ui.label("城市选项根据选择的国家动态更新")

                with ui.card().classes("p-4"):
                    ui.label("🎚️ 滑块控件").classes("font-bold text-green-600")
                    ui.label("评分字段使用滑块进行输入")

                with ui.card().classes("p-4"):
                    ui.label("🏷️ 多选标签").classes("font-bold text-purple-600")
                    ui.label("技能标签支持多选功能")

                with ui.card().classes("p-4"):
                    ui.label("✅ 数据验证").classes("font-bold text-red-600")
                    ui.label("自定义验证逻辑和错误提示")

        # 创建高级 CRUD
        fields = create_advanced_fields()
        config = create_advanced_config()

        AdvancedEmployeeCRUD(fields=fields, data=employees.copy(), config=config, table_type="grid")


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="NiceCRUD 高级功能示例", port=8080, show=True, reload=True)
