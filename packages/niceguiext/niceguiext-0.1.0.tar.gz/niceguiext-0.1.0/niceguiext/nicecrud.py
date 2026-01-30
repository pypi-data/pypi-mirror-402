# pyright: reportArgumentType=false
# pyright: reportIncompatibleMethodOverride=false
"""
NiceCRUD - 基于 NiceTable 的 CRUD 组件

继承 NiceTable 的表格展示和查询能力，添加增删改功能
"""

import logging
from functools import partial
from typing import Awaitable, Callable, Literal, Optional, Union, Any, Dict, List

from nicegui import events, ui
from pydantic import Field

from .show_error import show_error
from .nicetable import (
    NiceTable,
    NiceTableConfig,
    FieldDefinition,
    PageData,
    ActionConfig,
    FieldHelperMixin,
)

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

__all__ = [
    "NiceCRUD",
    "NiceCRUDCard",
    "NiceCRUDConfig",
    "FieldDefinition",
    "PageData",
    "ActionConfig",
    "FieldHelperMixin",
]


class NiceCRUDConfig(NiceTableConfig):
    """NiceCRUD 配置类，继承自 NiceTableConfig"""

    add_button_text: str = "新增"
    delete_button_text: str = "删除选中"
    new_item_dialog_heading: Optional[str] = None
    update_item_dialog_heading: Optional[str] = None
    additional_exclude: List[str] = Field(default_factory=list)

    # 覆盖父类的默认值
    show_detail_action: bool = Field(default=False, description="CRUD模式默认不显示详情按钮")

    # 表格显示类型
    table_type: Literal["table", "grid"] = Field(default="table")

    # Grid 模式样式
    class_card_selected: str = Field(default="dark:bg-slate-800 bg-slate-100")
    column_count: Optional[int] = Field(default=None)


