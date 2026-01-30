# pyright: reportArgumentType=false
import logging
import typing
from datetime import date, datetime, time
from functools import partial
from pathlib import Path
from types import UnionType
from typing import Any, Awaitable, Callable, Literal, Optional, Union
from dataclasses import dataclass

from nicegui import ui
from pydantic import BaseModel

from .show_error import show_error

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


@dataclass
class FieldDefinition:
    """字段定义类"""

    name: str
    field_type: Any
    default: Any = None
    title: Optional[str] = None
    description: Optional[str] = None
    required: bool = True
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    step: Optional[float] = None
    input_type: Optional[str] = None  # "select", "multiselect", "slider", "number", etc.
    readonly: bool = False
    selections: Optional[dict] = None  # 用于 select/multiselect 的选项
    exclude: bool = False

    @property
    def is_optional(self) -> bool:
        """判断字段是否可选"""
        if not self.required:
            return True

        # 检查类型是否为 Union[T, None] 或 Optional[T]
        if typing.get_origin(self.field_type) in {Union, UnionType}:
            args = typing.get_args(self.field_type)
            if len(args) > 1 and type(None) in args:
                return True
        return False

    @property
    def actual_type(self) -> type:
        """获取实际类型（排除 Optional）"""
        if typing.get_origin(self.field_type) in {Union, UnionType}:
            args = typing.get_args(self.field_type)
            if len(args) > 1 and type(None) in args:
                # 返回非 None 的类型
                return next(arg for arg in args if arg is not type(None))
        return self.field_type


class FormConfig(BaseModel):
    """表单配置类"""

    title: Optional[str] = None
    submit_button_text: str = "提交"
    reset_button_text: str = "重置"
    class_heading: str = "text-xl font-bold"
    class_form_card: str = "w-full p-4"
    column_count: Optional[int] = None
    show_validation_errors: bool = True

    def update(self, data: dict):
        for k, v in data.items():
            setattr(self, k, v)


