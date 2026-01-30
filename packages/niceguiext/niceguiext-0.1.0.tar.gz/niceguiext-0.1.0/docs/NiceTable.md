# NiceTable 组件文档

NiceTable 是一个功能丰富的表格组件，支持查询条件配置、可扩展的操作按钮、查看详情功能、分页以及多种字段类型的查询。

## 功能特性

- 支持查询条件配置（文本、选择框、日期范围等）
- 支持可扩展的 action 按钮
- 支持查看详情功能
- 支持分页
- 支持多种字段类型（text、integer、number、date、datetime、json、html、tag 等）
- 支持行展开显示详细信息

## 安装

```bash
pip install niceguiext
```

## 基本用法

```python
from nicegui import ui
from niceguiext import NiceTable, FieldDefinition, PageData

# 定义字段
fields = [
    FieldDefinition(
        name="id",
        title="ID",
        type="integer",
        show_in_table=True,
        show_in_detail=True,
    ),
    FieldDefinition(
        name="name",
        title="名称",
        type="text",
        show_in_table=True,
        show_in_query=True,
        show_in_detail=True,
    ),
    FieldDefinition(
        name="status",
        title="状态",
        type="tag",
        input_type="select",
        selections={"active": "激活|green", "inactive": "未激活|red"},
        show_in_table=True,
        show_in_query=True,
    ),
]

# 创建自定义表格类
class MyTable(NiceTable):
    async def query(self, query_values: dict, page: int = 1, page_size: int = 20) -> PageData:
        # 实现数据查询逻辑
        data = [...]  # 从数据库或其他数据源获取数据
        return PageData(data=data, total=len(data))

# 创建表格
table = MyTable(
    fields=fields,
    id_field="id",
    heading="数据列表",
    page_size=10,
)

ui.run()
```

## FieldDefinition 字段定义

`FieldDefinition` 是用于定义表格字段的配置类。

### 基本属性

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `name` | str | 必填 | 字段名称 |
| `title` | str | 必填 | 字段显示标题 |
| `type` | str | "text" | 字段类型 |
| `description` | str | None | 字段描述（显示为 tooltip） |
| `default` | Any | None | 默认值 |
| `required` | bool | True | 是否必填 |

### 数字类型属性

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `min_value` | float | None | 最小值 |
| `max_value` | float | None | 最大值 |
| `step` | float | None | 步长 |

### 选择类型属性

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `input_type` | str | None | 输入类型：`"select"`, `"multiselect"`, `"slider"`, `"number"` |
| `selections` | dict | None | 选择选项，格式：`{"value": "label"}` |
| `show_selection_label` | bool | None | 是否显示选择标签 |

### 显示控制属性

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `readonly` | bool | False | 是否只读 |
| `exclude` | bool | False | 是否排除显示 |
| `show_in_table` | bool | False | 是否在表格中显示 |
| `show_in_query` | bool | False | 是否作为查询条件 |
| `show_in_expand` | bool | False | 是否在展开行中显示 |
| `show_in_detail` | bool | False | 是否在详情对话框中显示 |

### 其他属性

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `max_length` | int | None | 最大长度（文本类型） |
| `datetime_format` | str | "%Y-%m-%d %H:%M:%S" | datetime 格式化字符串 |
| `validation` | Callable/dict | None | 验证规则 |
| `validation_error` | str | None | 验证错误消息 |

### 支持的字段类型

| 类型 | 说明 |
|------|------|
| `text` | 文本类型 |
| `integer` | 整数类型 |
| `number` | 数字类型（浮点数） |
| `boolean` | 布尔类型 |
| `date` | 日期类型 |
| `datetime` | 日期时间类型 |
| `json` | JSON 类型（格式化显示） |
| `html` | HTML 类型（直接渲染） |
| `tag` | 标签类型（带颜色的标签） |

## NiceTableConfig 配置类

`NiceTableConfig` 用于配置表格的行为和外观。

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `id_field` | str | "" | ID 字段名 |
| `id_label` | str | None | ID 字段标签 |
| `no_data_label` | str | "No data" | 无数据时显示的文本 |
| `heading` | str | "列表" | 表格标题 |
| `query_button_text` | str | "查询" | 查询按钮文本 |
| `reset_button_text` | str | "重置" | 重置按钮文本 |
| `detail_button_text` | str | "详情" | 详情按钮文本 |
| `detail_dialog_heading` | str | None | 详情对话框标题 |
| `show_detail_action` | bool | True | 是否显示查看详情按钮 |
| `page_size` | int | 20 | 每页显示条数 |
| `actions` | List[ActionConfig] | [] | 表格行操作按钮 |
| `class_heading` | str | "text-xl font-bold" | 标题样式类 |
| `class_card` | str | "dark:bg-slate-900 bg-slate-200" | 卡片样式类 |
| `class_card_header` | str | "dark:bg-slate-700 bg-slate-50" | 卡片头部样式类 |

