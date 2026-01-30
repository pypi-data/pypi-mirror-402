# NiceCRUD 组件文档

NiceCRUD 是基于 NiceTable 的 CRUD（增删改查）组件，继承了 NiceTable 的表格展示和查询能力，并添加了创建、编辑、删除功能。

## 功能特性

- 继承 NiceTable 的所有功能（查询、分页、详情查看等）
- 支持新增数据
- 支持编辑数据
- 支持单条删除和批量删除
- 支持表格模式和卡片网格模式
- 自动生成编辑表单

## 安装

```bash
pip install niceguiext
```

## 基本用法

```python
from nicegui import ui
from niceguiext import NiceCRUD, FieldDefinition, PageData

# 数据存储
products = [
    {"id": 1, "name": "笔记本电脑", "price": 5999.00, "category": "电子产品"},
    {"id": 2, "name": "鼠标", "price": 99.00, "category": "电子产品"},
]

class ProductCRUD(NiceCRUD):
    async def query(self, query_values: dict, page: int = 1, page_size: int = 20) -> PageData:
        filtered_data = products.copy()
        # 实现查询过滤逻辑
        for field_name, value in query_values.items():
            if value:
                filtered_data = [
                    item for item in filtered_data
                    if str(item.get(field_name, "")).lower().find(str(value).lower()) >= 0
                ]
        # 分页
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        return PageData(data=filtered_data[start_idx:end_idx], total=len(filtered_data))
    
    async def create(self, item: dict):
        # 生成新 ID
        max_id = max((p["id"] for p in products), default=0)
        item["id"] = max_id + 1
        products.append(item)
    
    async def update(self, item: dict):
        for i, p in enumerate(products):
            if p["id"] == item["id"]:
                products[i] = item
                break
    
    async def delete(self, item_id: str):
        global products
        products = [p for p in products if str(p["id"]) != str(item_id)]

@ui.page('/')
def main():
    fields = [
        FieldDefinition(name="id", title="ID", type="integer", readonly=True),
        FieldDefinition(name="name", title="产品名称", type="text", required=True, show_in_query=True),
        FieldDefinition(name="price", title="价格", type="number", min_value=0, step=0.01),
        FieldDefinition(name="category", title="分类", type="text", show_in_query=True),
    ]
    
    crud = ProductCRUD(
        fields=fields,
        id_field="id",
        heading="产品管理",
        add_button_text="添加产品",
        delete_button_text="删除选中",
    )

if __name__ in {"__main__", "__mp_main__"}:
    ui.run()
```

## NiceCRUDConfig 配置类

`NiceCRUDConfig` 继承自 `NiceTableConfig`，增加了 CRUD 相关的配置项。

### 新增配置项

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `add_button_text` | str | "新增" | 新增按钮文本 |
| `delete_button_text` | str | "删除选中" | 删除选中按钮文本 |
| `new_item_dialog_heading` | str | None | 新增对话框标题 |
| `update_item_dialog_heading` | str | None | 编辑对话框标题 |
| `additional_exclude` | List[str] | [] | 额外排除的字段列表 |
| `show_detail_action` | bool | False | CRUD 模式默认不显示详情按钮 |
| `table_type` | str | "table" | 表格显示类型：`"table"` 或 `"grid"` |
| `class_card_selected` | str | "dark:bg-slate-800 bg-slate-100" | Grid 模式选中卡片样式 |
| `column_count` | int | None | 表单列数（自动计算） |

### 继承的配置项

参见 [NiceTable 文档](./NiceTable.md) 中的 `NiceTableConfig` 配置。

## 使用本地数据

NiceCRUD 内置了基于本地数据的默认 CRUD 实现，可以直接传入数据使用：

```python
from niceguiext import NiceCRUD, FieldDefinition

# 初始数据
data = [
    {"id": 1, "name": "Item 1", "value": 100},
    {"id": 2, "name": "Item 2", "value": 200},
]

fields = [
    FieldDefinition(name="id", title="ID", type="integer", readonly=True),
    FieldDefinition(name="name", title="名称", type="text"),
    FieldDefinition(name="value", title="数值", type="number"),
]

# 直接使用，无需重写方法
crud = NiceCRUD(
    fields=fields,
    data=data,  # 传入本地数据
    id_field="id",
    heading="数据管理",
)
```

## Grid 模式

NiceCRUD 支持卡片网格模式，适合展示更丰富的内容：

```python
crud = NiceCRUD(
    fields=fields,
    id_field="id",
    heading="产品管理",
    table_type="grid",  # 使用网格模式
)
```

## 需要重写的方法

### query 方法

查询数据，与 NiceTable 相同：

```python
async def query(self, query_values: dict, page: int = 1, page_size: int = 20) -> PageData:
    """
    查询数据
    
    Args:
        query_values: 查询条件字典
        page: 当前页码
        page_size: 每页条数
    
    Returns:
        PageData: 分页数据
    """
    # 实现查询逻辑
    return PageData(data=[], total=0)
```

### create 方法

创建新数据：

```python
async def create(self, item: dict):
    """
    创建新项目
    
    Args:
        item: 新项目数据字典
    """
    # 保存到数据库
    pass
```

### update 方法

更新数据：

```python
async def update(self, item: dict):
    """
    更新项目
    
    Args:
        item: 更新后的项目数据字典
    """
    # 更新数据库
    pass
```

### delete 方法

删除数据：

```python
async def delete(self, item_id: str):
    """
    删除项目
    
    Args:
        item_id: 要删除的项目 ID
    """
    # 从数据库删除
    pass
```

### detail 方法（可选）

获取详情数据：

