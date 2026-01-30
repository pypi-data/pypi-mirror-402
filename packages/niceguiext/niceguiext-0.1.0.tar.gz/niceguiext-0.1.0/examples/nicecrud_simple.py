#!/usr/bin/env python3
"""
NiceCRUD 简单示例

这是一个最简单的 NiceCRUD 使用示例，展示了如何快速创建一个 CRUD 界面。
"""

from nicegui import ui
from niceguiext.nicecrud import NiceCRUD, FieldDefinition, PageData


# 简单的产品数据
products = [
    {"id": 1, "name": "笔记本电脑", "price": 5999.00, "category": "电子产品"},
    {"id": 2, "name": "鼠标", "price": 99.00, "category": "电子产品"},
    {"id": 3, "name": "键盘", "price": 299.00, "category": "电子产品"},
]


class ProductCRUD(NiceCRUD):
    """产品管理 CRUD 组件"""

    async def query(self, query_values: dict, page: int = 1, page_size: int = 20) -> PageData:
        """查询数据，支持分页"""
        # 使用全局产品数据
        filtered_data = products.copy()

        # 应用查询过滤
        for field_name, value in query_values.items():
            if value is None or value == "":
                continue

            # 普通字符串匹配查询
            filtered_data = [
                item
                for item in filtered_data
                if str(item.get(field_name, "")).lower().find(str(value).lower()) >= 0
            ]

        # 分页处理
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_data = filtered_data[start_idx:end_idx]

        return PageData(data=page_data, total=len(filtered_data))


@ui.page("/")
def main():
    ui.page_title("NiceCRUD 简单示例")

    # 定义字段
    fields = [
        FieldDefinition(name="id", title="ID", type="integer", readonly=True),
        FieldDefinition(
            name="name", title="产品名称", type="text", required=True, show_in_query=True
        ),
        FieldDefinition(name="price", title="价格", type="number", min_value=0, step=0.01),
        FieldDefinition(name="category", title="分类", type="text", show_in_query=True),
    ]

    # 创建 CRUD 组件，不传入初始数据
    ProductCRUD(
        fields=fields,
        id_field="id",
        heading="产品管理",
        add_button_text="添加产品",
        delete_button_text="删除产品",
        page_size=20,
    )


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(port=8081, show=True)