## ActionConfig 操作按钮配置

`ActionConfig` 用于配置表格行的自定义操作按钮。

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `label` | str | 必填 | 按钮显示文本 |
| `call` | str/Callable | 必填 | 调用的函数名或函数对象 |
| `color` | str | "primary" | 按钮颜色 |
| `icon` | str | None | 按钮图标 |
| `tooltip` | str | None | 按钮提示文本 |

## PageData 分页数据类

`PageData` 用于封装分页查询的返回结果。

| 属性 | 类型 | 说明 |
|------|------|------|
| `data` | List[Dict] | 当前页的数据 |
| `total` | int | 总数据条数 |

## 完整示例

```python
from nicegui import ui
from niceguiext import NiceTable, FieldDefinition, ActionConfig, PageData

# 测试数据
TEST_DATA = [
    {"id": i, "name": f"User {i}", "email": f"user{i}@example.com", "status": "active"}
    for i in range(1, 51)
]

class UserTable(NiceTable):
    async def select_options(self, field_name: str, item) -> dict:
        """获取选择选项"""
        if field_name == "status":
            return {"active": "激活", "inactive": "未激活", "pending": "待审"}
        return {}
    
    async def query(self, query_values: dict, page: int = 1, page_size: int = 20) -> PageData:
        """实现查询和分页"""
        filtered_data = TEST_DATA.copy()
        
        # 应用查询条件
        for field_name, value in query_values.items():
            if value is None or value == "":
                continue
            if field_name == "status":
                filtered_data = [item for item in filtered_data if item.get(field_name) == value]
            else:
                filtered_data = [
                    item for item in filtered_data
                    if str(item.get(field_name, "")).lower().find(str(value).lower()) >= 0
                ]
        
        # 分页处理
        total_count = len(filtered_data)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_data = filtered_data[start_idx:end_idx]
        
        return PageData(data=page_data, total=total_count)

@ui.page('/')
async def main():
    # 定义字段
    fields = [
        FieldDefinition(
            name="id",
            title="ID",
            type="integer",
            show_in_table=True,
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
            show_in_detail=True,
        ),
    ]

    # 自定义操作处理函数
    def handle_edit(row_data):
        ui.notify(f"编辑: {row_data.get('name')}", color="info")

    def handle_delete(row_data):
        ui.notify(f"删除: {row_data.get('name')}", color="negative")

    # 创建表格
    table = UserTable(
        fields=fields,
        id_field="id",
        heading="用户列表",
        page_size=10,
        actions=[
            ActionConfig(label="编辑", call=handle_edit, color="info", icon="edit"),
            ActionConfig(label="删除", call=handle_delete, color="negative", icon="delete"),
        ],
    )

if __name__ in {"__main__", "__mp_main__"}:
    ui.run()
```

## Tag 类型使用

Tag 类型用于显示带颜色的状态标签。在 `selections` 中使用 `"value": "label|color"` 格式：

```python
FieldDefinition(
    name="status",
    title="状态",
    type="tag",
    input_type="select",
    selections={
        "active": "激活|green",
        "inactive": "未激活|red",
        "pending": "待审|orange",
        "approved": "已通过|blue",
    },
    show_in_table=True,
)
```

支持的颜色：`red`, `green`, `blue`, `orange`, `yellow`, `purple`, `pink`, `cyan`, `gray`

## 需要重写的方法

### query 方法

子类必须重写 `query` 方法来实现数据查询逻辑：

```python
async def query(self, query_values: dict, page: int = 1, page_size: int = 20) -> PageData:
    """
    查询数据
    
    Args:
        query_values: 查询条件字典
        page: 当前页码（从1开始）
        page_size: 每页条数
    
    Returns:
        PageData: 包含当前页数据和总条数
    """
    # 实现查询逻辑
    return PageData(data=[], total=0)
```

### select_options 方法（可选）

如果有选择类型的字段，可以重写此方法动态获取选项：

```python
async def select_options(self, field_name: str, item: Dict[str, Any]) -> Dict[str, str]:
    """
    获取字段的选择选项
    
    Args:
        field_name: 字段名
        item: 当前行数据
    
    Returns:
        选项字典 {"value": "label"}
    """
    if field_name == "category":
        return {"cat1": "分类1", "cat2": "分类2"}
    return {}
```

### detail 方法（可选）

如果需要自定义详情数据获取逻辑，可以重写此方法：

```python
async def detail(self, item_id: str):
    """
    获取项目详情
    
    Args:
        item_id: 项目ID
    
    Returns:
        项目数据字典
    """
    # 从数据库获取详情
    return {"id": item_id, "name": "..."}
```