```python
async def detail(self, item_id: str):
    """
    获取项目详情
    
    Args:
        item_id: 项目 ID
    
    Returns:
        项目数据字典
    """
    # 从数据库获取详情
    return {}
```

### select_options 方法（可选）

动态获取选择选项：

```python
async def select_options(self, field_name: str, item: dict) -> dict:
    """
    获取字段的选择选项
    
    Args:
        field_name: 字段名
        item: 当前数据
    
    Returns:
        选项字典 {"value": "label"}
    """
    if field_name == "category":
        return {"cat1": "分类1", "cat2": "分类2"}
    return {}
```

## 完整示例

```python
from nicegui import ui
from niceguiext import NiceCRUD, FieldDefinition, PageData, ActionConfig

# 模拟数据库
users = [
    {"id": 1, "name": "张三", "age": 25, "role": "admin", "active": True},
    {"id": 2, "name": "李四", "age": 30, "role": "user", "active": True},
    {"id": 3, "name": "王五", "age": 28, "role": "user", "active": False},
]

class UserCRUD(NiceCRUD):
    async def select_options(self, field_name: str, item: dict) -> dict:
        if field_name == "role":
            return {"admin": "管理员", "user": "普通用户", "guest": "访客"}
        return {}
    
    async def query(self, query_values: dict, page: int = 1, page_size: int = 20) -> PageData:
        filtered = users.copy()
        
        for field_name, value in query_values.items():
            if value is None or value == "":
                continue
            if field_name == "role":
                filtered = [u for u in filtered if u.get("role") == value]
            else:
                filtered = [
                    u for u in filtered
                    if str(u.get(field_name, "")).lower().find(str(value).lower()) >= 0
                ]
        
        total = len(filtered)
        start = (page - 1) * page_size
        end = start + page_size
        
        return PageData(data=filtered[start:end], total=total)
    
    async def create(self, item: dict):
        max_id = max((u["id"] for u in users), default=0)
        item["id"] = max_id + 1
        users.append(item)
        ui.notify(f"创建成功: {item['name']}", color="positive")
    
    async def update(self, item: dict):
        for i, u in enumerate(users):
            if u["id"] == item["id"]:
                users[i] = item
                break
        ui.notify(f"更新成功: {item['name']}", color="positive")
    
    async def delete(self, item_id: str):
        global users
        users = [u for u in users if str(u["id"]) != str(item_id)]
        ui.notify(f"删除成功", color="positive")

@ui.page('/')
def main():
    ui.page_title("用户管理系统")
    
    fields = [
        FieldDefinition(
            name="id",
            title="ID",
            type="integer",
            readonly=True,
            show_in_table=True,
        ),
        FieldDefinition(
            name="name",
            title="姓名",
            type="text",
            required=True,
            show_in_table=True,
            show_in_query=True,
        ),
        FieldDefinition(
            name="age",
            title="年龄",
            type="integer",
            min_value=0,
            max_value=150,
            show_in_table=True,
        ),
        FieldDefinition(
            name="role",
            title="角色",
            type="tag",
            input_type="select",
            selections={
                "admin": "管理员|blue",
                "user": "普通用户|green",
                "guest": "访客|gray",
            },
            show_in_table=True,
            show_in_query=True,
        ),
        FieldDefinition(
            name="active",
            title="激活状态",
            type="boolean",
            default=True,
            show_in_table=True,
        ),
    ]
    
    # 自定义操作
    def handle_reset_password(row_data):
        ui.notify(f"重置 {row_data.get('name')} 的密码", color="info")
    
    crud = UserCRUD(
        fields=fields,
        id_field="id",
        heading="用户管理",
        add_button_text="添加用户",
        delete_button_text="批量删除",
        new_item_dialog_heading="添加新用户",
        update_item_dialog_heading="编辑用户信息",
        page_size=10,
        actions=[
            ActionConfig(
                label="重置密码",
                call=handle_reset_password,
                color="warning",
                icon="lock_reset",
            ),
        ],
    )

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(port=8080)
```

## NiceCRUDCard 组件

`NiceCRUDCard` 是用于编辑表单的卡片组件，通常由 NiceCRUD 内部使用，但也可以单独使用：

```python
from niceguiext.nicecrud import NiceCRUDCard, NiceCRUDConfig

# 创建编辑卡片
card = NiceCRUDCard(
    item={"id": 1, "name": "测试"},
    fields=fields,
    config=NiceCRUDConfig(),
    id_editable=False,  # ID 不可编辑
    on_change_extra=lambda field, data: print(f"Changed: {field}"),
    on_validation_result=lambda valid: print(f"Valid: {valid}"),
)
```

## 字段类型在表单中的表现

| 字段类型 | 输入组件 |
|----------|----------|
| `text` | 文本输入框 |
| `integer` | 数字输入框 |
| `number` | 数字输入框 |
| `boolean` | 复选框 |
| `date` | 日期选择器 |
| `datetime` | 日期时间输入框 |
| `select` | 下拉选择框 |
| `multiselect` | 多选下拉框 |
| `slider` | 滑动条 |

## 验证功能

NiceCRUD 支持字段验证：

```python
FieldDefinition(
    name="email",
    title="邮箱",
    type="text",
    required=True,
    validation=lambda v: "请输入有效的邮箱地址" if "@" not in str(v) else None,
)
```

也可以使用字典形式定义多个验证规则：

```python
FieldDefinition(
    name="password",
    title="密码",
    type="text",
    validation={
        "密码长度至少8位": lambda v: len(str(v)) >= 8,
        "密码必须包含数字": lambda v: any(c.isdigit() for c in str(v)),
    },
)
```
