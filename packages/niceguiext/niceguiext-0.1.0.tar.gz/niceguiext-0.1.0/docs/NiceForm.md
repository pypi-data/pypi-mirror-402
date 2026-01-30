# NiceForm 组件文档

NiceForm 是一个基于字段定义列表的表单组件，支持多种输入类型（文本、数字、选择框等），具备数据验证逻辑，并提供提交和重置功能。

## 功能特性

- 支持多种输入类型（文本、数字、日期、选择框、滑动条等）
- 自动类型转换和验证
- 支持可选字段和必填字段
- 支持提交和重置回调
- 支持字段变化回调
- 响应式表单验证状态

## 安装

```bash
pip install niceguiext
```

## 基本用法

```python
from nicegui import ui
from niceguiext import NiceForm, FormConfig
from niceguiext.form import FieldDefinition

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
        min_value=0,
        max_value=120,
        default=25,
    ),
    FieldDefinition(
        name="email",
        field_type=str,
        title="邮箱",
        required=False,
        default="",
    ),
]

# 表单配置
config = FormConfig(
    title="用户信息",
    submit_button_text="提交",
    reset_button_text="重置",
)

async def handle_submit(form_data: dict):
    print("提交的数据:", form_data)
    ui.notify("提交成功!", color="positive")

# 创建表单
form = NiceForm(
    fields=fields,
    config=config,
    on_submit=handle_submit,
)

ui.run()
```

## FieldDefinition 字段定义

NiceForm 使用的 `FieldDefinition` 是一个 dataclass，与 NiceTable/NiceCRUD 中的略有不同。

### 属性说明

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `name` | str | 必填 | 字段名称 |
| `field_type` | Any | 必填 | 字段类型（Python 类型） |
| `default` | Any | None | 默认值 |
| `title` | str | None | 字段显示标题 |
| `description` | str | None | 字段描述（显示为 placeholder 或 tooltip） |
| `required` | bool | True | 是否必填 |
| `min_value` | float | None | 最小值（数字类型） |
| `max_value` | float | None | 最大值（数字类型） |
| `step` | float | None | 步长（数字类型） |
| `input_type` | str | None | 输入类型：`"select"`, `"multiselect"`, `"slider"`, `"number"` |
| `readonly` | bool | False | 是否只读 |
| `selections` | dict | None | 选择选项 |
| `exclude` | bool | False | 是否排除显示 |

### 支持的 field_type 类型

| Python 类型 | 输入组件 |
|-------------|----------|
| `str` | 文本输入框 |
| `int` | 数字输入框 |
| `float` | 数字输入框 |
| `bool` | 开关 |
| `date` | 日期选择器 |
| `time` | 时间选择器 |
| `datetime` | 日期时间选择器 |
| `Path` | 文本输入框 |
| `list[str]` | 文本输入框（逗号分隔） |
| `list[int]` | 文本输入框（逗号分隔） |
| `Literal[...]` | 下拉选择框 |
| `Optional[T]` | 对应类型的可清空输入框 |

## FormConfig 配置类

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `title` | str | None | 表单标题 |
| `submit_button_text` | str | "提交" | 提交按钮文本 |
| `reset_button_text` | str | "重置" | 重置按钮文本 |
| `class_heading` | str | "text-xl font-bold" | 标题样式类 |
| `class_form_card` | str | "w-full p-4" | 表单卡片样式类 |
| `column_count` | int | None | 表单列数（自动计算） |
| `show_validation_errors` | bool | True | 是否显示验证错误 |

## 完整示例

```python
from datetime import date
from pathlib import Path
from typing import Union, Literal

from nicegui import ui
from niceguiext import NiceForm, FormConfig
from niceguiext.form import FieldDefinition

@ui.page("/")
async def main():
    # 定义表单字段
    fields = [
        # 文本字段
        FieldDefinition(
            name="name",
            field_type=str,
            title="姓名",
            description="请输入您的姓名",
            required=True,
            default="",
        ),
        # 数字字段（带范围限制）
        FieldDefinition(
            name="age",
            field_type=int,
            title="年龄",
            description="请输入您的年龄",
            min_value=0,
            max_value=120,
            default=25,
        ),
        # 可选字段
        FieldDefinition(
            name="email",
            field_type=Union[str, type(None)],
            title="邮箱",
            description="请输入您的邮箱地址",
            required=False,
            default=None,
        ),
        # 选择框字段
        FieldDefinition(
            name="gender",
            field_type=str,
            title="性别",
            input_type="select",
            selections={"male": "男", "female": "女", "other": "其他"},
            default="male",
        ),
        # 滑动条字段
        FieldDefinition(
            name="salary",
            field_type=float,
            title="期望薪资",
            min_value=0.0,
            max_value=100000.0,
            input_type="slider",
            step=1000.0,
            default=10000.0,
        ),
        # 列表字段
        FieldDefinition(
            name="skills",
            field_type=list[str],
            title="技能",
            description="请输入您的技能，用逗号分隔",
            default=[],
        ),
        # 布尔字段
        FieldDefinition(
            name="is_active",
            field_type=bool,
            title="是否激活",
            default=True,
        ),
        # 日期字段
        FieldDefinition(
            name="birth_date",
            field_type=date,
            title="出生日期",
            default=date(1990, 1, 1),
        ),
        # 路径字段（可选）
        FieldDefinition(
            name="profile_path",
            field_type=Union[Path, type(None)],
            title="头像路径",
            required=False,
            default=None,
        ),
        # Literal 类型（枚举选择）
        FieldDefinition(
            name="priority",
            field_type=Literal["low", "medium", "high"],
            title="优先级",
            default="medium",
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
        ui.notify(f"提交成功！", color="positive")

    def handle_change(field_name: str, form_data: dict):
        """处理字段变化"""
        print(f"字段 {field_name} 变化: {form_data.get(field_name)}")

    # 创建表单
    form = NiceForm(
        fields=fields,
        config=config,
        on_submit=handle_submit,
        on_change=handle_change,
    )

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="NiceForm 示例")
```

## 动态选择选项

可以通过 `select_options` 参数动态获取选择选项：

```python
async def get_select_options(field_name: str, form_data: dict) -> dict:
    """动态获取选择选项"""
    if field_name == "city":
        # 根据省份返回城市列表
        province = form_data.get("province")
        if province == "guangdong":
            return {"shenzhen": "深圳", "guangzhou": "广州", "dongguan": "东莞"}
        elif province == "beijing":
            return {"chaoyang": "朝阳区", "haidian": "海淀区"}
    return {}

form = NiceForm(
    fields=fields,
    config=config,
    on_submit=handle_submit,
    select_options=get_select_options,
)
```

## 访问表单数据

可以通过 `form.form_data` 访问当前表单数据：

```python
form = NiceForm(fields=fields, config=config)

# 获取当前表单数据
current_data = form.form_data

# 检查表单验证状态
is_valid = form.form_valid
```

## 表单验证

NiceForm 自动进行类型验证和范围验证：

- **类型验证**：根据 `field_type` 自动转换和验证值
- **范围验证**：对数字类型检查 `min_value` 和 `max_value`
- **必填验证**：对非可选字段检查是否有值

验证错误会显示在表单底部（如果 `show_validation_errors=True`），并且提交按钮会在表单无效时禁用。

## 手动刷新表单

如果需要手动刷新表单，可以调用：

```python
form.create_form.refresh()
```

## 重置表单

点击重置按钮会将所有字段恢复到默认值，也可以手动调用：

```python
form.handle_reset()
```
