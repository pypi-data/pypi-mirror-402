import os

try:
    from recurvedata.pigeon.utils import fs
except ImportError:
    pass

from recurvedata.core.translation import _l
from recurvedata.operators.transfer_operator.task import LoadTask
from recurvedata.utils.email_util import send_email

_default_html = """<div><includetail><div style="font:Verdana normal 14px;color:#000;">
<div style="position:relative;"><blockquote style="margin-Top: 0px; margin-Bottom: 0px; margin-Left: 0.5em">
<div class="FoxDiv20190108121908737768">
<div id="mailContentContainer" style=" font-size: 14px; padding: 0px; height: auto; min-height: auto ; ">
<div>Dear all,</div>
<div><br></div>

<div>————————</div>
<div>RecurveData Automatic Reporting</div>
</div>
</div></blockquote>
</div></div>"""


class EmailLoadTask(LoadTask):
    ds_name_fields = ("data_source_name",)
    ds_types = ("mail",)
    worker_install_require = ["pigeon"]

    def execute_impl(self, *args, **kwargs):
        load_options = self.rendered_config
        ds = self.must_get_connection_by_name(load_options["data_source_name"])
        smtp_config = {
            "host": ds.host,
            "port": ds.port,
            "ssl": ds.extra.get("ssl", True),
            "user": ds.user,
            "password": ds.password,
            "timeout": ds.extra.get("timeout", 60),
        }

        remove_files = [self.filename]
        filename = load_options.get("filename")
        default_file_ext = ".csv"
        if filename and "." not in filename:
            filename = f"{filename}{default_file_ext}"
        if filename and self.filename:
            # 文件压缩
            uncompress_filename = filename
            if filename.endswith((".zip", ".gz")):
                uncompress_filename = ".".join(filename.split(".")[:-1])
            new_filename = os.path.join(os.path.dirname(self.filename), uncompress_filename)
            os.rename(self.filename, new_filename)
            compress_mode = load_options["compress_mode"]
            file_upload, ext = self.compress_file(filename=new_filename, compress_mode=compress_mode)
            if compress_mode != "None" and not load_options["filename"].endswith(ext):
                filename = f"{filename}{ext}"

            files = {filename: file_upload}
            remove_files = [new_filename, file_upload]
        else:
            files = None

        ok = send_email(
            mail_to=self.parse_email_list(load_options["mail_to"]),
            subject=load_options["subject"],
            html=load_options["html"],
            cc=self.parse_email_list(load_options.get("cc")),
            bcc=self.parse_email_list(load_options.get("bcc")),
            files=files,
            mail_from=load_options["mail_from"],
            reply_to=load_options.get("reply_to"),
            smtp_config=smtp_config,
        )
        assert ok, "Failed to send email"
        fs.remove_files_safely(remove_files)

    @staticmethod
    def parse_email_list(obj, separator=";"):
        if not obj:
            return None
        return obj.split(separator)

    @classmethod
    def config_schema(cls):
        # get_choices_by_type = cls.get_connection_names_by_type
        # dss = get_choices_by_type(cls.ds_types)
        schema = {
            "type": "object",
            "properties": {
                "data_source_name": {
                    "type": "string",
                    "title": _l("SMTP Server"),
                    "ui:field": "ProjectConnectionSelectorField",
                    "ui:options": {
                        "supportTypes": cls.ds_types,
                    },
                },
                "subject": {
                    "type": "string",
                    "title": _l("Email Subject"),
                    "description": _l("Subject line of the email"),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "mail_to": {
                    "type": "string",
                    "title": _l("Recipients"),
                    "description": _l("Email recipients (separate multiple addresses with semicolons)"),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "mail_from": {
                    "type": "string",
                    "title": _l("Sender Name"),
                    "default": "RecurveData SERVICE",
                    "description": _l("Display name that appears as the email sender"),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "cc": {
                    "type": "string",
                    "title": _l("CC Recipients"),
                    "description": _l("Carbon copy recipients (separate multiple addresses with semicolons)"),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "bcc": {
                    "type": "string",
                    "title": _l("BCC Recipients"),
                    "description": _l("Blind carbon copy recipients (separate multiple addresses with semicolons)"),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "html": {
                    "type": "string",
                    "title": _l("Email Body"),
                    "description": _l("HTML content of the email body."),
                    "default": _default_html,
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "code",
                        "lang": "python",
                    },
                },
                "filename": {
                    "type": "string",
                    "title": _l("Attachment Name"),
                    "description": _l(
                        "Name of the email attachment. Supports template variables. Leave empty for no attachment. Default extension is .csv if none specified."
                    ),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
                "compress_mode": {
                    "type": "string",
                    "title": _l("Compression Method"),
                    "enum": ["None", "Gzip", "Zip"],
                    "enumNames": ["None", "Gzip", "Zip"],
                    "default": "None",
                    "description": _l("Compression method for attachments"),
                },
                "reply_to": {
                    "type": "string",
                    "title": _l("Reply-To Address"),
                    "description": _l("Email address that will receive replies to this email"),
                    "ui:field": "CodeEditorWithReferencesField",
                    "ui:options": {
                        "type": "plain",
                    },
                },
            },
            "required": ["data_source_name", "subject", "mail_to", "mail_from", "html"],
        }
        return schema
