#!/usr/bin/env python3
"""
NiceCRUD 网格模式示例

展示 NiceCRUD 的网格显示模式，适合展示卡片式的数据。
"""

from typing import List, Dict, Any
from nicegui import ui
from niceguiext.nicecrud import NiceCRUD, FieldDefinition, NiceCRUDConfig, PageData


# 产品数据
products = [
    {
        "id": 1,
        "name": "MacBook Pro",
        "brand": "Apple",
        "price": 12999.00,
        "category": "laptop",
        "rating": 4.8,
        "stock": 50,
        "featured": True,
        "description": "强大的专业级笔记本电脑",
    },
    {
        "id": 2,
        "name": "iPhone 15",
        "brand": "Apple",
        "price": 5999.00,
        "category": "phone",
        "rating": 4.7,
        "stock": 100,
        "featured": True,
        "description": "最新款智能手机",
    },
    {
        "id": 3,
        "name": "ThinkPad X1",
        "brand": "Lenovo",
        "price": 8999.00,
        "category": "laptop",
        "rating": 4.5,
        "stock": 30,
        "featured": False,
        "description": "商务办公笔记本",
    },
    {
        "id": 4,
        "name": "Galaxy S24",
        "brand": "Samsung",
        "price": 4999.00,
        "category": "phone",
        "rating": 4.6,
        "stock": 80,
        "featured": False,
        "description": "安卓旗舰手机",
    },
    {
        "id": 5,
        "name": "iPad Air",
        "brand": "Apple",
        "price": 3999.00,
        "category": "tablet",
        "rating": 4.4,
        "stock": 60,
        "featured": True,
        "description": "轻薄平板电脑",
    },
    {
        "id": 6,
        "name": "Surface Pro",
        "brand": "Microsoft",
        "price": 6999.00,
        "category": "tablet",
        "rating": 4.3,
        "stock": 40,
        "featured": False,
        "description": "二合一平板电脑",
    },
]


class ProductGridCRUD(NiceCRUD):
    """产品网格 CRUD"""

    async def select_options(self, field_name: str, item: Dict[str, Any]) -> Dict[str, str]:
        """提供选择选项"""
        if field_name == "brand":
            return {
                "Apple": "苹果",
                "Samsung": "三星",
                "Lenovo": "联想",
                "Microsoft": "微软",
                "Huawei": "华为",
                "Xiaomi": "小米",
            }
        elif field_name == "category":
            return {
                "laptop": "💻 笔记本电脑",
                "phone": "📱 智能手机",
                "tablet": "📱 平板电脑",
                "accessory": "🎧 配件",
            }
        return {}

    async def query(self, query_values: dict, page: int = 1, page_size: int = 20) -> PageData:
        """查询产品"""
        filtered_data = products.copy()

        for field_name, value in query_values.items():
            if not value:
                continue

            if field_name == "name":
                filtered_data = [
                    item for item in filtered_data if value.lower() in item.get("name", "").lower()
                ]
            elif field_name == "brand":
                filtered_data = [item for item in filtered_data if item.get("brand") == value]
            elif field_name == "category":
                filtered_data = [item for item in filtered_data if item.get("category") == value]
            elif field_name == "featured":
                filtered_data = [
                    item for item in filtered_data if item.get("featured") == (value == "true")
                ]
            elif field_name == "min_price":
                try:
                    min_price = float(value)
                    filtered_data = [
                        item for item in filtered_data if item.get("price", 0) >= min_price
                    ]
                except ValueError:
                    pass

        # 分页
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_data = filtered_data[start_idx:end_idx]

        return PageData(data=page_data, total=len(filtered_data))

    async def create(self, item: Dict[str, Any]):
        """添加产品"""
        if not item.get("name"):
            raise ValueError("产品名称不能为空")

        if item.get("price", 0) <= 0:
            raise ValueError("价格必须大于0")

        # 生成ID
        max_id = max([p.get("id", 0) for p in products], default=0)
        item["id"] = max_id + 1

        products.append(item)
        ui.notify(f"产品 {item['name']} 添加成功", type="positive")

    async def update(self, item: Dict[str, Any]):
        """更新产品"""
        product_id = item["id"]
        for i, product in enumerate(products):
            if product["id"] == product_id:
                products[i] = item
                ui.notify(f"产品 {item['name']} 更新成功", type="positive")
                return
        raise ValueError(f"产品 ID {product_id} 不存在")

    async def delete(self, item: Dict[str, Any]):
        """删除产品"""
        product_id = item["id"]
        for i, product in enumerate(products):
            if product["id"] == product_id:
                deleted_product = products.pop(i)
                ui.notify(f"产品 {deleted_product['name']} 删除成功", type="positive")
                return
        raise ValueError(f"产品 ID {product_id} 不存在")


