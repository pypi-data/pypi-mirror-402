# pyright: reportArgumentType=false
"""
NiceTable - 带查询和可扩展action的表格组件

功能特性：
- 支持查询条件配置
- 支持可扩展的action按钮
- 支持查看详情功能
- 支持分页
- 支持多种字段类型的查询（日期范围、数字范围等）
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Callable, Optional, Union, Any, Dict, List, Literal
import asyncio

from nicegui import events, ui
from pydantic import BaseModel, Field

# 东八区时区
TZ_SHANGHAI = timezone(timedelta(hours=8))

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class ActionConfig(BaseModel):
    """自定义操作按钮配置"""

    label: str = Field(description="按钮显示文本")
    call: Union[str, Callable] = Field(description="调用的函数名或函数对象")
    color: str = Field(default="primary", description="按钮颜色")
    icon: Optional[str] = Field(default=None, description="按钮图标")
    tooltip: Optional[str] = Field(default=None, description="按钮提示文本")


class FieldDefinition(BaseModel):
    """动态字段定义"""

    name: str = Field(description="字段名称")
    title: str = Field(description="字段显示标题")
    type: str = Field(default="text", description="字段类型")
    description: Optional[str] = Field(default=None, description="字段描述")
    default: Any = Field(default=None, description="默认值")
    required: bool = Field(default=True, description="是否必填")

    # 数字类型相关
    min_value: Optional[float] = Field(default=None, description="最小值")
    max_value: Optional[float] = Field(default=None, description="最大值")
    step: Optional[float] = Field(default=None, description="步长")

    # 选择类型相关
    input_type: Optional[Literal["slider", "number", "select", "multiselect"]] = Field(default=None)
    selections: Optional[Dict[str, str]] = Field(default=None, description="选择选项")
    show_selection_label: Optional[bool] = Field(default=None)

    # 显示控制
    readonly: bool = Field(default=False, description="是否只读")
    exclude: bool = Field(default=False, description="是否排除显示")
    show_in_table: bool = Field(default=False, description="是否在表格中显示")
    show_in_query: bool = Field(default=False, description="是否作为查询条件")
    show_in_expand: bool = Field(default=False, description="是否在展开行中显示")
    show_in_detail: bool = Field(default=False, description="是否在详情对话框中显示")

    # 文本类型相关
    max_length: Optional[int] = Field(default=None, description="最大长度")

    # datetime 类型相关
    datetime_format: str = Field(default="%Y-%m-%d %H:%M:%S", description="datetime格式化字符串")

    # 验证相关
    validation: Optional[Union[Callable, Dict[str, Callable]]] = Field(
        default=None, description="验证规则"
    )
    validation_error: Optional[str] = Field(default=None, description="验证错误消息")


class PageData(BaseModel):
    """分页数据类，包含数据和总数"""

    data: List[Dict[str, Any]] = Field(description="当前页的数据")
    total: int = Field(description="总数据条数")


class FieldHelperMixin:
    """动态字段处理 Mixin 类"""

    # 声明这些属性将由子类提供
    fields: List[FieldDefinition]
    config: Any  # 配置对象
    included_fields: List[FieldDefinition]
    table_fields: List[FieldDefinition]
    query_fields: List[FieldDefinition]
    expand_fields: List[FieldDefinition]
    detail_fields: List[FieldDefinition]

    def __init__(self):
        self.get_included_fields()
        self.get_table_fields()
        self.get_query_fields()
        self.get_expand_fields()
        self.get_detail_fields()

    def is_excluded(self, field_def: FieldDefinition) -> bool:
        """检查字段是否应该被排除"""
        return field_def.exclude or field_def.name in getattr(self.config, "additional_exclude", [])

    def get_included_fields(self):
        """获取包含在卡片中的字段列表"""
        self.included_fields = []
        for field_def in self.fields:
            if not self.is_excluded(field_def):
                self.included_fields.append(field_def)

    def get_table_fields(self):
        """获取在表格中显示的字段列表"""
        self.table_fields = []
        for field_def in self.fields:
            if not self.is_excluded(field_def) and field_def.show_in_table:
                self.table_fields.append(field_def)

    def get_query_fields(self):
        """获取用作查询条件的字段列表"""
        self.query_fields = []
        for field_def in self.fields:
            if not self.is_excluded(field_def) and field_def.show_in_query:
                self.query_fields.append(field_def)

    def get_expand_fields(self):
        """获取在展开行中显示的字段列表"""
        self.expand_fields = []
        for field_def in self.fields:
            if not self.is_excluded(field_def) and field_def.show_in_expand:
                self.expand_fields.append(field_def)

    def get_detail_fields(self):
        """获取在详情对话框中显示的字段列表"""
        self.detail_fields = []
        for field_def in self.fields:
            if not self.is_excluded(field_def) and field_def.show_in_detail:
                self.detail_fields.append(field_def)

    @property
    def included_field_names(self):
        return [field.name for field in self.included_fields]

    @property
    def table_field_names(self):
        return [field.name for field in self.table_fields]

    @property
    def query_field_names(self):
        return [field.name for field in self.query_fields]

    @property
    def expand_field_names(self):
        return [field.name for field in self.expand_fields]

    @property
    def detail_field_names(self):
        return [field.name for field in self.detail_fields]

    def field_exists(self, field_name: str):
        return field_name in [field.name for field in self.fields]

    def get_field_by_name(self, field_name: str) -> Optional[FieldDefinition]:
        """根据字段名获取字段定义"""
        for field in self.fields:
            if field.name == field_name:
                return field
        return None


class NiceTableConfig(BaseModel):
    """NiceTable 配置类"""

    id_field: str = ""
    id_label: Optional[str] = None
    no_data_label: str = "No data"
    heading: str = "列表"
    query_button_text: str = "查询"
    reset_button_text: str = "重置"
    detail_button_text: str = "详情"
    detail_dialog_heading: Optional[str] = None
    show_detail_action: bool = Field(default=True, description="是否显示查看详情按钮")
    page_size: int = Field(default=20)
    actions: List[ActionConfig] = Field(default_factory=list, description="表格行操作按钮")

    class_heading: str = Field(default="text-xl font-bold")
    class_card: str = Field(default="dark:bg-slate-900 bg-slate-200")
    class_card_header: str = Field(default="dark:bg-slate-700 bg-slate-50")

    def update(self, data: dict):
        for k, v in data.items():
            setattr(self, k, v)


class NiceTable(FieldHelperMixin):
    """带查询和可扩展action的表格组件"""

    # 表格列显示最大字符数
    MAX_DISPLAY_LENGTH = 60

    # Tag 颜色映射到 Tailwind CSS 类
    TAG_COLOR_CLASSES = {
        "red": "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300",
        "green": "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300",
        "blue": "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300",
        "orange": "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300",
        "yellow": "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300",
        "purple": "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300",
        "pink": "bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-300",
        "cyan": "bg-cyan-100 text-cyan-800 dark:bg-cyan-900 dark:text-cyan-300",
        "gray": "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300",
    }

    def __init__(
        self,
        fields: List[FieldDefinition],
        id_field: Optional[str] = None,
        config: Union[NiceTableConfig, dict] = NiceTableConfig(),
        **kwargs,
    ):
        self.fields = fields

        if isinstance(config, dict):
            table_config = NiceTableConfig(**config, **kwargs)
        else:
            table_config = config  # type: ignore
        self.config = table_config  # type: ignore
        self.config.update(kwargs)

        if id_field is not None:
            self.config.id_field = id_field

        # 初始化字段处理
        super().__init__()

        self.rows: List[dict] = []
        self.columns: List[dict] = []
        self.field_selections: Dict[str, Dict[str, str]] = {}
        self.assert_id_field_exists()

        # 查询和分页相关
        self.current_query: dict = {}
        self.query_values: dict = {}
        self.data: List[Dict[str, Any]] = []  # 当前页的数据
        self.page_size: int = self.config.page_size
        self.current_page: int = 1
        self.total_count: int = 0

        # UI 组件引用
        self.detail_dialog: ui.dialog
        self.table: ui.table
        self.query_section: Optional[ui.expansion] = None
        self.pagination_container: Optional[ui.row] = None
        self.page_size_select: Optional[ui.select] = None
        self.goto_page_input: Optional[ui.number] = None

        ui.timer(0, self.render_components, once=True)

    def assert_id_field_exists(self):
        """检查ID字段是否存在"""
        if self.config.id_field and not self.field_exists(self.config.id_field):
            available_fields = [field.name for field in self.fields]
            raise ValueError(
                f"id_field '{self.config.id_field}' not found in fields. "
                f"Available fields: {available_fields}"
            )

    async def collect_field_selections(self):
        """收集字段选择选项"""
        self.field_selections = {}

        for field_def in self.fields:
            if field_def.input_type in ("select", "multiselect"):
                if field_def.selections:
                    self.field_selections[field_def.name] = field_def.selections
                else:
                    try:
                        # 使用当前页的第一条数据作为样本
                        sample_item = self.data[0] if self.data else {}
                        options = await self.select_options(field_def.name, sample_item)
                        self.field_selections[field_def.name] = options
                    except Exception as e:
                        log.warning(f"Failed to get selections for {field_def.name}: {e}")
                        self.field_selections[field_def.name] = {}

    async def select_options(self, field_name: str, item: Dict[str, Any]) -> Dict[str, str]:
        """获取字段的选择选项，子类可重写"""
        return {}

    async def render_components(self):
        """渲染所有组件"""
        await self.collect_field_selections()
        await self.render_heading()
        await self.render_query_section()
        # 初始化加载第一页数据
        page_data = await self.query({}, 1, self.page_size)
        self.data = page_data.data
        self.total_count = page_data.total
        await self.render_table()
        await self.render_pagination()

    async def render_heading(self):
        """渲染标题"""
        ui.label(self.config.heading).classes(self.config.class_heading)

    async def render_query_section(self):
        """渲染查询区域"""
        if not self.query_fields:
            return

        with ui.expansion("查询条件", icon="search").classes("w-full") as self.query_section:
            await self._build_query_content()

    async def _build_query_content(self):
        """构建查询区域的内容（输入框和按钮）"""
        grid_class = "gap-1 gap-x-6 w-full items-center"
        columns = "minmax(100px,max-content) 1fr " * min(len(self.query_fields), 3)

        with ui.grid(columns=columns).classes(grid_class):
            for field_def in self.query_fields:
                await self._create_query_input(field_def)

        with ui.row().classes("w-full justify-end mt-2"):
            ui.button(self.config.query_button_text, on_click=self.handle_query_click).props(
                "color=primary"
            )
            ui.button(self.config.reset_button_text, on_click=self.handle_reset_click).props(
                "color=secondary outline"
            )

    async def _create_query_input(self, field_def: FieldDefinition):
        """创建查询输入组件"""
        field_name = field_def.name

        with ui.label(field_def.title + ":"):
            pass

        if field_def.input_type == "select":
            options = self.field_selections.get(field_name, {})
            # 添加空选项
            options = {"": "全部", **options}
            ui.select(
                options=options,
                value="",
                on_change=lambda e, fn=field_name: self._update_query_value(fn, e.value),
            )
        elif field_def.type in ("date", "datetime"):
            # 日期范围查询
            ui.date_input(
                "Range",
                range_input=True,
                on_change=lambda e, fn=field_name: self._update_date_range_query_value(fn, e.value),
            ).classes("w-full")
        elif field_def.type in ("integer", "number"):
            ui.number(
                placeholder=f"输入{field_def.title}",
                on_change=lambda e, fn=field_name: self._update_query_value(fn, e.value),
            )
        else:
            ui.input(
                placeholder=f"输入{field_def.title}",
                on_change=lambda e, fn=field_name: self._update_query_value(fn, e.value),
            )

    def _update_query_value(self, field_name: str, value):
        """更新查询值"""
        if value == "" or value is None:
            self.query_values.pop(field_name, None)
        else:
            self.query_values[field_name] = value

    def _update_date_range_query_value(self, field_name: str, value):
        """更新日期范围查询值"""
        # 清除旧的范围查询值
        min_field = f"{field_name}_min"
        max_field = f"{field_name}_max"
        self.query_values.pop(min_field, None)
        self.query_values.pop(max_field, None)

        if value and isinstance(value, dict):
            # 处理范围日期值
            if "from" in value and value["from"]:
                self.query_values[min_field] = value["from"]
            if "to" in value and value["to"]:
                self.query_values[max_field] = value["to"]
        elif value and isinstance(value, list) and len(value) == 2:
            # 处理数组形式的范围值 [start_date, end_date]
            if value[0]:
                self.query_values[min_field] = value[0]
            if value[1]:
                self.query_values[max_field] = value[1]
        elif value and not isinstance(value, (dict, list)):
            # 如果是单个日期值，作为开始日期
            self.query_values[min_field] = value

    def _generate_action_buttons_html(self) -> str:
        """生成操作按钮的HTML"""
        buttons_html = ""

        # 根据配置决定是否显示详情按钮
        if self.config.show_detail_action:  # type: ignore
            detail_btn_text = self.config.detail_button_text  # type: ignore
            buttons_html += f'''
        <q-btn size="md" color="info" dense flat label="{detail_btn_text}"
            @click="() => $parent.$emit('detail', props.row)" class="mr-1" />'''

        # 添加自定义action按钮
        for i, action in enumerate(self.config.actions):
            event_name = f"action_{i}"
            icon_html = f' icon="{action.icon}"' if action.icon else ""
            tooltip_html = f' title="{action.tooltip}"' if action.tooltip else ""

            buttons_html += f'''
        <q-btn size="md" color="{action.color}" dense flat label="{action.label}"{icon_html}{tooltip_html}
            @click="() => $parent.$emit('{event_name}', props.row)" class="mr-1" />'''

        return buttons_html

    def _format_json_value(self, value: Any) -> str:
        """格式化 JSON 值为易读的字符串"""
        if value is None:
            return ""
        try:
            # 如果是字符串，尝试解析为 JSON
            if isinstance(value, str):
                try:
                    parsed = json.loads(value)
                    return json.dumps(parsed, indent=2, ensure_ascii=False)
                except json.JSONDecodeError:
                    return value
            # 如果是 dict 或 list，直接格式化
            elif isinstance(value, (dict, list)):
                return json.dumps(value, indent=2, ensure_ascii=False)
            else:
                return str(value)
        except Exception:
            return str(value) if value is not None else ""

    def _format_datetime_value(self, value: Any, field_def: FieldDefinition) -> str:
        """格式化 datetime 类型的值为指定格式的字符串

        Args:
            value: datetime 值，可以是 datetime 对象、字符串或其他类型
            field_def: 字段定义，包含 datetime_format 格式

        Returns:
            格式化后的时间字符串
        """
        if value is None:
            return ""

        fmt = field_def.datetime_format

        if isinstance(value, datetime):
            # 如果有时区信息，转换为东八区
            if value.tzinfo is not None:
                return value.astimezone(TZ_SHANGHAI).strftime(fmt)
            else:
                # 无时区信息，假设是 UTC，转换为东八区
                return value.replace(tzinfo=timezone.utc).astimezone(TZ_SHANGHAI).strftime(fmt)

        if isinstance(value, str):
            # 尝试解析字符串为 datetime
            try:
                # 尝试多种常见格式
                for parse_fmt in [
                    "%Y-%m-%dT%H:%M:%S.%fZ",
                    "%Y-%m-%dT%H:%M:%SZ",
                    "%Y-%m-%dT%H:%M:%S.%f",
                    "%Y-%m-%dT%H:%M:%S",
                    "%Y-%m-%d %H:%M:%S.%f",
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%d",
                ]:
                    try:
                        dt = datetime.strptime(value, parse_fmt)
                        # 如果是 ISO 格式带 Z，表示 UTC
                        if parse_fmt.endswith("Z"):
                            dt = dt.replace(tzinfo=timezone.utc).astimezone(TZ_SHANGHAI)
                        return dt.strftime(fmt)
                    except ValueError:
                        continue
                # 无法解析，返回原字符串
                return value
            except Exception:
                return value

        return str(value)

    def _format_tag_value(self, value: Any, field_def: FieldDefinition) -> str:
        """格式化 tag 类型的值为带颜色的 HTML 标签

        selections 格式: {"value": "label|color"} 或 {"value": "label"}
        例如: {"active": "激活|green", "inactive": "未激活|red", "pending": "待审|orange"}
        支持的颜色: red, green, blue, orange, purple, gray, cyan, pink, yellow 等
        """
        if value is None:
            return ""

        str_value = str(value)
        if not field_def.selections:
            return str_value

        selection = field_def.selections.get(str_value, str_value)

        # 解析 "label|color" 格式
        if "|" in selection:
            label, color = selection.rsplit("|", 1)
        else:
            label = selection
            color = "gray"  # 默认颜色

        css_class = self.TAG_COLOR_CLASSES.get(color.lower(), self.TAG_COLOR_CLASSES["gray"])
        return (
            f'<span class="px-2 py-1 rounded-full text-xs font-medium {css_class}">{label}</span>'
        )

    def _format_field_value(
        self, value: Any, field_def: FieldDefinition, truncate: bool = True
    ) -> str:
        """统一的字段值格式化方法

        Args:
            value: 字段原始值
            field_def: 字段定义
            truncate: 是否截断长文本（表格列需要截断，展开/详情不截断）

        Returns:
            格式化后的显示值
        """
        # Tag 类型：生成带颜色的标签 HTML，不截断
        if field_def.type == "tag" and field_def.selections:
            return self._format_tag_value(value, field_def)

        # JSON 类型：使用 json.dumps 确保双引号格式
        if field_def.type == "json":
            return self._format_json_value(value)

        # HTML 类型：不截断
        if field_def.type == "html":
            return str(value) if value is not None else ""

        # datetime 类型：格式化为指定格式
        if field_def.type == "datetime":
            return self._format_datetime_value(value, field_def)

        # Select 类型
        if field_def.input_type == "select" and field_def.selections:
            display_value = field_def.selections.get(
                str(value), str(value) if value is not None else ""
            )
        # Multiselect 类型
        elif field_def.input_type == "multiselect":
            if isinstance(value, list) and field_def.selections:
                display_labels = [field_def.selections.get(str(v), str(v)) for v in value]
                display_value = ", ".join(display_labels)
            elif isinstance(value, list):
                display_value = ", ".join(str(v) for v in value)
            else:
                display_value = str(value) if value is not None else ""
        # 其他类型
        else:
            display_value = str(value) if value is not None else ""

        # 根据需要截断
        if truncate and len(display_value) > self.MAX_DISPLAY_LENGTH:
            return display_value[: self.MAX_DISPLAY_LENGTH] + "..."
        return display_value

    def _generate_expand_content_html(self) -> str:
        """生成展开行内容的HTML"""
        if not self.expand_fields:
            return ""

        content_html = ""
        for field_def in self.expand_fields:
            field_name = field_def.name
            # 使用带 _expand 后缀的字段，显示完整值
            if field_def.type == "json":
                # JSON 类型使用 pre 标签，添加自动换行样式
                content_html += f'<div class="mb-2 break-all"><strong>{field_def.title}:</strong><pre class="mt-1 p-2 bg-gray-100 dark:bg-slate-700 rounded text-sm font-mono whitespace-pre-wrap break-all">{{{{ props.row.{field_name}_expand }}}}</pre></div>'
            elif field_def.type == "html":
                # HTML 类型直接渲染
                content_html += f'<div class="mb-2 break-all"><strong>{field_def.title}:</strong><div class="mt-1" v-html="props.row.{field_name}_expand"></div></div>'
            elif field_def.type == "tag":
                # Tag 类型使用 v-html 渲染带颜色的标签
                content_html += f'<div class="mb-2 break-all"><strong>{field_def.title}:</strong> <span v-html="props.row.{field_name}_expand"></span></div>'
            else:
                content_html += f'<div class="mb-2 break-all whitespace-pre-wrap"><strong>{field_def.title}:</strong> {{{{ props.row.{field_name}_expand }}}}</div>'

        return content_html

    def _has_any_actions(self) -> bool:
        """判断是否有任何操作按钮（详情按钮或自定义action）"""
        return self.config.show_detail_action or len(self.config.actions) > 0  # type: ignore

    async def render_table(self):
        """渲染表格"""
        await self.update_table_data()

        # 如果配置了可展开字段，在列的开头添加展开列
        if self.expand_fields:
            self.columns.insert(
                0,
                {
                    "name": "expand",
                    "label": "",
                    "field": "expand",
                    "align": "center",
                    "sortable": False,
                },
            )

        # 只有当有操作按钮时才添加操作列
        has_actions = self._has_any_actions()
        if has_actions:
            self.columns.append(
                {
                    "name": "actions",
                    "label": "操作",
                    "field": "actions",
                    "align": "center",
                }
            )

        self.table = (
            ui.table(
                columns=self.columns,
                rows=self.rows,
                row_key="obj_id",
                pagination=None,
            )
            .props(f"no-data-label='{self.config.no_data_label}'")
            .classes("w-full")
        )

        # 如果配置了可展开字段，添加展开行功能
        if self.expand_fields:
            expand_content_html = self._generate_expand_content_html()
            # 获取 HTML 和 tag 类型字段列表（需要使用 v-html 渲染）
            html_fields = [f.name for f in self.table_fields if f.type in ("html", "tag")]

            # 根据是否有 action 生成不同的模板
            if has_actions:
                action_buttons_html = self._generate_action_buttons_html()
                # 有操作列时，slice(1, -1) 排除展开列和操作列
                slot_template = f"""
                <q-tr :props="props" class="cursor-pointer">
                    <q-td auto-width>
                        <q-icon :name="props.expand ? 'unfold_less' : 'unfold_more'" 
                            class="cursor-pointer" size="md"
                            @click.stop="props.expand = !props.expand" />
                    </q-td>
                    <q-td v-for="col in props.cols.slice(1, -1)" :key="col.name" :props="props"
                        @click.stop="props.expand = !props.expand">
                        <span v-if="{html_fields}.includes(col.name)" v-html="col.value"></span>
                        <span v-else>{{{{ col.value }}}}</span>
                    </q-td>
                    <q-td key="actions" class="text-center">
                        <div class="flex items-center justify-center">
                            {action_buttons_html}
                        </div>
                    </q-td>
                </q-tr>
                <q-tr v-show="props.expand" :props="props">
                    <q-td colspan="100%">
                        <div class="text-left p-4 bg-blue-1 dark:bg-slate-800">
                            {expand_content_html}
                        </div>
                    </q-td>
                </q-tr>
                """
            else:
                # 无操作列时，slice(1) 只排除展开列
                slot_template = f"""
                <q-tr :props="props" class="cursor-pointer">
                    <q-td auto-width>
                        <q-icon :name="props.expand ? 'unfold_less' : 'unfold_more'" 
                            class="cursor-pointer" size="md"
                            @click.stop="props.expand = !props.expand" />
                    </q-td>
                    <q-td v-for="col in props.cols.slice(1)" :key="col.name" :props="props"
                        @click.stop="props.expand = !props.expand">
                        <span v-if="{html_fields}.includes(col.name)" v-html="col.value"></span>
                        <span v-else>{{{{ col.value }}}}</span>
                    </q-td>
                </q-tr>
                <q-tr v-show="props.expand" :props="props">
                    <q-td colspan="100%">
                        <div class="text-left p-4 bg-blue-1 dark:bg-slate-800">
                            {expand_content_html}
                        </div>
                    </q-td>
                </q-tr>
                """
            self.table.add_slot("body", slot_template)
        else:
            # 非展开模式
            if has_actions:
                action_buttons_html = self._generate_action_buttons_html()
                self.table.add_slot(
                    "body-cell-actions",
                    f"""
                    <q-td :props="props">
                        <div class="flex items-center justify-center">
                            {action_buttons_html}
                        </div>
                    </q-td>
                    """,
                )
            # 为 HTML 和 tag 类型字段添加单独的 slot
            for field_def in self.table_fields:
                if field_def.type in ("html", "tag"):
                    self.table.add_slot(
                        f"body-cell-{field_def.name}",
                        '<q-td :props="props"><span v-html="props.value"></span></q-td>',
                    )

        # 绑定详情事件（仅在启用时）
        if self.config.show_detail_action:  # type: ignore
            self.table.on("detail", self.handle_detail_click)

        # 绑定自定义action事件
        for i, action in enumerate(self.config.actions):
            event_name = f"action_{i}"
            self.table.on(
                event_name, lambda e, action=action: self._handle_custom_action(e, action)
            )

    async def update_table_data(self):
        """更新表格数据"""
        # 构建列定义
        self.columns = []
        for field_def in self.table_fields:
            self.columns.append(
                {
                    "name": field_def.name,
                    "label": field_def.title,
                    "field": field_def.name,
                    "sortable": True,
                    "align": "left",
                }
            )

        # 构建行数据
        self.rows = []
        for item in self.data:
            row = {}
            # 添加ID字段作为row_key
            if self.config.id_field:
                row["obj_id"] = item.get(self.config.id_field)

            # 格式化表格字段（需要截断）
            for field_def in self.table_fields:
                value = item.get(field_def.name)
                row[field_def.name] = self._format_field_value(value, field_def, truncate=True)

            # 添加可展开字段的值（用于展开行显示），不截断
            if self.expand_fields:
                for field_def in self.expand_fields:
                    value = item.get(field_def.name)
                    row[f"{field_def.name}_expand"] = self._format_field_value(
                        value, field_def, truncate=False
                    )

            self.rows.append(row)

    def _get_total_pages(self) -> int:
        """计算总页数"""
        return (self.total_count + self.page_size - 1) // self.page_size

    @ui.refreshable
    async def render_pagination(self):
        """渲染分页组件，使用 @ui.refreshable 支持动态刷新"""
        if self.total_count <= self.page_size:
            return

        with ui.row().classes("w-full items-center justify-center gap-4 mt-4"):
            await self._render_pagination_content()

    async def _render_pagination_content(self):
        """渲染分页组件的内容"""
        total_pages = self._get_total_pages()

        # 总数显示
        ui.label(f"共 {self.total_count} 条").classes("font-medium")

        # 每页条数选择
        page_size_options = {str(v): f"{v}条/页" for v in [10, 20, 30, 50, 100]}
        self.page_size_select = ui.select(
            options=page_size_options,
            value=str(self.page_size),
            on_change=self._handle_page_size_change,
        ).classes("w-28")

        # 上一页按钮
        prev_btn = ui.button(icon="chevron_left", on_click=self._handle_prev_page).props(
            "flat dense"
        )
        prev_btn.enabled = self.current_page > 1

        # 页码显示和跳转
        with ui.row().classes("items-center gap-2"):
            # 页码按钮显示
            start_page = max(1, self.current_page - 1)
            end_page = min(total_pages, self.current_page + 1)

            if start_page > 1:
                ui.button("1", on_click=lambda: self.handle_goto_page(1)).props(
                    "flat" if self.current_page != 1 else ""
                ).props("color=primary" if self.current_page == 1 else "")

                if start_page > 2:
                    ui.label("...")

            for page_num in range(start_page, end_page + 1):
                if page_num <= total_pages:
                    btn = ui.button(
                        str(page_num), on_click=lambda p=page_num: self.handle_goto_page(p)
                    )
                    if self.current_page == page_num:
                        btn.props("color=primary")
                    else:
                        btn.props("flat")

            if end_page < total_pages:
                if end_page < total_pages - 1:
                    ui.label("...")
                ui.button(
                    str(total_pages), on_click=lambda: self.handle_goto_page(total_pages)
                ).props("flat" if self.current_page != total_pages else "color=primary")

        # 下一页按钮
        next_btn = ui.button(icon="chevron_right", on_click=self._handle_next_page).props(
            "flat dense"
        )
        next_btn.enabled = self.current_page < total_pages

        # 前往页码
        ui.label("前往")
        self.goto_page_input = ui.number(
            value=self.current_page,
            min=1,
            max=total_pages,
        ).classes("w-20")
        # 绑定 blur 事件和回车键事件
        self.goto_page_input.on("blur", lambda: self._handle_goto_page_input_blur())
        self.goto_page_input.on("keydown.enter", lambda: self._handle_goto_page_input_blur())
        ui.label("页")

    async def handle_page_size_change(self, e):
        """处理每页条数变化"""
        self.page_size = int(e.value)
        self.current_page = 1
        await self.handle_query(self.current_query, 1)

    def _handle_page_size_change(self, e):
        """同步包装：处理每页条数变化"""
        asyncio.create_task(self.handle_page_size_change(e))

    async def handle_prev_page(self):
        """处理上一页"""
        if self.current_page > 1:
            await self.handle_goto_page(self.current_page - 1)

    def _handle_prev_page(self):
        """同步包装：处理上一页"""
        asyncio.create_task(self.handle_prev_page())

    async def handle_next_page(self):
        """处理下一页"""
        total_pages = self._get_total_pages()
        if self.current_page < total_pages:
            await self.handle_goto_page(self.current_page + 1)

    def _handle_next_page(self):
        """同步包装：处理下一页"""
        asyncio.create_task(self.handle_next_page())

    async def handle_goto_page(self, page: int):
        """处理跳转到指定页"""
        total_pages = self._get_total_pages()
        if 1 <= page <= total_pages:
            await self.handle_query(self.current_query, page)

    async def handle_goto_page_input_change(self, value):
        """处理前往页码输入框变化"""
        if value is not None and value > 0:
            await self.handle_goto_page(int(value))

    def _handle_goto_page_input_blur(self):
        """处理前往页码输入框失焦事件"""
        if self.goto_page_input and self.goto_page_input.value:
            asyncio.create_task(self.handle_goto_page(int(self.goto_page_input.value)))

    async def handle_query_click(self):
        """处理查询按钮点击"""
        await self.handle_query(self.query_values, 1)

    async def handle_reset_click(self):
        """处理重置按钮点击"""
        self.query_values = {}
        # 重新渲染查询组件以清空日期范围选择器
        if self.query_section:
            self.query_section.clear()
            with self.query_section:
                await self._build_query_content()
        await self.handle_query({}, 1)

    async def handle_query(self, query_values: dict, page: int = 1):
        """处理查询"""
        self.current_query = query_values
        self.current_page = page

        try:
            page_data = await self.query(query_values, page, self.page_size)
            self.data = page_data.data
            self.total_count = page_data.total
            await self.update_table_data()

            # 更新表格
            if hasattr(self, "table"):
                self.table.rows = self.rows
                self.table.update()

            # 刷新分页栏
            if hasattr(self, "render_pagination"):
                self.render_pagination.refresh()

        except Exception as e:
            log.error(f"Query failed: {e}")

    async def handle_detail_click(self, e: events.GenericEventArguments) -> None:
        """处理查看详情按钮点击

        Args:
            e: Event argument with the row information passed from javascript
        """
        obj_id: str = e.args.get("obj_id") or e.args.get(self.config.id_field)
        log.debug(f"view detail with {obj_id=}")
        model = await self.detail(obj_id)
        if model is None:
            log.error(f"Error, could not find {obj_id=}")
            ui.notify("无法获取详情数据", color="negative")
            return
        try:
            await self.show_detail_dialog(model)
        except Exception as ex:
            ui.notify(
                f"Error viewing details: {str(ex)}",
                color="negative",
            )
            log.error(ex)

    def _handle_custom_action(self, e: events.GenericEventArguments, action: ActionConfig) -> None:
        """处理自定义action点击事件"""
        try:
            # 获取行数据
            row_data = e.args

            # 如果传入的是函数名字符串，从当前实例获取方法
            if isinstance(action.call, str):
                method = getattr(self, action.call, None)
                if method is None:
                    log.error(f"Method '{action.call}' not found in {self.__class__.__name__}")
                    ui.notify(f"方法 '{action.call}' 未找到", color="negative")
                    return
                if not callable(method):
                    log.error(f"'{action.call}' is not callable")
                    ui.notify(f"'{action.call}' 不是可调用方法", color="negative")
                    return
                call_func = method
            else:
                # 直接使用传入的函数
                call_func = action.call

            # 调用函数，传入行数据
            if callable(call_func):
                call_func(row_data)
            else:
                log.error(f"Action call is not callable: {action.call}")
                ui.notify("无效的action调用", color="negative")

        except Exception as ex:
            log.error(f"Error handling custom action: {ex}")
            ui.notify(f"执行自定义操作时出错: {str(ex)}", color="negative")

    async def show_detail_dialog(self, item: Dict[str, Any]):
        """显示详情对话框"""
        detail_heading = self.config.detail_dialog_heading  # type: ignore
        title = detail_heading or f"{self.config.heading}详情"

        with ui.dialog().props("full-width") as self.detail_dialog:
            with ui.card().classes("w-full"):
                # 标题栏
                with ui.card_section().classes("pb-2"):
                    ui.label(title).classes(self.config.class_heading)

                # 详情内容区域
                with ui.card_section().classes("overflow-auto w-full"):
                    grid_class = "w-full items-center gap-x-10"
                    columns = "minmax(120px,max-content) 1fr"

                    with ui.grid(columns=columns).classes(grid_class):
                        for field_def in self.detail_fields:
                            # 标签
                            with ui.label(field_def.title + ":"):
                                if field_def.description:
                                    with ui.tooltip():
                                        ui.html(field_def.description, sanitize=False)

                            # 值
                            value = item.get(field_def.name, "")

                            # 格式化显示值
                            if field_def.type == "json":
                                # JSON 类型使用 code 组件格式化显示
                                display_value = self._format_json_value(value)
                                ui.code(display_value, language="json").classes(
                                    "w-full max-h-64 overflow-auto"
                                )
                            elif field_def.type == "html":
                                # HTML 类型直接渲染
                                display_value = str(value) if value is not None else ""
                                ui.html(display_value, sanitize=False).classes("w-full")
                            elif field_def.type == "tag" and field_def.selections:
                                # Tag 类型渲染带颜色的标签
                                display_value = self._format_tag_value(value, field_def)
                                ui.html(display_value, sanitize=False)
                            elif field_def.type == "datetime":
                                # datetime 类型格式化显示
                                display_value = self._format_datetime_value(value, field_def)
                                ui.label(display_value).classes("break-words")
                            elif field_def.input_type == "select" and field_def.selections:
                                display_value = field_def.selections.get(str(value), str(value))
                                ui.label(display_value).classes("break-words")
                            elif field_def.input_type == "multiselect":
                                if isinstance(value, list) and field_def.selections:
                                    display_labels = [
                                        field_def.selections.get(str(v), str(v)) for v in value
                                    ]
                                    display_value = ", ".join(display_labels)
                                elif isinstance(value, list):
                                    display_value = ", ".join(str(v) for v in value)
                                else:
                                    display_value = str(value) if value else ""
                                ui.label(display_value).classes("break-words")
                            else:
                                display_value = str(value) if value is not None else ""
                                ui.label(display_value).classes("break-words")

                # 按钮区域
                with ui.card_actions().classes("justify-end w-full"):
                    ui.button("关闭", on_click=self.detail_dialog.close).props(
                        "outline color=secondary"
                    )

        self.detail_dialog.open()

    async def detail(self, item_id: str):
        """获取项目详情，子类应重写此方法"""
        for item in self.data:
            if str(item.get(self.config.id_field)) == str(item_id):
                return item

    # 以下方法需要子类重写
    async def query(self, query_values: dict, page: int = 1, page_size: int = 20) -> PageData:
        """查询数据，子类必须重写此方法"""
        # 默认返回空数据，子类应重写此方法实现具体的数据加载逻辑
        return PageData(data=[], total=0)
