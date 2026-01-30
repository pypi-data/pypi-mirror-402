import json
import logging

import jsonschema

try:
    from recurvedata.pigeon.connector.feishu import FeishuBot
except ImportError:
    pass

from recurvedata.core.translation import _l
from recurvedata.operators.operator import BaseOperator
from recurvedata.operators.task import BaseTask

logger = logging.getLogger(__name__)


class NotifyTask(BaseTask):
    @staticmethod
    def split_str_lst(s: str, default_value: list[str] = None) -> list[str]:
        if default_value is None:
            default_value = []
        if not s:
            return default_value
        return list(set(item.strip() for item in s.split(",")))

    def execute_impl(self, *args, **kwargs):
        config = self.rendered_config
        bot = FeishuBot(**self.get_connection_by_name(config["feishu_bot"]).extra)

        send_method = bot.send_message
        send_conf = {"msg_type": config.msg_type}
        email_lst = self.split_str_lst(config.at_user_email, default_value=None)
        if config.msg_type == "post":
            send_conf.update({"content": config.text_content})
            if email_lst is None and not config.subject:
                send_conf.update({"msg_type": "text"})
                send_conf.update({"content": json.dumps({"text": config.text_content})})
            else:
                send_method = bot.send_text
                send_conf.pop("msg_type")
                send_conf.update({"email_lst": email_lst, "subject": config.subject})
        else:
            send_conf.update({"content": config.card_content})

        user_lst = self.split_str_lst(config.email)
        chat_name_lst = self.split_str_lst(config.chat_name)
        chat_id_lst = self.split_str_lst(config.chat_id)
        for email in user_lst:
            send_method(receiver_type="user", user_email=email, **send_conf)
        for chat_name in chat_name_lst:
            send_method(receiver_type="group", chat_name=chat_name, **send_conf)
        for chat_id in chat_id_lst:
            send_method(receiver_type="group", chat_id=chat_id, **send_conf)
        logger.info("Message was successfully sent to the receivers.")

    @classmethod
    def config_schema(cls):
        # get_choices_by_type = cls.get_connection_names_by_type
        return {
            "type": "object",
            "properties": {
                "feishu_bot": {
                    "type": "string",
                    "title": _l("Feishu Bot Connection"),
                    "description": _l("Select the Feishu bot connection to use for sending messages"),
                    "ui:field": "ProjectConnectionSelectorField",
                    "ui:options": {
                        "supportTypes": [
                            "feishu_bot",
                        ],
                    },
                },
                "msg_type": {
                    "type": "string",
                    "title": _l("Message Format"),
                    "description": _l("Choose between simple text/post format or interactive card format"),
                    "default": "post",
                    "enum": ["post", "interactive"],
                    "enumNames": ["post", "interactive"],
                },
                "subject": {
                    "ui:hidden": '{{parentFormData.msg_type === "interactive"}}',
                    "type": "string",
                    "title": _l("Message Subject"),
                    "description": _l("Subject line for the message. Supports template variables."),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "at_user_email": {
                    "ui:hidden": '{{parentFormData.msg_type === "interactive"}}',
                    "type": "string",
                    "title": _l("Mention Users"),
                    "description": _l(
                        "Email addresses of users to @mention in the message. Separate multiple emails with commas. Use 'all' to @mention everyone."
                    ),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "text_content": {
                    "ui:hidden": '{{parentFormData.msg_type === "interactive"}}',
                    "type": "string",
                    "title": _l("Message Text"),
                    "default": "",
                    "description": _l("Main text content of the message. Supports template variables."),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "card_content": {
                    "ui:hidden": '{{parentFormData.msg_type === "post"}}',
                    "type": "string",
                    "title": _l("Interactive Card JSON"),
                    "description": _l("JSON definition for the interactive message card. Supports template variables."),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "code",
                        "lang": "json",
                    },
                },
                "email": {
                    "type": "string",
                    "title": _l("Individual Recipients"),
                    "description": _l(
                        "Email addresses of individual users to receive the message. Separate multiple emails with commas."
                    ),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "chat_name": {
                    "type": "string",
                    "title": _l("Group Recipients (by Name)"),
                    "description": _l(
                        "Names of Feishu chat groups to receive the message. Separate multiple names with commas. Bot must be a member of the groups."
                    ),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "chat_id": {
                    "type": "string",
                    "title": _l("Group Recipients (by ID)"),
                    "description": _l(
                        "IDs of Feishu chat groups to receive the message. Separate multiple IDs with commas. Bot must be a member of the groups."
                    ),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
            },
            "required": ["feishu_bot", "msg_type"],
        }

    @classmethod
    def validate(cls, configuration) -> dict:
        config = super().validate(configuration)
        if not any([config["user_email"], config["chat_name"], config["chat_id"]]):
            raise jsonschema.ValidationError(
                message="at least one of (User Email, Chat Group Name, Chat Group ID) must be entered",
                path=("user_email", "chat_name", "chat_id"),
            )
        if config["card_content"]:
            try:
                json.loads(config["card_content"])
            except Exception:
                raise jsonschema.ValidationError(message="Card Content should be valid JSON", path=("card_content",))
        return config


class NotifyOperator(BaseOperator):
    task_cls = NotifyTask