class NiceCRUDCard(FieldHelperMixin):
    """动态字段的单个卡片组件，用于编辑表单"""

    def __init__(
        self,
        item: Dict[str, Any],
        fields: List[FieldDefinition],
        select_options: Optional[Callable[[str, Dict[str, Any]], Awaitable[dict]]] = None,
        config: NiceCRUDConfig = NiceCRUDConfig(),
        id_editable: bool = True,
        on_change_extra: Optional[Callable[[str, Dict[str, Any]], None]] = None,
        on_validation_result: Callable[[bool], None] = lambda _: None,
        **kwargs,
    ):
        self.item = item
        self.fields = fields
        self.config = config
        self.config.update(kwargs)
        self.id_editable = id_editable
        self.errormsg = dict(msg="", visible=False)

        if select_options is not None:
            self.select_options = select_options
        else:

            async def default_select_options(field_name: str, obj: Dict[str, Any]):
                return dict()

            self.select_options = default_select_options

        self.on_change_extra = on_change_extra
        self.on_validation_result = on_validation_result

        super().__init__()
        ui.timer(0, self.create_card, once=True)

    def onchange(self, value, attr: str = "", refresh: bool = False):
        """字段值变化时的处理"""
        if hasattr(value, "value"):
            value = value.value

        log.debug(f"{attr=} {value=} {type(value)=}")

        try:
            self.errormsg["msg"] = ""
            self.errormsg["visible"] = False

            # 根据字段类型转换值
            field_def = self.get_field_by_name(attr)
            if field_def:
                value = self._convert_value(value, field_def)

            self.item[attr] = value
            val_result = True

        except (ValueError, TypeError) as e:
            self.errormsg["msg"] = str(e)
            self.errormsg["visible"] = True
            val_result = False

        if self.on_change_extra is not None:
            self.on_change_extra(attr, self.item)

        self.on_validation_result(val_result)

        if refresh:
            self.create_card.refresh()

    def _convert_value(self, value, field_def: FieldDefinition):
        """根据字段类型转换值"""
        if value is None:
            return None

        # multiselect字段应该保持为列表
        if field_def.input_type == "multiselect":
            return value if isinstance(value, list) else []

        if field_def.type == "integer":
            return int(value) if value != "" else None
        elif field_def.type == "number":
            return float(value) if value != "" else None
        elif field_def.type == "boolean":
            return bool(value)
        elif field_def.type == "text":
            return str(value)
        else:
            return value

    def _build_validation(self, field_def: FieldDefinition):
        """构建字段验证规则"""
        validations = []

        # 必填验证
        if field_def.required:
            validations.append(
                lambda value: "此字段为必填项" if not value or str(value).strip() == "" else None
            )

        # 最大长度验证
        if field_def.max_length is not None:
            max_len = field_def.max_length
            validations.append(
                lambda value: f"最大长度为{max_len}字符" if len(str(value)) > max_len else None
            )

        # 数字范围验证
        if field_def.type in ("integer", "number"):
            if field_def.min_value is not None:
                min_val = field_def.min_value
                validations.append(
                    lambda value: f"值不能小于{min_val}"
                    if value is not None and float(value) < min_val
                    else None
                )
            if field_def.max_value is not None:
                max_val = field_def.max_value
                validations.append(
                    lambda value: f"值不能大于{max_val}"
                    if value is not None and float(value) > max_val
                    else None
                )

        # 自定义验证
        if field_def.validation is not None:
            if callable(field_def.validation):
                validations.append(field_def.validation)
            elif isinstance(field_def.validation, dict):
                # 字典形式的验证规则
                for error_msg, validation_func in field_def.validation.items():
                    validations.append(
                        lambda value, msg=error_msg, func=validation_func: msg
                        if not func(value)
                        else None
                    )

        # 如果没有验证规则，返回None
        if not validations:
            return None

        # 组合多个验证规则
        def combined_validation(value):
            for validation_func in validations:
                try:
                    error = validation_func(value)
                    if error:
                        return error
                except Exception as e:
                    log.warning(f"Validation error: {e}")
                    return f"验证失败: {str(e)}"
            return None

        return combined_validation

    @property
    def column_count(self):
        return getattr(self.config, "column_count", None) or max(
            (int(len(self.included_fields) / 4), 1)
        )

    @ui.refreshable
    async def create_card(self):
        """创建卡片UI"""
        grid_class = "w-full items-center gap-x-10"
        columns = "minmax(80px,max-content) 1fr " * self.column_count

        with ui.grid(columns=columns).classes(grid_class):
            for field_def in self.included_fields:
                if field_def.name == self.config.id_field and not self.id_editable:
                    continue
                await self.get_input(field_def)

        errlabel, errrow = show_error("")
        errlabel.bind_text_from(self.errormsg, "msg")
        errrow.bind_visibility_from(self.errormsg, "visible").classes("w-full")

    async def get_input(self, field_def: FieldDefinition):
        """根据字段定义创建输入组件"""
        field_name = field_def.name
        curval = self.item.get(field_name, field_def.default)
        validation = partial(self.onchange, attr=field_name)

        # 确保初始值被设置到 item 中
        if field_name not in self.item:
            self.item[field_name] = curval

        # 标签
        with ui.label(field_def.title + ":"):
            if field_def.description:
                with ui.tooltip():
                    ui.html(field_def.description, sanitize=False)

        # 只读字段
        if field_def.readonly:
            ui.label(str(curval))
            return

        # 选择类型
        if field_def.input_type in ("select", "multiselect"):
            await self._create_select_input(field_def, curval, validation)

        # 数字类型
        elif field_def.type in ("integer", "number"):
            await self._create_number_input(field_def, curval, validation)

        # 布尔类型
        elif field_def.type == "boolean":
            # 确保初始值被设置到 item 中
            self.item[field_name] = curval
            ui.checkbox("", value=curval, on_change=validation)

        # 日期类型
        elif field_def.type == "date":
            date_value = str(curval) if curval else None
            # 确保初始值被设置到 item 中
            self.item[field_name] = date_value

            ui.date_input(
                value=date_value,
                on_change=validation,
            ).classes("w-full")

        # 时间类型
        elif field_def.type == "datetime":
            datetime_value = str(curval) if curval else ""
            # 确保初始值被设置到 item 中
            self.item[field_name] = datetime_value

            # 构建验证规则
            input_validation = self._build_validation(field_def)

            with ui.input(value=datetime_value, validation=input_validation).classes(
                "w-full"
            ) as datetime_input:
                with datetime_input.add_slot("append"):
                    ui.icon("schedule").on("click", lambda: ui.time().bind_value(datetime_input))
                datetime_input.on("change", validation)

        # 默认文本类型
        else:
            await self._create_text_input(field_def, curval, validation)

    async def _create_select_input(self, field_def: FieldDefinition, curval, validation):
        """创建选择输入组件"""
        if field_def.selections:
            select_options_dict = field_def.selections
        else:
            select_options_dict = await self.select_options(field_def.name, self.item)

        if field_def.input_type == "multiselect":
            # 多选
            if isinstance(curval, list):
                selected_keys = curval
            else:
                # 如果curval是字符串，尝试解析为列表
                if isinstance(curval, str) and curval.startswith("[") and curval.endswith("]"):
                    try:
                        import ast

                        selected_keys = ast.literal_eval(curval)
                    except (ValueError, SyntaxError):
                        selected_keys = []
                else:
                    selected_keys = [] if curval is None else [curval]

            # 确保初始值被设置到 item 中
            self.item[field_def.name] = selected_keys

            log.debug(
                f"multiselect {field_def.name}: curval={curval}, selected_keys={selected_keys}, options={select_options_dict}"
            )

            ui.select(
                options=select_options_dict,
                multiple=True,
                value=selected_keys,
                on_change=validation,
            ).classes("w-full")
        else:
            # 单选
            if curval not in select_options_dict and len(select_options_dict) > 0:
                curval = next(iter(select_options_dict.keys()))

            # 确保初始值被设置到 item 中
            self.item[field_def.name] = curval

            ui.select(options=select_options_dict, value=curval, on_change=validation).classes(
                "w-full"
            )

    async def _create_number_input(self, field_def: FieldDefinition, curval, validation):
        """创建数字输入组件"""
        if field_def.input_type == "slider":
            slider_value = curval or field_def.default or 0
            # 确保初始值被设置到 item 中
            self.item[field_def.name] = slider_value

            ui.slider(
                min=field_def.min_value or 0,
                max=field_def.max_value or 100,
                step=field_def.step or 1,
                value=slider_value,
                on_change=validation,
            ).classes("w-full")
        else:
            # 确保初始值被设置到 item 中
            self.item[field_def.name] = curval

            # 构建验证规则
            input_validation = self._build_validation(field_def)

            ui.number(
                value=curval,
                min=field_def.min_value,
                max=field_def.max_value,
                step=field_def.step,
                on_change=validation,
                validation=input_validation,
            ).classes("w-full")

    async def _create_text_input(self, field_def: FieldDefinition, curval, validation):
        """创建文本输入组件"""
        text_value = str(curval) if curval is not None else ""
        # 确保初始值被设置到 item 中
        self.item[field_def.name] = text_value

        # 构建验证规则
        input_validation = self._build_validation(field_def)

        ui.input(
            value=text_value,
            on_change=validation,
            placeholder=field_def.description or f"请输入{field_def.title}",
            validation=input_validation,
        ).classes("w-full")


