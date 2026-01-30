# show_error 和 show_warn 组件文档

`show_error` 和 `show_warn` 是用于显示错误和警告消息的工具函数，提供统一的视觉样式。

## 功能特性

- 醒目的错误/警告样式
- 带图标的消息显示
- 返回 UI 元素引用，支持动态绑定

## 安装

```bash
pip install niceguiext
```

## 基本用法

### show_error

显示错误消息，使用红色文字和黄色背景：

```python
from nicegui import ui
from niceguiext import show_error

# 显示静态错误消息
show_error("发生了一个错误！")

ui.run()
```

### show_warn

显示警告消息，使用橙色文字和白色背景：

```python
from nicegui import ui
from niceguiext import show_warn

# 显示警告消息
show_warn("这是一个警告信息")

ui.run()
```

## 函数签名

### show_error

```python
def show_error(message: str = "Something went horribly wrong") -> tuple[ui.label, ui.row]:
    """
    显示错误消息
    
    Args:
        message: 错误消息文本
    
    Returns:
        tuple: (label_element, row_element) - 标签元素和行容器元素
    """
```

### show_warn

```python
def show_warn(message: str = "Something went not quite as horribly wrong, but still not good") -> None:
    """
    显示警告消息
    
    Args:
        message: 警告消息文本
    """
```

## 动态绑定

`show_error` 返回标签元素和行容器元素，可以用于动态绑定：

```python
from nicegui import ui
from niceguiext import show_error

# 创建一个响应式的错误状态
error_state = {"msg": "", "visible": False}

# 创建错误显示组件
label_element, row_element = show_error("")

# 绑定文本和可见性
label_element.bind_text_from(error_state, "msg")
row_element.bind_visibility_from(error_state, "visible")

# 模拟错误发生
def trigger_error():
    error_state["msg"] = "操作失败：无法连接到服务器"
    error_state["visible"] = True

def clear_error():
    error_state["visible"] = False

ui.button("触发错误", on_click=trigger_error)
ui.button("清除错误", on_click=clear_error)

ui.run()
```

## 样式说明

### show_error 样式

- 背景色：黄色 (`bg-yellow-100`)
- 文字颜色：红色 (`text-red-500`)
- 左边框：黄色粗边框 (`border-l-8 border-yellow-500`)
- 图标：错误图标 (`error`)
- 字体：粗体 (`font-bold`)

### show_warn 样式

- 背景色：白色 (`bg-white`)
- 文字颜色：橙色 (`text-orange-500`)
- 左边框：橙色边框 (`border-l-4 border-orange-500`)
- 图标：警告图标 (`warning`)
- 内边距：`p-4`

## 在表单中使用

常见用法是在表单验证中显示错误：

```python
from nicegui import ui
from niceguiext import show_error

class MyForm:
    def __init__(self):
        self.errormsg = {"msg": "", "visible": False}
        
        with ui.card():
            ui.input("用户名", on_change=self.validate)
            ui.input("密码", password=True, on_change=self.validate)
            
            # 错误显示区域
            errlabel, errrow = show_error("")
            errlabel.bind_text_from(self.errormsg, "msg")
            errrow.bind_visibility_from(self.errormsg, "visible")
            
            ui.button("提交", on_click=self.submit)
    
    def validate(self, e):
        if len(e.value) < 3:
            self.errormsg["msg"] = "输入长度至少3个字符"
            self.errormsg["visible"] = True
        else:
            self.errormsg["visible"] = False
    
    def submit(self):
        if self.errormsg["visible"]:
            ui.notify("请修正错误后再提交", color="negative")
        else:
            ui.notify("提交成功", color="positive")

MyForm()
ui.run()
```

## 自定义样式

如果需要自定义样式，可以直接修改返回的元素：

```python
from nicegui import ui
from niceguiext import show_error

label, row = show_error("自定义错误")

# 修改行容器样式
row.classes(remove="bg-yellow-100", add="bg-red-100")

# 修改标签样式
label.classes(add="text-lg")

ui.run()
```
