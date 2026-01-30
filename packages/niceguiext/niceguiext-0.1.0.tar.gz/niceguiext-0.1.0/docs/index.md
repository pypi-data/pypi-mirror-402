# NiceGUIExt 文档

NiceGUIExt 是一个基于 [NiceGUI](https://nicegui.io) 的扩展组件库，提供了 CRUD 界面、表格、表单等常用组件，帮助快速构建数据管理界面。

## 功能特性

- **NiceTable** - 功能丰富的表格组件，支持查询、分页、详情查看
- **NiceCRUD** - 基于 NiceTable 的 CRUD 组件，支持增删改查
- **NiceForm** - 基于字段定义的表单组件，支持多种输入类型
- **show_error/show_warn** - 错误和警告消息显示组件

## 安装

```bash
pip install niceguiext
```

## 快速开始

### 简单的 CRUD 示例

```python
from nicegui import ui
from niceguiext import NiceCRUD, FieldDefinition

# 定义字段
fields = [
    FieldDefinition(name="id", title="ID", type="integer", readonly=True),
    FieldDefinition(name="name", title="名称", type="text", required=True, show_in_query=True),
    FieldDefinition(name="price", title="价格", type="number", min_value=0),
]

# 初始数据
data = [
    {"id": 1, "name": "产品A", "price": 100},
    {"id": 2, "name": "产品B", "price": 200},
]

# 创建 CRUD 组件
crud = NiceCRUD(
    fields=fields,
    data=data,
    id_field="id",
    heading="产品管理",
)

ui.run()
```

## 组件文档

- [NiceTable](./NiceTable.md) - 表格组件
- [NiceCRUD](./NiceCRUD.md) - CRUD 组件
- [NiceForm](./NiceForm.md) - 表单组件
- [show_error](./show_error.md) - 错误/警告显示组件

## 导入方式

```python
# 推荐的导入方式
from niceguiext import (
    NiceTable,
    NiceTableConfig,
    NiceCRUD,
    NiceCRUDConfig,
    NiceForm,
    FormConfig,
    FieldDefinition,
    PageData,
    ActionConfig,
    show_error,
    show_warn,
)

# 或者从子模块导入
from niceguiext.nicetable import NiceTable, FieldDefinition, PageData
from niceguiext.nicecrud import NiceCRUD, NiceCRUDCard
from niceguiext.form import NiceForm, FormConfig
from niceguiext.show_error import show_error, show_warn
```

## 核心概念

### FieldDefinition

`FieldDefinition` 是定义字段的核心类，用于描述数据字段的类型、验证规则、显示方式等。

```python
from niceguiext import FieldDefinition

field = FieldDefinition(
    name="email",           # 字段名
    title="邮箱",           # 显示标题
    type="text",            # 字段类型
    required=True,          # 是否必填
    show_in_table=True,     # 是否在表格中显示
    show_in_query=True,     # 是否作为查询条件
    show_in_detail=True,    # 是否在详情中显示
)
```

### PageData

`PageData` 用于封装分页查询的返回结果：

```python
from niceguiext import PageData

# 查询方法返回 PageData
async def query(self, query_values: dict, page: int, page_size: int) -> PageData:
    data = [...]  # 当前页数据
    total = 100   # 总条数
    return PageData(data=data, total=total)
```

### ActionConfig

`ActionConfig` 用于配置表格行的自定义操作按钮：

```python
from niceguiext import ActionConfig

action = ActionConfig(
    label="编辑",
    call=handle_edit,  # 可以是函数或方法名字符串
    color="primary",
    icon="edit",
    tooltip="编辑此项",
)
```

## 字段类型

| 类型 | 说明 | 适用组件 |
|------|------|----------|
| `text` | 文本 | NiceTable, NiceCRUD |
| `integer` | 整数 | NiceTable, NiceCRUD |
| `number` | 浮点数 | NiceTable, NiceCRUD |
| `boolean` | 布尔值 | NiceTable, NiceCRUD |
| `date` | 日期 | NiceTable, NiceCRUD |
| `datetime` | 日期时间 | NiceTable, NiceCRUD |
| `json` | JSON 数据 | NiceTable, NiceCRUD |
| `html` | HTML 内容 | NiceTable, NiceCRUD |
| `tag` | 彩色标签 | NiceTable, NiceCRUD |

## 示例项目

查看 [examples](../examples) 目录获取更多示例：

| 示例 | 说明 |
|------|------|
| `nicecrud_simple.py` | NiceCRUD 简单示例 |
| `nicecrud_example.py` | NiceCRUD 完整示例 |
| `nicecrud_advanced.py` | NiceCRUD 高级用法 |
| `nicecrud_grid.py` | NiceCRUD 网格模式 |
| `nicetable_example.py` | NiceTable 示例 |
| `form_field_definition_example.py` | NiceForm 示例 |
| `validation_example.py` | 验证功能示例 |

## 许可证

MIT License