class NiceCRUD(NiceTable):
    """基于 NiceTable 的 CRUD 组件，继承表格展示和查询能力"""

    def __init__(
        self,
        fields: List[FieldDefinition],
        data: Optional[List[Dict[str, Any]]] = None,
        id_field: Optional[str] = None,
        config: Union[NiceCRUDConfig, dict] = NiceCRUDConfig(),
        **kwargs,
    ):
        # 转换配置类型
        if isinstance(config, dict):
            crud_config = NiceCRUDConfig(**config, **kwargs)
        else:
            crud_config = config
            crud_config.update(kwargs)

        # 存储本地数据（用于默认的 CRUD 操作）
        self._local_data = data or []

        # 调用父类初始化（不传 data，由 query 方法提供数据）
        super().__init__(
            fields=fields,
            id_field=id_field,
            config=crud_config,
        )

        # CRUD 相关的 UI 组件引用
        self.item_dialog: ui.dialog
        self.button_row: ui.row

    @property
    def crud_config(self) -> NiceCRUDConfig:
        """获取 CRUD 配置（类型安全的访问方式）"""
        return self.config  # type: ignore

    def _generate_action_buttons_html(self) -> str:
        """生成操作按钮的HTML，覆盖父类方法添加编辑和删除按钮"""
        buttons_html = '''
        <q-btn size="md" color="primary" dense flat label="编辑"
            @click="() => $parent.$emit('edit', props.row)" class="mr-1" />
        <q-btn size="md" color="negative" dense flat label="删除"
            @click="() => $parent.$emit('delete', props.row)"'''

        # 如果有自定义actions，添加间距
        if self.config.actions:
            buttons_html += ' class="mr-1"'

        buttons_html += " />"

        # 添加自定义action按钮
        for i, action in enumerate(self.config.actions):
            event_name = f"action_{i}"
            icon_html = f' icon="{action.icon}"' if action.icon else ""
            tooltip_html = f' title="{action.tooltip}"' if action.tooltip else ""

            buttons_html += f'''
        <q-btn size="md" color="{action.color}" dense flat label="{action.label}"{icon_html}{tooltip_html}
            @click="() => $parent.$emit('{event_name}', props.row)" class="mr-1" />'''

        return buttons_html

    def _generate_grid_action_buttons_html(self) -> str:
        """生成grid模式操作按钮的HTML"""
        buttons_html = """
                        <q-btn class="mr-2 mt-2 z-10" size="md" color="negative" dense flat label="删除"
                            @click="() => $parent.$emit('delete', props.row)"
                        />
                        <q-btn class="mr-2 mt-2 z-10" size="md" color="primary" dense flat label="编辑"
                            @click="() => $parent.$emit('edit', props.row)"
                        />"""

        # 添加自定义action按钮
        for i, action in enumerate(self.config.actions):
            event_name = f"action_{i}"
            icon_html = f' icon="{action.icon}"' if action.icon else ""
            tooltip_html = f' title="{action.tooltip}"' if action.tooltip else ""

            buttons_html += f'''
                        <q-btn class="mr-2 mt-2 z-10" size="md" color="{action.color}" dense flat label="{action.label}"{icon_html}{tooltip_html}
                            @click="() => $parent.$emit('{event_name}', props.row)"
                        />'''

        return buttons_html

    def _has_any_actions(self) -> bool:
        """CRUD 模式始终有操作按钮（编辑/删除）"""
        return True

    async def render_components(self):
        """渲染所有组件，覆盖父类方法添加按钮行"""
        await self.collect_field_selections()
        await self.render_heading()
        await self.render_query_section()
        await self.render_button_row()
        # 初始化加载第一页数据
        page_data = await self.query({}, 1, self.page_size)
        self.data = page_data.data
        self.total_count = page_data.total
        await self.render_table()
        await self.render_pagination()

    async def render_heading(self):
        """渲染标题 - CRUD 模式不单独渲染标题，由 button_row 统一处理"""
        pass

    async def render_button_row(self):
        """渲染按钮行"""
        with ui.row().classes("w-full justify-between items-center") as self.button_row:
            ui.label(self.config.heading).classes(self.config.class_heading)

            with ui.row():
                ui.button(self.crud_config.add_button_text, on_click=self.handle_add_click).props(
                    "color=primary"
                )

                ui.button(
                    self.crud_config.delete_button_text, on_click=self.handle_delete_selected_click
                ).props("color=negative")

    async def render_table(self):
        """渲染表格，覆盖父类方法支持 grid 模式"""
        if self.crud_config.table_type == "grid":
            await self._render_grid_table()
        else:
            await super().render_table()
            # 绑定 CRUD 特有的事件
            self.table.on("delete", self.handle_delete_click)
            self.table.on("edit", self.handle_update_click)

    async def _render_grid_table(self):
        """渲染 grid 模式的表格"""
        await self.update_table_data()

        self.table = (
            ui.table(
                columns=self.columns,
                rows=self.rows,
                row_key="obj_id",
                selection="multiple",
            )
            .props(f"no-data-label='{self.config.no_data_label}' grid")
            .classes("w-full")
        )

        grid_action_buttons_html = self._generate_grid_action_buttons_html()
        # 获取 tag 类型字段名列表
        tag_fields = [f.name for f in self.table_fields if f.type == "tag"]
        self.table.add_slot(
            "item",
            f"""<q-card bordered flat :class=" """
            f"props.selected ?  '{self.crud_config.class_card_selected}' : '{self.config.class_card}'"
            f""" "
                class="sm:w-[calc(50%-20px)] w-full m-2 relative">
                <div class="absolute top-0 right-0 z-10">
                    {grid_action_buttons_html}
                </div>
                <q-card-section class="z-1 """
            + self.config.class_card_header
            + """ ">
                <q-checkbox dense v-model="props.selected">
                    <span v-html="props.row.obj_id"></span>
                </q-checkbox>
                </q-card-section>
                <q-card-section>
                    <div class="flex flex-row p-0 m-1 w-full gap-y-1">
                    <div class="p-2 border-l-2" v-for="col in props.cols.filter(col => col.name !== 'obj_id')" :key="col.obj_id" >
                        <q-item-label caption class="text-[#444444] dark:text-[#BBBBBB]">{{ col.label }}</q-item-label>
                        <q-item-label v-if=\""""
            + str(tag_fields)
            + """.includes(col.name)\" v-html="col.value"></q-item-label>
                        <q-item-label v-else>{{ col.value }}</q-item-label>
                    </div>
                    </div>
                </q-card-section>
            </q-card>
            """,
        )

        self.table.on("delete", self.handle_delete_click)
        self.table.on("edit", self.handle_update_click)

        # 绑定自定义action事件
        for i, action in enumerate(self.config.actions):
            event_name = f"action_{i}"
            self.table.on(
                event_name, lambda e, action=action: self._handle_custom_action(e, action)
            )

    async def handle_add_click(self):
        """处理添加按钮点击"""
        # 创建新项目，使用字段默认值
        new_item = {}
        for field_def in self.fields:
            new_item[field_def.name] = field_def.default

        await self.show_item_dialog(new_item, is_new=True)

    async def handle_delete_selected_click(self):
        """处理删除选中项按钮点击"""
        if not hasattr(self, "table") or not self.table.selected:
            ui.notify("请选择要删除的项目", color="warning")
            return

        selected_items = self.table.selected.copy()  # 复制选中项列表
        deleted_count = 0
        failed_count = 0

        for item in selected_items:
            # 从选中的行数据中获取ID
            item_id = item.get("obj_id") or item.get(self.config.id_field)
            if item_id is not None:
                try:
                    await self.delete(str(item_id))
                    deleted_count += 1
                except (KeyError, ValueError) as e:
                    log.warning(f"Failed to delete item {item_id}: {e}")
                    failed_count += 1

        # 清空选中状态
        self.table.selected = []

        # 显示操作结果
        if deleted_count > 0:
            ui.notify(f"成功删除 {deleted_count} 个项目", color="positive")
        if failed_count > 0:
            ui.notify(f"删除失败 {failed_count} 个项目", color="negative")

        await self.refresh_data()

    async def handle_delete_click(self, e: events.GenericEventArguments) -> None:
        """处理单行删除按钮点击"""
        obj_id: str = e.args.get("obj_id") or e.args.get(self.config.id_field)
        log.debug(f"delete row with {obj_id=}")
        try:
            await self.delete(obj_id)
        except KeyError as er:
            log.error(f"Deletion operation failed for object with id: {obj_id} {str(er)}")
            ui.notify(f"Error deleting: {str(er)}", color="negative")
        else:
            ui.notify(f"Deleted {obj_id}")
        finally:
            await self.refresh_data()

    async def handle_update_click(self, e: events.GenericEventArguments) -> None:
        """处理编辑按钮点击"""
        obj_id: str = e.args.get("obj_id") or e.args.get(self.config.id_field)
        log.debug(f"edit row with {obj_id=}")
        model = await self.detail(obj_id)
        if model is None:
            log.error(f"Error, could not find {obj_id=}")
            return
        try:
            await self.show_item_dialog(model)
        except NotImplementedError as er:
            ui.notify(
                f"Error editing: {str(er)}",
                color="negative",
            )
            log.error(er)
        finally:
            await self.refresh_data()

    @property
    def column_count(self):
        """计算表单列数"""
        return getattr(self.crud_config, "column_count", None) or max(
            (int(len(self.included_fields) / 4), 1)
        )

    async def show_item_dialog(self, item: Dict[str, Any], is_new: bool = False):
        """显示项目编辑对话框"""
        title = (
            self.crud_config.new_item_dialog_heading
            if is_new
            else self.crud_config.update_item_dialog_heading
        ) or (f"添加{self.config.heading}" if is_new else f"编辑{self.config.heading}")

        if self.column_count > 1:
            props = "full-width"
        else:
            props = ""
        with ui.dialog().props(props) as self.item_dialog:
            with ui.card().classes("w-full"):
                # 标题栏
                with ui.card_section().classes("pb-2"):
                    ui.label(title).classes("text-lg font-bold")

                # 表单内容区域
                with ui.card_section().classes("overflow-auto w-full"):
                    # 创建表单卡片
                    card = NiceCRUDCard(
                        item=item,
                        fields=self.fields,
                        select_options=self.select_options,
                        config=self.crud_config,
                        id_editable=is_new,
                    )

                # 按钮区域 - 放在底部
                with ui.card_actions().classes("justify-end w-full"):
                    ui.button("取消", on_click=self.item_dialog.close).props(
                        "outline color=secondary"
                    )
                    ui.button(
                        "保存", on_click=lambda: self.handle_save_click(card.item, is_new)
                    ).props("color=primary")

        self.item_dialog.open()

    async def handle_save_click(self, item: Dict[str, Any], is_new: bool):
        """处理保存按钮点击"""
        try:
            if is_new:
                await self.create(item)
            else:
                await self.update(item)

            self.item_dialog.close()
            await self.refresh_data()

        except Exception as e:
            log.error(f"Save failed: {e}")
            ui.notify(f"保存失败: {str(e)}", color="negative")

    async def refresh_data(self):
        """刷新数据"""
        await self.handle_query(self.current_query, self.current_page)

    # CRUD 操作方法 - 默认实现基于本地数据
    async def query(self, query_values: dict, page: int = 1, page_size: int = 20) -> PageData:
        """查询数据，子类应重写此方法"""
        # 默认实现：简单过滤本地数据
        filtered_data = self._local_data.copy()

        for field_name, value in query_values.items():
            if value is None or value == "":
                continue

            # 处理日期范围查询
            if field_name.endswith("_min"):
                # 最小值查询
                original_field = field_name[:-4]  # 移除 '_min' 后缀
                filtered_data = [
                    item
                    for item in filtered_data
                    if item.get(original_field) is not None
                    and str(item.get(original_field)) >= str(value)
                ]
            elif field_name.endswith("_max"):
                # 最大值查询
                original_field = field_name[:-4]  # 移除 '_max' 后缀
                filtered_data = [
                    item
                    for item in filtered_data
                    if item.get(original_field) is not None
                    and str(item.get(original_field)) <= str(value)
                ]
            else:
                # 普通字符串匹配查询
                filtered_data = [
                    item
                    for item in filtered_data
                    if str(item.get(field_name, "")).lower().find(str(value).lower()) >= 0
                ]

        # 分页
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_data = filtered_data[start_idx:end_idx]

        return PageData(data=page_data, total=len(filtered_data))

    async def detail(self, item_id: str):
        """获取项目详情，子类应重写此方法"""
        # 优先从当前页数据查找
        for item in self.data:
            if str(item.get(self.config.id_field)) == str(item_id):
                return item
        # 再从本地数据查找
        for item in self._local_data:
            if str(item.get(self.config.id_field)) == str(item_id):
                return item
        return None

    async def create(self, item: Dict[str, Any]):
        """创建新项目，子类应重写此方法"""
        # 生成ID（如果需要）
        if self.config.id_field and not item.get(self.config.id_field):
            max_id = 0
            for existing_item in self._local_data:
                existing_id = existing_item.get(self.config.id_field)
                if isinstance(existing_id, int):
                    max_id = max(max_id, existing_id)
            item[self.config.id_field] = max_id + 1

        self._local_data.append(item)

    async def update(self, item: Dict[str, Any]):
        """更新项目，子类应重写此方法"""
        if not self.config.id_field:
            raise ValueError("id_field is required for update operation")

        item_id = item.get(self.config.id_field)
        for i, existing_item in enumerate(self._local_data):
            if existing_item.get(self.config.id_field) == item_id:
                self._local_data[i] = item
                break
        else:
            raise KeyError(f"Item with {self.config.id_field}={item_id} not found")

    async def delete(self, item_id: str):
        """删除项目，子类应重写此方法"""
        if not self.config.id_field:
            raise ValueError("id_field is required for delete operation")

        for i, existing_item in enumerate(self._local_data):
            if str(existing_item.get(self.config.id_field)) == str(item_id):
                del self._local_data[i]
                break
        else:
            raise KeyError(f"Item with {self.config.id_field}={item_id} not found")
