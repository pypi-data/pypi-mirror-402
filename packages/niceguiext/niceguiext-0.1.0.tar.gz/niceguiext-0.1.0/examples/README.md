# NiceCRUD 示例集合

这个目录包含了 NiceCRUD 组件的各种使用示例，从简单的入门示例到复杂的高级功能演示。

## 📁 示例文件说明

### 1. `nicecrud_simple.py` - 快速入门
**端口**: 8081  
**适合人群**: 初学者  
**特性**:
- 最简单的 CRUD 实现
- 基础字段类型演示
- 快速上手，代码量少

**运行方式**:
```bash
python examples/nicecrud_simple.py
```

### 2. `nicecrud_example.py` - 完整功能示例
**端口**: 8080  
**适合人群**: 需要了解完整功能的开发者  
**特性**:
- 用户管理系统完整实现
- 查询、分页、增删改查全流程
- 多种字段类型：文本、数字、选择、多选、布尔、日期
- 自定义配置和样式
- 详细的使用说明文档

**运行方式**:
```bash
python examples/nicecrud_example.py
```

### 3. `nicecrud_advanced.py` - 高级功能演示
**端口**: 8082  
**适合人群**: 需要使用高级功能的开发者  
**特性**:
- 动态选项加载（城市根据国家动态更新）
- 滑块控件（评分字段）
- 多选标签（技能选择）
- 自定义数据验证
- 异步数据服务模拟
- 渐变样式和动画效果

**运行方式**:
```bash
python examples/nicecrud_advanced.py
```

### 4. `nicecrud_grid.py` - 网格模式展示
**端口**: 8083  
**适合人群**: 需要卡片式展示的场景  
**特性**:
- 网格布局模式
- 产品展示系统
- 卡片式数据展示
- 美观的 UI 设计
- 悬停动画效果
- 多维度筛选功能

**运行方式**:
```bash
python examples/nicecrud_grid.py
```

## 🚀 快速开始

1. **安装依赖**:
```bash
pip install nicegui pydantic
```

2. **运行任一示例**:
```bash
# 选择一个示例运行
python examples/nicecrud_simple.py
```

3. **在浏览器中访问**:
```
http://localhost:端口号
```

## 📋 字段类型支持

| 字段类型 | 描述 | 示例 |
|---------|------|------|
| `text` | 文本输入 | 姓名、邮箱、描述 |
| `integer` | 整数输入 | ID、年龄、数量 |
| `number` | 数字输入 | 价格、评分、百分比 |
| `boolean` | 布尔选择 | 是否激活、是否推荐 |
| `date` | 日期选择 | 入职日期、创建时间 |
| `datetime` | 日期时间 | 最后登录时间 |

## 🎛️ 输入控件类型

| 控件类型 | 适用字段 | 描述 |
|---------|---------|------|
| `select` | text | 下拉单选 |
| `multiselect` | text | 下拉多选 |
| `slider` | number/integer | 滑块输入 |
| `number` | number/integer | 数字输入框 |

## ⚙️ 字段配置选项

### 基础配置
- `name`: 字段名称（必填）
- `title`: 显示标题（必填）
- `type`: 字段类型
- `required`: 是否必填
- `default`: 默认值
- `description`: 字段描述

### 显示控制
- `readonly`: 是否只读
- `exclude`: 是否排除显示
- `show_in_table`: 是否在表格中显示
- `show_in_query`: 是否作为查询条件

### 数字字段专用
- `min_value`: 最小值
- `max_value`: 最大值
- `step`: 步长

### 选择字段专用
- `selections`: 静态选择选项
- `input_type`: 输入控件类型

### 文本字段专用
- `max_length`: 最大长度

## 🎨 自定义样式

NiceCRUD 支持通过 `NiceCRUDConfig` 自定义样式：

```python
config = NiceCRUDConfig(
    class_heading="text-3xl font-bold text-blue-600",
    class_card="bg-white shadow-lg rounded-lg",
    class_card_selected="bg-blue-50 border-2 border-blue-400",
    class_card_header="bg-blue-600 text-white"
)
```

## 🔧 高级功能

### 1. 动态选项加载
```python
async def select_options(self, field_name: str, item: Dict[str, Any]) -> Dict[str, str]:
    if field_name == "city":
        country = item.get("country")
        return await get_cities_by_country(country)
    return {}
```

### 2. 自定义验证
```python
async def create(self, item: Dict[str, Any]):
    if not item.get("email"):
        raise ValueError("邮箱不能为空")
    if "@" not in item.get("email", ""):
        raise ValueError("邮箱格式不正确")
    # ... 保存逻辑
```

### 3. 异步数据操作
```python
async def query(self, query_values: dict, page: int = 1, page_size: int = 20) -> PageData:
    # 异步数据库查询
    data = await database.query(query_values, page, page_size)
    return PageData(data=data.items, total=data.total)
```

## 📞 获取帮助

如果在使用过程中遇到问题：

1. 查看示例代码中的注释
2. 参考 `nicecrud.py` 源码中的文档字符串
3. 检查浏览器控制台的错误信息
4. 确保字段定义和数据结构匹配

## 🎯 最佳实践

1. **字段命名**: 使用清晰、一致的字段名称
2. **类型匹配**: 确保字段类型与实际数据类型匹配
3. **验证逻辑**: 在 `create` 和 `update` 方法中添加适当的验证
4. **错误处理**: 使用 `try-catch` 处理异步操作中的错误
5. **性能优化**: 对于大量数据，实现真正的分页查询而不是前端分页
6. **用户体验**: 提供清晰的错误信息和成功反馈

---

希望这些示例能帮助您快速掌握 NiceCRUD 的使用方法！🎉