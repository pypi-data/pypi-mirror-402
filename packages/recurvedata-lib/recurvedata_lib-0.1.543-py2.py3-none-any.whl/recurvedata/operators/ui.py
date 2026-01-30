def format_config_schema(config_schema: dict, schema_name: str):
    """
    按前端需求，重新格式化 config_schema
    """
    if "properties" not in config_schema:
        return config_schema
    for field_name, field_dct in config_schema["properties"].items():
        if field_dct["type"] == "object":
            format_config_schema(field_dct, field_name)
        else:
            format_field_schema(field_dct, schema_name)
    return config_schema


def format_field_schema(field_dct: dict, schema_name: str):
    """
    field_dct 例子：
        {
            'type': 'string',
            'title': 'Data Source',
            "ui:field": "ProjectConnectionSelectorField",
            "ui:options": {
                "supportTypes": ["mysql", "postgres",],
            },
        },
    """
    _add_option_id(field_dct)
    _format_input_with_variable(field_dct, schema_name)
    _format_aliases_select_field(field_dct)


def _add_option_id(field_dct: dict):
    ui_field = field_dct.get("ui:field")
    if ui_field == "CodeEditorWithReferencesField":
        return
    if "ui:options" not in field_dct:
        field_dct["ui:options"] = {}
    if "id" in field_dct["ui:options"]:
        return
    field_dct["ui:options"]["id"] = ""


def _format_input_with_variable(field_dct: dict, schema_name: str):
    ui_field = field_dct.get("ui:field")
    if ui_field != "CodeEditorWithReferencesField":
        return
    ui_options: dict = field_dct.get("ui:options")
    if not ui_options:
        return
    ui_type = ui_options.get("type")
    if ui_type != "code":
        return
    # 全屏相关配置
    if "toParent" in ui_options:
        return
    ui_options["toParent"] = ".expanded_code_position"
    ui_options["parentName"] = schema_name
    ui_options["needExpandBtn"] = True


def _format_aliases_select_field(field_dct: dict):
    """
    ProjectConnectionSelectorField 的 supportTypes 前端需要展示 connection 的 ui_type
    """
    from recurvedata.connectors import get_connection_ui_type

    ui_field = field_dct.get("ui:field")
    if ui_field != "ProjectConnectionSelectorField":
        return
    ui_options: dict = field_dct.get("ui:options")
    if not ui_options:
        return

    support_types = ui_options.get("supportTypes")
    if not support_types:
        return

    ui_options["supportTypes"] = [
        ui_type for ui_type in [get_connection_ui_type(backend_type) for backend_type in support_types] if ui_type
    ]