class NiceForm:
    """基于字段定义列表的表单组件

    支持多种输入类型（文本、数字、选择框等），具备数据验证逻辑，
    有 on_submit 参数来传递回调函数。

    Attributes:
        fields: 字段定义列表
        config: FormConfig 表单配置
        on_submit: 提交回调函数
        on_change: 字段变化回调函数
        select_options: 获取选择选项的异步函数
    """

    def __init__(
        self,
        fields: list[FieldDefinition],
        config: FormConfig = FormConfig(),
        on_submit: Optional[Callable[[dict[str, Any]], Awaitable[None]]] = None,
        on_change: Optional[Callable[[str, dict[str, Any]], None]] = None,
        select_options: Optional[Callable[[str, dict[str, Any]], Awaitable[dict]]] = None,
        **kwargs,
    ):
        self.fields = fields
        self.config = config
        self.config.update(kwargs)
        self.on_submit = on_submit
        self.on_change = on_change
        self.errormsg = dict(msg="", visible=False)
        self.validation_results = {}  # 存储每个字段的验证结果
        self.form_valid = True  # 整个表单的验证状态

        # 初始化表单数据
        self.form_data = {}
        for field in self.fields:
            if not field.exclude:
                self.form_data[field.name] = field.default

        # 设置选择选项获取函数
        if select_options is not None:
            self.select_options = select_options
        else:

            async def default_select_options(field_name: str, data: dict[str, Any]):
                log.debug(f"default_select_options: {field_name=} {data=}")
                return dict()

            self.select_options = default_select_options

        # 获取包含的字段
        self.included_fields = self._get_included_fields()

        # 使用 timer 在 nicegui 异步事件循环中创建表单
        ui.timer(0, self.create_form, once=True)

    def _get_included_fields(self) -> list[FieldDefinition]:
        """获取要包含在表单中的字段"""
        return [field for field in self.fields if not field.exclude]

    @property
    def column_count(self):
        """计算表单列数"""
        return self.config.column_count or max((int(len(self.included_fields) / 4), 1))

    def onchange(self, value, attr: str = "", field_def: Optional[FieldDefinition] = None):
        """字段值变化时的回调函数"""
        if hasattr(value, "value"):
            value = value.value

        log.debug(f"{attr=} {value=} {type(value)=}")

        try:
            self.errormsg["msg"] = ""
            self.errormsg["visible"] = False

            if field_def is None:
                # 查找字段定义
                field_def = next((f for f in self.fields if f.name == attr), None)

            if field_def is not None:
                # 类型转换和验证
                validated_value = self._validate_and_convert_value(value, field_def)
                self.form_data[attr] = validated_value
                self.validation_results[attr] = True
            else:
                self.form_data[attr] = value
                self.validation_results[attr] = True

        except (ValueError, TypeError) as e:
            error_msg = str(e)
            self.errormsg["msg"] = error_msg
            self.errormsg["visible"] = True
            self.validation_results[attr] = False

        # 更新整个表单的验证状态
        self._update_form_validation()

        # 调用外部变化回调
        if self.on_change is not None:
            self.on_change(attr, self.form_data)

    def _validate_and_convert_value(self, value: Any, field_def: FieldDefinition) -> Any:
        """验证和转换字段值"""
        if value is None:
            if field_def.is_optional:
                return None
            elif field_def.default is not None:
                return field_def.default
            else:
                raise ValueError(f"字段 {field_def.name} 不能为空")

        actual_type = field_def.actual_type

        # 类型转换
        if actual_type is int:
            if isinstance(value, bool):
                raise ValueError(f"字段 {field_def.name} 需要整数类型")
            converted_value = int(value)
            if field_def.min_value is not None and converted_value < field_def.min_value:
                raise ValueError(f"字段 {field_def.name} 的值不能小于 {field_def.min_value}")
            if field_def.max_value is not None and converted_value > field_def.max_value:
                raise ValueError(f"字段 {field_def.name} 的值不能大于 {field_def.max_value}")
            return converted_value

        elif actual_type is float:
            converted_value = float(value)
            if field_def.min_value is not None and converted_value < field_def.min_value:
                raise ValueError(f"字段 {field_def.name} 的值不能小于 {field_def.min_value}")
            if field_def.max_value is not None and converted_value > field_def.max_value:
                raise ValueError(f"字段 {field_def.name} 的值不能大于 {field_def.max_value}")
            return converted_value

        elif actual_type is str:
            return str(value)

        elif actual_type is Path:
            return Path(value)

        elif actual_type is bool:
            return bool(value)

        elif actual_type in (date, time, datetime):
            if isinstance(value, actual_type):
                return value
            elif isinstance(value, str):
                if actual_type is date:
                    return datetime.fromisoformat(value).date()
                elif actual_type is time:
                    return time.fromisoformat(value)
                elif actual_type is datetime:
                    return datetime.fromisoformat(value)
            raise ValueError(f"字段 {field_def.name} 的值格式不正确")

        # 处理列表类型
        elif typing.get_origin(actual_type) in (list, set):
            if isinstance(value, str):
                # 逗号分隔的字符串转换为列表
                items = [item.strip() for item in value.split(",") if item.strip()]
                if typing.get_args(actual_type) and typing.get_args(actual_type)[0] in (int, float):
                    items = [typing.get_args(actual_type)[0](item) for item in items]
                return items
            elif isinstance(value, (list, set)):
                return value
            else:
                return [value]

        # 处理字典类型
        elif typing.get_origin(actual_type) is dict:
            if isinstance(value, dict):
                return value
            else:
                raise ValueError(f"字段 {field_def.name} 需要字典类型")

        # 处理 Literal 类型
        elif typing.get_origin(actual_type) is Literal:
            valid_values = typing.get_args(actual_type)
            if value in valid_values:
                return value
            else:
                raise ValueError(f"字段 {field_def.name} 的值必须是 {valid_values} 中的一个")

        return value

    def _update_form_validation(self):
        """更新整个表单的验证状态"""
        self.form_valid = all(self.validation_results.values()) if self.validation_results else True

    @ui.refreshable
    async def create_form(self):
        """创建表单UI"""
        with ui.card().classes(self.config.class_form_card):
            # 表单标题
            if self.config.title:
                ui.label(self.config.title).classes(self.config.class_heading)

            # 表单字段网格
            grid_class = "gap-1 gap-x-6 w-full items-center"
            columns = "minmax(100px,max-content) 1fr " * self.column_count

            with ui.grid(columns=columns).classes(grid_class):
                for field_def in self.included_fields:
                    await self.get_input(field_def)

            # 错误信息显示
            if self.config.show_validation_errors:
                errlabel, errrow = show_error("")
                errlabel.bind_text_from(self.errormsg, "msg")
                errrow.bind_visibility_from(self.errormsg, "visible").classes("w-full")

            # 按钮行
            with ui.row().classes("w-full justify-end mt-4 gap-2"):
                ui.button(
                    self.config.reset_button_text, on_click=self.handle_reset, color="secondary"
                )
                submit_btn = ui.button(
                    self.config.submit_button_text, on_click=self.handle_submit, color="primary"
                )
                # 绑定表单验证状态到提交按钮
                submit_btn.bind_enabled_from({"form_valid": self.form_valid}, "form_valid")

    async def get_input(self, field_def: FieldDefinition):
        """根据字段定义创建相应的输入组件

        这个方法基于 NiceCRUD.get_input 方法实现，支持多种输入类型。
        """
        field_name = field_def.name
        typ = field_def.actual_type
        curval = self.form_data.get(field_name, field_def.default)
        validation = partial(self.onchange, attr=field_name, field_def=field_def)
        validation_refresh = partial(self.onchange, attr=field_name, field_def=field_def)

        # 字段标签
        with ui.label((field_def.title or field_name) + ":"):
            if field_def.description is not None:
                with ui.tooltip():
                    ui.html(field_def.description)

        # 获取字段属性
        _min = field_def.min_value
        _max = field_def.max_value
        _step = field_def.step
        _input_type = field_def.input_type
        _readonly = field_def.readonly
        _selections = field_def.selections
        _optional = field_def.is_optional

        ele = None

        log.debug(f"{field_name=} {_input_type=} {typ=} {typing.get_origin(typ)=}")

        # 错误处理
        if typ is None:
            log.error(f"no type found for field {field_name}")
            ui.label("ERROR")

        # 选择框输入
        elif _input_type in ("select", "multiselect"):
            if _selections is not None:
                assert isinstance(_selections, dict)
                select_options_dict = {str(k): str(v) for k, v in _selections.items()}
            else:
                select_options_dict = await self.select_options(field_name, self.form_data)

            if len(select_options_dict) == 0 and curval:
                select_options_dict = {curval: curval}

            log.debug(f"{field_name=}: selections = {select_options_dict}")

            if (
                _input_type != "multiselect"
                and curval not in select_options_dict
                and len(select_options_dict) > 0
            ):
                curval = next(iter(select_options_dict.keys()))

            def list_to_dictval(x: list):
                return validation(dict.fromkeys(x))

            ele = ui.select(
                options=select_options_dict,
                value=curval
                if typing.get_origin(typ) is not dict
                else list(curval.keys())
                if isinstance(curval, dict)
                else curval,
                validation=validation if typing.get_origin(typ) is not dict else list_to_dictval,
                multiple=_input_type == "multiselect",
            ).props("use-chips" if _input_type == "multiselect" else "")

        # 字符串输入
        elif typ is str:
            ele = ui.input(
                value=curval or "",
                validation=validation,
                placeholder=field_def.description or "",
            )
            if _optional:
                ele.props("clearable")

        # 路径输入
        elif typ is Path:
            value = str(curval) if curval is not None else ""
            ele = ui.input(
                value=value,
                validation=validation,
                placeholder=field_def.description or "",
            )
            if _optional:
                ele.props("clearable")

        # 日期输入
        elif typ is date:
            with ui.input(value=curval, validation=validation) as dates:
                with ui.menu().props("no-parent-event") as menu:
                    with ui.date().bind_value(dates):
                        with ui.row().classes("justify-end"):
                            ui.button("Close", on_click=menu.close).props("flat")
                with dates.add_slot("append"):
                    ui.icon("edit_calendar").on("click", menu.open).classes("cursor-pointer")
            ele = dates

        # 时间输入
        elif typ is time:
            with ui.input(value=curval, validation=validation) as times:
                with ui.menu().props("no-parent-event") as menu:
                    with ui.time().bind_value(times):
                        with ui.row().classes("justify-end"):
                            ui.button("Close", on_click=menu.close).props("flat")
                with times.add_slot("append"):
                    ui.icon("access_time").on("click", menu.open).classes("cursor-pointer")
            ele = times

        # 日期时间输入
        elif typ is datetime:

            def update_datetime():
                log.debug(
                    f"update_datetime: {dateinput.value=} {timeinput.value=} {type(timeinput.value)=}"
                )
                mydate = (
                    dateinput.value
                    if isinstance(dateinput.value, date)
                    else datetime.fromisoformat(dateinput.value)
                )
                mytime = (
                    timeinput.value
                    if isinstance(timeinput.value, time)
                    else time.fromisoformat(timeinput.value)
                )
                datetimes.value = datetime.combine(mydate, mytime)

            with ui.input(value=curval, validation=validation) as datetimes:
                with ui.menu().props("no-parent-event") as menu:
                    with ui.row():
                        dateinput = (
                            ui.date()
                            .bind_value_from(datetimes, backward=lambda x: x.date())
                            .on_value_change(update_datetime)
                        )
                        timeinput = (
                            ui.time()
                            .bind_value_from(datetimes, backward=lambda x: x.time())
                            .on_value_change(update_datetime)
                        )
                    with ui.row().classes("justify-end"):
                        ui.button("Close", on_click=menu.close).props("flat")
                with datetimes.add_slot("append"):
                    ui.icon("edit_calendar").on("click", menu.open).classes("cursor-pointer")
            ele = datetimes

        # 数字输入
        elif typ in (int, float):
            if _input_type == "number" or _input_type is None or _min is None or _max is None:
                ele = ui.number(
                    value=curval or 0,
                    validation=validation,
                    min=_min,
                    max=_max,
                    step=_step,
                )
                if _optional:
                    ele.props("clearable")
            elif _input_type == "slider":
                ui.slider(
                    value=curval or 0,
                    on_change=validation,
                    min=_min,
                    max=_max,
                    step=_step,
                ).props("label-always").classes("my-4")

        # 字符串字面量
        elif typing.get_origin(typ) == Literal:
            ele = ui.select(
                [x for x in typing.get_args(typ)],
                value=curval,
                validation=validation_refresh,
            )

        # 布尔值输入
        elif typ is bool:
            ele = ui.switch(value=curval or False, on_change=validation_refresh)

        # 字符串列表输入
        elif typing.get_origin(typ) in (list, set) and typing.get_args(typ)[0] is str:
            ele = ui.input(
                value=",".join(curval) if curval else "",
                validation=lambda v: validation(v.split(",")),
            )

        # 数字列表输入
        elif typing.get_origin(typ) is list and issubclass(typing.get_args(typ)[0], (int, float)):
            ele = ui.input(
                value=",".join(map(str, curval)) if curval else "",
                validation=lambda v: validation(v.split(",")),
            )

        else:
            log.warning(f"Unknown input for {field_name=} of {typ=}")
            ele = ui.input(value="ERROR", validation=validation)

        # 设置只读状态
        if _readonly and ele is not None:
            ele.disable()

    async def handle_submit(self):
        """处理表单提交"""
        if not self.form_valid:
            ui.notify("请修正表单中的错误后再提交", color="negative")
            return

        if self.on_submit is not None:
            try:
                await self.on_submit(self.form_data)
            except Exception as e:
                log.error(f"Submit callback failed: {e}")
                ui.notify(f"提交失败: {str(e)}", color="negative")
        else:
            ui.notify("表单提交成功", color="positive")

    def handle_reset(self):
        """处理表单重置"""
        # 重置表单数据到初始状态
        for field_def in self.included_fields:
            self.form_data[field_def.name] = field_def.default

        # 重置验证状态
        self.validation_results = {}
        self.form_valid = True
        self.errormsg["msg"] = ""
        self.errormsg["visible"] = False

        # 刷新表单
        self.create_form.refresh()

        ui.notify("表单已重置", color="info")
