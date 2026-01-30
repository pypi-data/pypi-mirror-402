"""NiceTable 分页功能测试示例"""

from nicegui import ui
from niceguiext import NiceTable, FieldDefinition, ActionConfig, PageData


# 生成 50 条测试数据（全局变量）
TEST_DATA = []
statuses = ["active", "inactive", "pending"]
for i in range(1, 51):
    TEST_DATA.append(
        {
            "id": i,
            "name": f"User {i:02d}" * 100,
            "email": f'<font color="red">{i:02d}@example.com</font>',
            "status": statuses[(i - 1) % 3],
            "info": '{"recordId":"ROUTINE-692ff64f2865071c808b328d","contractNo":"CON02-TME00-20251203-0042","contractStatus":4,"contractEntryPerson":"janjian","contractOperators":["janjian"],"contractAuthStartTime":[2025,12,4],"contractAuthEndTime":[2029,7,3],"contractOtherPartys":[{"partyCode":"1045","partyName":"腾讯音乐娱乐科技（深圳）有限公司","settlementParty":"N","partyType":"OU"},{"partyCode":"5965","partyName":"滴滴出行科技有限公司","settlementParty":"Y","partyType":"VENDOR"}],"contractLawApprovers":null,"paymentList":[{"paymentNameCode":"ADVANCE","paymentName":"预付款","payConditionCode":"TME_IV+60","payCondition":"收到发票日+60天","scheduledTime":"2025-12-03","amount":2000.0,"paidAmount":null,"remark":null},{"paymentNameCode":"ARRIVAL","paymentName":"验收付款","payConditionCode":"TME_IV+60","payCondition":"收到发票日+60天","scheduledTime":"2025-12-03","amount":2000.0,"paidAmount":null,"remark":null},{"paymentNameCode":"ADVANCE","paymentName":"预付款","payConditionCode":"TME_IV+60","payCondition":"收到发票日+60天","scheduledTime":"2025-12-03","amount":3000.0,"paidAmount":null,"remark":null},{"paymentNameCode":"ARRIVAL","paymentName":"验收付款","payConditionCode":"TME_IV+60","payCondition":"收到发票日+60天","scheduledTime":"2025-12-03","amount":3000.0,"paidAmount":null,"remark":null}],"signDate":[2025,12,3]}',
        }
    )


# 创建自定义NiceTable子类
class PaginationTestTable(NiceTable):
    async def select_options(self, field_name: str, item) -> dict:
        """获取选择选项"""
        if field_name == "status":
            return {"active": "激活", "inactive": "未激活", "pending": "待审"}
        return {}

    async def query(self, query_values: dict, page: int = 1, page_size: int = 20) -> PageData:
        """实现查询和分页，从全局数据源中查询"""
        filtered_data = TEST_DATA.copy()

        # 应用查询条件
        for field_name, value in query_values.items():
            if value is None or value == "":
                continue

            # status 字段使用精确匹配
            if field_name == "status":
                filtered_data = [item for item in filtered_data if item.get(field_name) == value]
            else:
                # 其他字段使用模糊匹配
                filtered_data = [
                    item
                    for item in filtered_data
                    if str(item.get(field_name, "")).lower().find(str(value).lower()) >= 0
                ]

        # 分页处理
        total_count = len(filtered_data)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_data = filtered_data[start_idx:end_idx]

        return PageData(data=page_data, total=total_count)


@ui.page("/")
async def main():
    # 页面标题
    ui.label("NiceTable 分页功能测试").classes("text-2xl font-bold mb-4")
    ui.label("总共 50 条数据，每页 10 条 - 测试分页栏功能").classes("text-sm text-gray-500 mb-6")

    # 定义字段
    fields = [
        FieldDefinition(
            name="id",
            title="ID",
            type="integer",
            show_in_table=True,
            show_in_query=False,
            show_in_expand=False,
            show_in_detail=True,
        ),
        FieldDefinition(
            name="name",
            title="名称",
            type="text",
            show_in_table=True,
            show_in_query=True,
            show_in_expand=True,
            show_in_detail=True,
        ),
        FieldDefinition(
            name="email",
            title="邮箱",
            type="html",
            show_in_table=True,
            show_in_query=False,
            show_in_expand=False,
            show_in_detail=True,
        ),
        FieldDefinition(
            name="status",
            title="状态",
            type="tag",
            input_type="select",
            selections={"active": "激活|green", "inactive": "未激活|red", "pending": "待审|orange"},
            show_in_table=True,
            show_in_query=True,
            show_in_expand=True,
            show_in_detail=True,
        ),
        FieldDefinition(
            name="info",
            title="信息",
            type="json",
            show_in_table=False,
            show_in_expand=True,
            show_in_detail=True,
        ),
    ]

    # 自定义action处理函数
    def handle_edit(row_data):
        """编辑行数据"""
        ui.notify(f"编辑用户: {row_data.get('name')}", color="info")

    def handle_delete(row_data):
        """删除行数据"""
        ui.notify(f"删除用户: {row_data.get('name')}", color="negative")

    # 创建表格配置
    config = {
        "id_field": "id",
        "heading": "用户列表",
        "detail_button_text": "查看详情",
        "page_size": 10,
        "actions": [
            ActionConfig(
                label="编辑",
                call=handle_edit,
                color="info",
                icon="edit",
            ),
            ActionConfig(
                label="删除",
                call=handle_delete,
                color="negative",
                icon="delete",
            ),
        ],
    }

    # 创建表格实例（不传入data参数）
    PaginationTestTable(
        fields=fields,
        config=config,
    )


if __name__ in {"__main__", "__mp_main__"}:
    ui.run()
