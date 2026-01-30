import logging
import os
import re
from typing import Any, Union

try:
    import emails
except ImportError:
    pass
logger = logging.getLogger(__name__)
_default_html = """<div><includetail><div style="font:Verdana normal 14px;color:#000;">
        <div style="position:relative;"><blockquote style="margin-Top: 0px; margin-Bottom: 0px; margin-Left: 0.5em">
        <div class="FoxDiv20190108121908737768">
        <div id="mailContentContainer" style=" font-size: 14px; padding: 0px; height: auto; min-height: auto ; ">
        {content}
        </div>
        </div></blockquote>
        </div></div>"""


def send_email(
    mail_to: Union[str, list[str], tuple[str, ...]],
    subject: str,
    html: str = None,
    content: str = None,
    cc: Union[str, list[str], tuple[str, ...]] = None,
    bcc: Union[str, list[str], tuple[str, ...]] = None,
    files: Union[str, list[str], tuple[str, ...], dict[str, str]] = None,
    mail_from: str = "noreply",
    reply_to: str = None,
    smtp_config: dict[str, Any] = None,
) -> bool:
    """
    Sends an email.

    Args:
        mail_to: The recipient of the email. Example: 'e1@example.com' or ['e1@example.com', 'e2@example.com'].
        subject: The subject of the email.
        html: The content of the email with special requirements such as font or background color.
        content: The content of the email in plain text format.
        cc: The CC recipients.
        bcc: The BCC recipients.
        files: The list of attachments. Example:
          '/data/tmp.txt' or ['/data/tmp_1.txt', '/data/tmp_2.txt'] or
          {'category_data.txt':'/data/tmp_1.txt', 'brand_data.txt':'/data/tmp_2.txt'}.
        mail_from: The displayed sender of the email. Default is 'RecurveData SERVICE'.
        reply_to: The default recipient when replying. Default is 'itservice@recurvedata.com'.
        smtp_config: The SMTP server for sending the email.

    Returns:
        True if the email was sent successfully, False otherwise.
    """

    if not any((html, content)):
        raise ValueError("At least one of HTML and content is not empty！")

    if isinstance(files, (list, tuple)):
        attach_files = [(file, os.path.basename(file)) for file in files]
    elif isinstance(files, dict):
        attach_files = [(files[file_name], file_name) for file_name in files]
    elif isinstance(files, str):
        attach_files = [(files, os.path.basename(files))]
    elif not files:
        attach_files = []
    else:
        raise ValueError("The parameter files is only support list、dict or string")

    for file_path, _ in attach_files:
        if not os.path.exists(file_path):
            raise ValueError(f"The attachment file does not exist! --- {file_path} ")
        if os.path.isdir(file_path):
            raise ValueError(f"Send directory are not supported, please send after compression！--- {file_path}")

    if not html and content:
        html_content = ""
        for line in content.split("\n"):
            line = line.replace("\t", " " * 4)
            if line:
                result = re.match(r"\s+", line)
                space = result.group(0) if result else ""
                html_content += f'<div style="margin-Left: {len(space)}em">{line.strip()}</div>'
            else:
                html_content += "<div><br></div>"
        html = _default_html.format(content=html_content)
    message = emails.Message(
        subject=subject,
        cc=cc,
        bcc=bcc,
        text="Build passed: {{ project_name }} ...",
        mail_from=(mail_from, smtp_config.get("user")),
        html=html,
        headers={"reply-to": reply_to},
    )

    for file, file_name in attach_files:
        message.attach(data=open(file, "rb"), filename=file_name)
    response = message.send(to=mail_to, smtp=smtp_config)
    if response.status_code == 250:
        return True
    logger.error(
        f"send email from {message.mail_from} to {mail_to}, "
        f"status_code:{response.status_code}, error_msg:{response._exc}"
    )
    return False