def create_product_fields() -> List[FieldDefinition]:
    """创建产品字段"""
    return [
        FieldDefinition(
            name="id", title="产品ID", type="integer", readonly=True, show_in_table=False
        ),
        FieldDefinition(
            name="name",
            title="产品名称",
            type="text",
            required=True,
            max_length=100,
            show_in_query=True,
            description="产品的名称",
        ),
        FieldDefinition(
            name="brand",
            title="品牌",
            type="text",
            input_type="select",
            required=True,
            show_in_query=True,
            description="产品品牌",
        ),
        FieldDefinition(
            name="price",
            title="价格",
            type="number",
            min_value=0,
            step=0.01,
            required=True,
            description="产品价格（元）",
        ),
        FieldDefinition(
            name="category",
            title="分类",
            type="text",
            input_type="select",
            required=True,
            show_in_query=True,
            description="产品分类",
        ),
        FieldDefinition(
            name="rating",
            title="评分",
            type="number",
            input_type="slider",
            min_value=1.0,
            max_value=5.0,
            step=0.1,
            default=4.0,
            description="用户评分（1-5星）",
        ),
        FieldDefinition(
            name="stock",
            title="库存",
            type="integer",
            min_value=0,
            default=0,
            description="库存数量",
        ),
        FieldDefinition(
            name="featured",
            title="推荐",
            type="boolean",
            default=False,
            show_in_query=True,
            description="是否为推荐产品",
        ),
        FieldDefinition(
            name="description",
            title="描述",
            type="text",
            show_in_table=False,
            max_length=500,
            description="产品详细描述",
        ),
        # 查询专用字段
        FieldDefinition(
            name="min_price",
            title="最低价格",
            type="number",
            min_value=0,
            step=0.01,
            exclude=True,  # 不在表单中显示
            show_in_query=True,
            description="价格筛选下限",
        ),
    ]


def create_grid_config() -> NiceCRUDConfig:
    """创建网格配置"""
    return NiceCRUDConfig(
        id_field="id",
        heading="📦 产品展示中心",
        add_button_text="➕ 添加产品",
        delete_button_text="🗑️ 删除选中",
        query_button_text="🔍 筛选",
        reset_button_text="🔄 重置筛选",
        new_item_dialog_heading="添加新产品",
        update_item_dialog_heading="编辑产品信息",
        page_size=6,
        table_type="grid",  # 使用网格模式
        # 美化样式
        class_heading="text-3xl font-bold text-center text-purple-600 mb-8",
        class_subheading="text-xl font-semibold text-gray-700",
        class_card="bg-white shadow-lg rounded-xl border border-gray-200 hover:shadow-xl transition-all duration-300",
        class_card_selected="bg-purple-50 shadow-xl border-2 border-purple-400",
        class_card_header="bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-t-xl",
    )


@ui.page("/")
def grid_page():
    """网格模式展示页面"""
    ui.page_title("NiceCRUD 网格模式")

    # 添加自定义样式
    ui.add_head_html("""
    <style>
        body {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
        }
        .product-grid .q-card {
            transition: all 0.3s ease;
        }
        .product-grid .q-card:hover {
            transform: translateY(-5px);
        }
        .feature-badge {
            position: absolute;
            top: 10px;
            right: 10px;
            background: linear-gradient(45deg, #ff6b6b, #feca57);
            color: white;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
        }
    </style>
    """)

    with ui.column().classes("w-full max-w-6xl mx-auto p-6"):
        # 页面标题
        with ui.card().classes(
            "w-full p-8 mb-6 text-center bg-gradient-to-r from-purple-600 to-pink-600 text-white"
        ):
            ui.label("🛍️ 产品展示中心").classes("text-4xl font-bold mb-2")
            ui.label("使用网格模式展示产品信息").classes("text-xl opacity-90")

        # 功能介绍
        with ui.expansion("🎨 网格模式特性", icon="grid_view").classes("mb-6"):
            with ui.grid(columns=3).classes("gap-4"):
                with ui.card().classes("p-4 text-center"):
                    ui.icon("view_module", size="2em").classes("text-blue-500")
                    ui.label("网格展示").classes("font-bold mt-2")
                    ui.label("卡片式布局，直观美观")

                with ui.card().classes("p-4 text-center"):
                    ui.icon("filter_alt", size="2em").classes("text-green-500")
                    ui.label("智能筛选").classes("font-bold mt-2")
                    ui.label("多条件组合筛选")

                with ui.card().classes("p-4 text-center"):
                    ui.icon("star", size="2em").classes("text-yellow-500")
                    ui.label("评分展示").classes("font-bold mt-2")
                    ui.label("滑块式评分输入")

        # 创建网格 CRUD
        fields = create_product_fields()
        config = create_grid_config()

        ProductGridCRUD(fields=fields, data=products.copy(), config=config)

        # 使用说明
        with ui.card().classes("mt-6 p-4 bg-blue-50 border-l-4 border-blue-400"):
            ui.label("💡 使用提示").classes("font-bold text-blue-700")
            with ui.column().classes("mt-2 space-y-1"):
                ui.label("• 点击产品卡片可以编辑产品信息")
                ui.label("• 使用筛选功能快速查找产品")
                ui.label("• 推荐产品会显示特殊标识")
                ui.label("• 支持按品牌、分类、价格等多维度筛选")


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="NiceCRUD 网格模式", port=8083, show=True, reload=True)
