import datetime
import json
import logging
import os
import re
import time
from collections import namedtuple
from io import BytesIO
from typing import Dict, List, Tuple, Union
from urllib.parse import unquote

import pandas
import requests

try:
    # python 3.12 requests_toolbelt 0.10 conflict with urllib3 2.0
    from requests_toolbelt import MultipartEncoder
except ImportError:
    pass


class ArgumentException(Exception):
    pass


class FeiShuException(Exception):
    pass


class FeiShuRenewTokenException(FeiShuException):
    pass


class FeiShuMessageException(FeiShuException):
    pass


class FeiShuDocumentException(FeiShuException):
    pass


class FeiShuUploadException(FeiShuDocumentException):
    pass


class FeiShuReadSheetException(FeiShuDocumentException):
    pass


class FeiShuWriteSheetException(FeiShuDocumentException):
    pass


class FeiShuReadExcelException(FeiShuDocumentException):
    pass


class FeiShuReadWikiException(FeiShuDocumentException):
    pass


class FeiShuWriteWikiException(FeiShuDocumentException):
    pass


class FeiShuCreateFolderException(FeiShuDocumentException):
    pass


class FeiShuListChildrenException(FeiShuDocumentException):
    pass


class FeiShuDeleteFileException(FeiShuDocumentException):
    pass


class FeiShuReadBitableException(FeiShuDocumentException):
    pass


Field = namedtuple("Field", ["field_id", "field_name", "type", "property"])
logger = logging.getLogger(__name__)


class FeishuBot:
    APP_ID: str = ""
    APP_SECRET: str = ""

    def __init__(self, app_id=APP_ID, app_secret=APP_SECRET):
        self._host = "https://open.feishu.cn/open-apis"
        self._app_id = app_id
        self._app_secret = app_secret
        self._tenant_access_token = None
        # self._renew_tenant_access_token()  # token valid for 2 hours
        self._tenant_access_token_expiration: int = 0
        self.type_mapping = {  # file_token prefix and corresponding type
            "boxcn": "file",
            "shtcn": "sheet",
            "doccn": "doc",
            "bascn": "bitable",
            "doxcn": "docx",
            "bmncn": "mindnote",
        }
        self._session: requests.Session | None = None

    @property
    def session(self) -> requests.Session:
        if self._session is None:
            self._session = requests.Session()

        if self._should_renew_access_token():
            self._renew_tenant_access_token()
            self._session.headers["Authorization"] = f"Bearer {self._tenant_access_token}"
        return self._session

    def _should_renew_access_token(self) -> bool:
        if self._tenant_access_token is None:
            return True
        if time.time() >= self._tenant_access_token_expiration:
            return True
        return False

    def _renew_tenant_access_token(self):
        logger.info("Attempting to renew tenant_access_token ...")
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal/"
        payload = {"app_id": self._app_id, "app_secret": self._app_secret}
        # 3 attempts to retry
        renew_status = False
        for i in range(3):
            resp = requests.post(url, json=payload, timeout=60)  # 60 seconds timeout
            resp.raise_for_status()
            data = resp.json()
            if data["code"] == 0:
                self._tenant_access_token = data["tenant_access_token"]
                self._tenant_access_token_expiration = (
                    time.time() + data["expire"] - 300
                )  # The server's validity period is a bit shorter, renew in advance
                renew_status = True
                break
            else:
                logger.warning(f"Failed to renew token, retrying {i + 1} time")
        if renew_status:
            logger.info("Successfully renewed tenant_access_token")
        else:
            raise FeiShuRenewTokenException("Failed to renew token")

    def _request(self, method: str, path: str, params=None, json=None, data=None, files=None, headers=None) -> dict:
        # TODO: add retry
        url = f'{self._host}/{path.lstrip("/")}'
        # 10 minutes timeout
        resp = self.session.request(
            method, url, params=params, data=data, json=json, files=files, headers=headers, timeout=600
        )
        logger.info(f"{method} {url} {params}, duration: {resp.elapsed.total_seconds() * 1000:.2f}ms")
        data = resp.json()
        try:
            resp.raise_for_status()
            if data.get("code") in (99991663, 99991668):
                self._renew_tenant_access_token()
        except Exception:
            if data.get("code") in (99991663, 99991668):
                logger.info("tenant access token expired, try to renew and request again")
                self._renew_tenant_access_token()
                return self._request(method, path, params, json, data, files, headers)
        return data

    def _iter_pages(self, path: str, params: dict = None, page_size=100, headers=None):
        has_more = True
        page_token = None
        while has_more:
            query = {
                "page_token": page_token,
                "page_size": page_size,
            }
            if params:
                query.update(params)
            resp = self._request("GET", path, params=query, headers=headers)
            data = resp["data"]
            has_more = data["has_more"]
            if has_more:
                page_token = data["page_token"]
            for item in data["items"]:
                yield item

    def get_group_list(self):
        """
        Get all groups where the application is located
        """
        group_lst = self._iter_pages("/im/v1/chats", {"user_id_type": "open_id"})
        result = [(item["chat_id"], item["name"]) for item in group_lst]
        return result

    def get_user_email(self, open_id):
        """
        Get user email: https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/contact-v3/user/get
        """
        path = f"/contact/v3/users/{open_id}"
        params = {"user_id_type": "open_id", "department_id_type": "open_department_id"}
        resp = self._request("GET", path, params=params)
        if resp["code"] == 0:
            return resp["data"]["user"]["enterprise_email"]
        else:
            raise FeiShuException(f"code: {resp.get('code')}, msg: {resp.get('msg')}")

    def get_group_members(self, chat_id):
        """
        Get the list of group members: https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/im-v1/chat-members/get
        return [(username, email, open_id)]
        """
        path = f"/im/v1/chats/{chat_id}/members"
        member_lst = self._iter_pages(path, {"member_id_type": "open_id"})
        result = [(i["name"], self.get_user_email(i["member_id"]), i["member_id"]) for i in member_lst]
        return result

    def get_name_by_chat_id(self, chat_id):
        """
        Get the group name by chat_id: https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/im-v1/chat/get
        """
        path = f"/im/v1/chats/{chat_id}"
        params = {"user_id_type": "open_id"}
        resp = self._request("GET", path, params=params)
        if resp["code"] == 0:
            return resp["data"]["name"]
        else:
            raise FeiShuException(f"code: {resp.get('code')}, msg: {resp.get('msg')}")

    def get_chat_id_by_name(self, group_name):
        group_lst = self._iter_pages("/im/v1/chats", {"user_id_type": "open_id"})
        result = []
        for group in group_lst:
            if group["name"] == group_name:
                result.append(group["chat_id"])
        if not result:
            logger.info(f"""Group {group_name} was not found in Feishu!""")
        return result

    def get_open_id_by_email(self, email_lst):
        resp = self._request("GET", "/user/v1/batch_get_id", params={"emails": email_lst})
        email_users = resp["data"]["email_users"]
        open_id_dct = {k: email_users[k][0]["open_id"] for k in email_users}
        return open_id_dct

    def send_message(
        self,
        receiver_type="user",
        user_email="",
        chat_name="",
        chat_id="",
        msg_type="text",
        content='{"text":"Feishu notification"}',
    ):
        """
        API documentation: https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/im-v1/message/create
        :param receiver_type: If the receiver is a user, then user_email needs to be filled; if the receiver is a group, then chat_name or chat_id needs to be filled
        :param user_email: Feishu email
        :param chat_name: Feishu group name
        :param chat_id: Feishu group chat_id
        :param msg_type: Message type, including text, post, image, file, audio, media, sticker, interactive, share_chat, share_user,
        Please refer to: https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/im-v1/message/create_json for the specific construction method of each type of message
        :param content: Message content, json structure
        :return: Returns response.json()
        """
        if receiver_type not in ("user", "group"):
            raise ValueError("""receiver_type must be user or group.""")

        if receiver_type == "user":
            if not user_email:
                raise ValueError("""valid user_email is required for receiver_type=user.""")
            params = {"receive_id_type": "email"}
            receive_id = user_email
        else:
            if not chat_id:
                if not chat_name:
                    raise ValueError("""chat_id or chat_name is required for receiver_type=group.""")
                chat_id = self.get_chat_id_by_name(chat_name)[
                    0
                ]  # to_do: Same-named groups may conflict, need to handle
                if not chat_id:
                    raise ValueError(f"""Group {chat_name} was not found in Feishu.""")
            params = {"receive_id_type": "chat_id"}
            receive_id = chat_id

        body = {
            "receive_id": receive_id,
            "content": content,
            "msg_type": msg_type,
        }
        resp = self._request("POST", "/im/v1/messages", params=params, json=body)
        return resp

    def send_card(
        self,
        receiver_type="user",
        user_email="",
        chat_name=None,
        chat_id=None,
        email_lst=None,
        subject="Data Refresh Notification",
        subject_bg_color="green",
        table="",
        table_row_num="",
        oneflow_url="",
        airflow_url="",
        log_url="",
        extra_info="",
        card=None,
        image_lst=None,
    ):
        """
        :param receiver_type: If the receiver is a user, then user_email needs to be filled; if the receiver is a group, then chat_name or chat_id needs to be filled
        :param user_email: Feishu email
        :param chat_name: Feishu group name
        :param chat_id: Feishu group chat_id
        :param email_lst: Feishu email list
        :param subject: Message card-title
        :param subject_bg_color: Message card-title background color, default green, other colors see Feishu interface document
         https://open.feishu.cn/document/ukTMukTMukTM/ukTNwUjL5UDM14SO1ATN
        :param table: Message card-data table
        :param table_row_num: Message card-data table row number
        :param oneflow_url: Message card-OneFlow link
        :param airflow_url: Message card-airflow link
        :param log_url: Message card-update log link
        :param extra_info: Additional text
        :param card: Custom message card
        :param image_lst: Image path list
        :return: Returns response.json()
        """
        msg_type = "interactive"  # The msg_type of the message card is interactive
        if not card:
            # If no card is passed in, it is constructed based on the parameters
            if email_lst == "all":
                at_lst = "<at id=all></at>"
            else:
                at_lst = f"{''.join(['<at email=' + email + '></at>' for email in email_lst])}"
            card = {
                "config": {"wide_screen_mode": True},
                "elements": [
                    {
                        "fields": [
                            {
                                "is_short": True,
                                "text": {
                                    "content": f"**⏱ Time：**\n{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                                    "tag": "lark_md",
                                },
                            },
                            {"is_short": True, "text": {"content": f"**✅ Data Table：**\n{table}", "tag": "lark_md"}},
                            {"is_short": False, "text": {"content": "", "tag": "lark_md"}},
                            {
                                "is_short": True,
                                "text": {"content": f"**📊 Data Row Number：**\n{table_row_num}", "tag": "lark_md"},
                            },
                            {
                                "is_short": True,
                                "text": {"content": f"**👨‍💻 Notified Person：**\n{at_lst}", "tag": "lark_md"},
                            },
                        ],
                        "tag": "div",
                    },
                ],
                "header": {"template": subject_bg_color, "title": {"content": subject, "tag": "plain_text"}},
            }
            # add text
            if extra_info:
                card["elements"].extend(
                    [
                        {"tag": "hr"},
                        {
                            "fields": [{"is_short": False, "text": {"content": extra_info, "tag": "lark_md"}}],
                            "tag": "div",
                        },
                    ]
                )
            # add image
            if image_lst:
                image_key_lst = [self.upload_image(image) for image in image_lst]
                image_content = "\n".join([f"![{k}]({k})" for k in image_key_lst])
                card["elements"].extend(
                    [
                        {"tag": "hr"},
                        {
                            "tag": "markdown",
                            "content": image_content,
                        },
                    ]
                )
            # add buttons
            card["elements"].extend(
                [
                    {"tag": "hr"},
                    {
                        "actions": [
                            {
                                "tag": "button",
                                "text": {"content": "      Update Log      ", "tag": "plain_text"},
                                "type": "default",
                                "url": log_url,
                            },
                            {
                                "tag": "button",
                                "text": {"content": "    OneFlow     ", "tag": "plain_text"},
                                "type": "default",
                                "url": oneflow_url,
                            },
                            {
                                "tag": "button",
                                "text": {"content": "   AirFlow   ", "tag": "plain_text"},
                                "type": "default",
                                "url": airflow_url,
                            },
                        ],
                        "tag": "action",
                    },
                ]
            )
        return self.send_message(
            receiver_type=receiver_type,
            user_email=user_email,
            chat_name=chat_name,
            chat_id=chat_id,
            msg_type=msg_type,
            content=json.dumps(card),
        )

    def send_text(
        self,
        receiver_type: str = "user",
        user_email: str = "",
        chat_name: str = None,
        chat_id: str = None,
        email_lst: Union[str, List[str]] = None,
        subject: str = "Data Notification",
        content: str = "",
        image_lst: List = None,
    ):
        """
        :param receiver_type: If the recipient is a user, user_email needs to be filled in; If the recipient is a group, chat_name or chat_id needs to be filled in
        :param user_email: Feishu email
        :param chat_name: Feishu group name
        :param chat_id: Feishu group chat_id
        :param email_lst: Feishu email list
        :param subject: Rich text message-title
        :param content: Rich text message-content
        :param image_lst: Image path list
        :return: Return response.json()
        """
        msg_type = "post"  # The msg_type of rich text is post
        content = {
            "zh_cn": {
                "title": subject,
                "content": [
                    [{"tag": "text", "text": content}],
                ],
            }
        }
        if email_lst == "all":
            at_lst = [{"tag": "at", "user_id": "all", "user_name": "all"}]
        else:
            at_lst = []
            if email_lst:
                open_id_dct = self.get_open_id_by_email(email_lst)
                for k in open_id_dct:
                    at_lst.append(
                        {
                            "tag": "at",
                            "user_id": open_id_dct[k],
                            "user_name": k,
                        }
                    )
        if at_lst:
            content["zh_cn"]["content"].append(at_lst)
        if image_lst:
            content["zh_cn"]["content"].append(
                [{"tag": "img", "image_key": self.upload_image(image)} for image in image_lst]
            )
        return self.send_message(
            receiver_type=receiver_type,
            user_email=user_email,
            chat_name=chat_name,
            chat_id=chat_id,
            msg_type=msg_type,
            content=json.dumps(content),
        )

    def upload_image(self, file_path, image_type="message") -> str:
        path = "/im/v1/images"
        form = {"image_type": image_type, "image": (open(file_path, "rb"))}
        multi_form = MultipartEncoder(form)
        resp = self._request("POST", path, headers={"Content-Type": multi_form.content_type}, data=multi_form)
        if resp["code"] == 0:
            return resp["data"]["image_key"]
        else:
            return FeiShuUploadException(f"code: {resp.get('code')}, msg: {resp.get('msg')}")

    def upload_file(self, file_path, parent_node="fldcn36aedZjP3L5Vj7QAoi5HQd", overwrite=True) -> str:
        """
        @return: Return a file url
        @param file_path: absolute file path
        @param parent_node: a unique id for a shared folder, default folder is "云文档/共享空间/feishu_loader_test"
        @param overwrite: default True, files with same name will be deleted after uploading
        """
        file_size = os.path.getsize(file_path)
        file_upload_info = {
            "share_link": "https://yimiandata.feishu.cn/file/{file_token}",
            "file_path": file_path,
            "file_size": file_size,
            "parent_node": parent_node,
        }
        # 20971520 is a 20MiB size limit, <= 20MiB, use small file upload, otherwise use large file upload
        if file_size <= 20971520:
            logger.info(f"Ready to upload file: {file_path}, size: {file_size}, use small file upload")
            rv = self._upload_small_file(file_upload_info)
        else:
            logger.info(f"Ready to upload file: {file_path}, size: {file_size}, use large file upload")
            rv = self._upload_large_file(file_upload_info)

        if rv and overwrite:
            # delete files that already exists with the same name if file is successfully uploaded and mode is overwrite
            file_shared_link = rv
            file_token = file_shared_link.split("/")[-1]
            file_name = os.path.basename(file_path)
            self.delete_file_by_title(title=file_name, parent_node=parent_node, keep_lst=[file_token])

        return rv

    def _upload_small_file(self, file_upload_info: dict) -> str:
        file_path = file_upload_info["file_path"]
        parent_node = file_upload_info["parent_node"]
        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)
        with open(file_path, "rb") as f:
            files = {
                "file": (file_name, f, "application/octet-stream"),
                "parent_type": (None, "explorer"),
                "parent_node": (None, parent_node),
                "size": (None, file_size),
                "file_name": (None, file_name),
            }

            logger.info(f"Start uploading process, file_name: {file_name}, file_size: {file_size}")
            # Debug info
            logging.debug(f"small upload request body dict: {files}")
            resp = self._request("POST", "/drive/v1/files/upload_all", files=files)
            if resp["code"] == 0:
                # success
                file_token = resp["data"]["file_token"]
                file_shared_link = file_upload_info["share_link"].format(file_token=file_token)
                logger.info(f"upload succeeded, file token: {file_token}")
                logger.info(f"share link: {file_shared_link}")
                return file_shared_link
            else:
                raise FeiShuUploadException(f"upload small file failed, unknown error, response json: {resp}")

    def _upload_large_file(self, file_upload_info: dict):
        file_upload_info = self._upload_large_file_prepare(file_upload_info)
        file_upload_info = self._upload_large_file_multipart(file_upload_info)
        return self._upload_large_file_finish(file_upload_info)

    def _upload_large_file_prepare(self, file_upload_info):
        file_path = file_upload_info["file_path"]
        parent_node = file_upload_info["parent_node"]
        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)
        body = {"file_name": file_name, "parent_type": "explorer", "parent_node": parent_node, "size": file_size}
        resp = self._request("POST", "/drive/v1/files/upload_prepare", json=body)
        if resp["code"] == 0:
            # success
            file_upload_info["prepare_resp"] = resp
            return file_upload_info
        else:
            raise FeiShuUploadException(f"upload_large_file_prepare failed, unknown error, response json: {resp}")

    def _upload_large_file_multipart(self, file_upload_info: dict) -> dict:
        file_path = file_upload_info["file_path"]
        prepare_resp = file_upload_info["prepare_resp"]
        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)
        upload_id_str = prepare_resp["data"]["upload_id"]
        block_size = prepare_resp["data"]["block_size"]
        block_num = prepare_resp["data"]["block_num"]
        current_block_num = 0
        logger.info(
            f"Start uploading large file, file_size: {file_size} ,block_size: {block_size}, "
            f"block_num in total: {block_num}"
        )

        with open(file_path, "rb") as f:
            while current_block_num < block_num:
                binary_data = f.read(block_size)
                files = {
                    "file": (file_name, binary_data, "application/octet-stream"),
                    "upload_id": (None, upload_id_str),
                    "seq": (None, f"{current_block_num}"),
                    "size": (None, len(binary_data)),
                }
                resp = self._request("POST", "/drive/v1/files/upload_part", files=files)
                if resp["code"] == 0:
                    logger.info(
                        f"upload_large_file_multipart: uploading block {current_block_num + 1} succeeded,"
                        f" progress: "
                        f"{current_block_num + 1}/{block_num}, %{((current_block_num + 1) / block_num) * 100}"
                    )
                else:
                    raise FeiShuUploadException(
                        f"upload_large_file_prepare failed, unknown error, response json: {resp}"
                    )
                current_block_num += 1

        file_upload_info["upload_id"] = upload_id_str
        file_upload_info["block_num"] = block_num
        return file_upload_info

    def _upload_large_file_finish(self, file_upload_info: dict):
        body = {"upload_id": file_upload_info["upload_id"], "block_num": file_upload_info["block_num"]}
        resp = self._request("POST", "/drive/v1/files/upload_finish", json=body)
        if resp["code"] == 0:
            file_token = resp["data"]["file_token"]
            file_shared_link = file_upload_info["share_link"].format(file_token=file_token)
            logger.info(f"upload large file succeeded, file token: {file_token}")
            logger.info(f"share link: {file_shared_link}")
            return file_shared_link
        else:
            raise FeiShuUploadException(f"upload_large_file_finish failed, unknown error, response json: {resp}")

    def read_feishusheet(
        self, file_token: str, sheet: str, use_raw=False, use_filter=False, **kwargs
    ) -> Union[pandas.DataFrame, List[List]]:
        """
        Read the content of a sheet in a Feishu electronic document (not excel or csv).
        Example url: https://yimiandata.feishu.cn/sheets/shtcncglGS4VMi9CcU2GNaNhaVc?sheet=ep8dvw
        @param file_token: The file token of the Feishu electronic document, `htcncglGS4VMi9CcU2GNaNhaVc`
        @param sheet: The token of a sheet in the electronic document, `ep8dvw`
        @param use_raw: default value is False; True returns a list, False returns a pandas.DataFrame
        @param use_filter: default value is False; True only reads the cells within the filter range, False reads all cells
        @param kwargs: extra key-value pairs passed to `pandas.DataFrame()`
        @return: pandas.DataFrame
        """
        file_token = self.get_real_file_token(file_token)
        if use_filter:
            sheet = self.get_sheet_filter_range(file_token, sheet)
        path = f"/sheets/v2/spreadsheets/{file_token}/values/{sheet}"
        params = {"valueRenderOption": "ToString", "dateTimeRenderOption": "FormattedString"}
        resp = self._request("GET", path, params=params)
        if resp["code"] == 0:
            data_dict = resp["data"]["valueRange"]["values"]
            if use_raw:
                return data_dict
            if len(data_dict) == 0:
                return pandas.DataFrame()
            column_names = data_dict[0]
            data_rows = data_dict[1:]
            logger.info(f"Sheet header: {column_names}")
            logger.info(f"{len(data_rows)} rows are downloaded")
            return pandas.DataFrame(data_rows, columns=column_names, **kwargs)
        else:
            raise FeiShuReadSheetException(f"read_feishusheet: Unexpected error. response json: {resp}")

    def get_sheet_filter_range(self, file_token: str, sheet: str) -> str:
        file_token = self.get_real_file_token(file_token)
        path = f"/sheets/v3/spreadsheets/{file_token}/sheets/{sheet}/filter"
        resp = self._request("GET", path)
        if resp["code"] == 0:
            data = resp["data"]
            if not data.get("sheet_filter_info"):
                raise ValueError("use_filter=True requires a filtered cell range in the feishu sheet.")
            cell_range = data["sheet_filter_info"]["range"]
            return cell_range
        else:
            raise FeiShuReadSheetException(f"get_sheet_filter_range: Unexpected error. response json: {resp}")

    def get_spreadsheets_metainfo(self, file_token: str) -> dict:
        """
        Get the metadata of a Feishu spreadsheet based on the file_token
        """
        file_token = self.get_real_file_token(file_token)
        path = f"/sheets/v2/spreadsheets/{file_token}/metainfo"
        resp = self._request("GET", path)
        if resp["code"] == 0:
            return resp["data"]
        else:
            raise FeiShuReadSheetException(f"get_spreadsheets_metainfo: Unexpected error. response json: {resp}")

    def get_sheet_metainfo(self, file_token: str, sheet: str) -> dict:
        """
        Get the metadata of a single sheet in a Feishu spreadsheet based on the file_token and sheet
        """
        file_token = self.get_real_file_token(file_token)
        spreadsheets_metainfo = self.get_spreadsheets_metainfo(file_token)
        for sheet_metainfo in spreadsheets_metainfo["sheets"]:
            if sheet == sheet_metainfo["sheetId"]:
                return sheet_metainfo
        raise FeiShuReadSheetException(f"get_sheet_metainfo: sheetId={sheet} does not exist.")

    def get_sheet_ids(self, file_token):
        """Get the sheet ids on a Feishu document
        Args:
            file_token (str): Feishu file token, the characters after https://yimiandata.feishu.cn/sheets/ are the token
        Returns:
            DataFrame: sheet data
        """
        file_token = self.get_real_file_token(file_token)
        # 1. Get the metadata of the sheet, and get the sheet_id of the corresponding sheet_name
        path = f"/sheets/v2/spreadsheets/{file_token}/metainfo"
        resp = self._request("GET", path)
        sheet_ids = []
        sheet_names = []
        for sheet in resp["data"]["sheets"]:
            sheet_ids.append(sheet["sheetId"])
            sheet_names.append(sheet["title"])
        return sheet_ids, sheet_names

    def read_feishusheets(self, file_token: str, **kwargs) -> pandas.DataFrame:
        """
        Read the content of multiple sheets in a Feishu electronic document (not excel or csv).
        Example url: https://yimiandata.feishu.cn/sheets/shtcncglGS4VMi9CcU2GNaNhaVc?sheet=ep8dvw
        @param file_token: The file token of the Feishu electronic document, `htcncglGS4VMi9CcU2GNaNhaVc`
        @param sheet: The token of a sheet in the electronic document, `ep8dvw`
        @param kwargs: extra key-value pairs passed to `pandas.DataFrame()`
        @return: pandas.DataFrame
        """
        file_token = self.get_real_file_token(file_token)
        sheet_ids, sheet_names = self.get_sheet_ids(file_token)
        df_new = []
        for index, sheet in enumerate(sheet_ids):
            _df = self.read_feishusheet(file_token, sheet, **kwargs)
            df_new.append(_df)
        return pandas.concat(df_new)

    def read_feishuexcel(self, file_token: str, is_excel: bool = True, **kwargs) -> pandas.DataFrame:
        """
        Read the Excel or CSV file uploaded to Feishu, the BOT needs to have read permission for this document.
        Example Excel url: https://yimiandata.feishu.cn/file/boxcnJo72CHvjRdD2uTC3dvN5Oc
        Example Csv url: https://yimiandata.feishu.cn/file/boxcnZDcu7NSjfcHA7ioZwEA6Ye
        @param file_token: The token of the document, `boxcnJo72CHvjRdD2uTC3dvN5Oc`
        @param is_excel: default read Excel, if `False`, call `pands.read_csv()`
        @param kwargs: extra key-value pairs passed to `pandas.read_excel()` or `pandas.read_csv()`
        @return: pandas.DataFrame
        """
        url = f"https://open.feishu.cn/open-apis/drive/v1/files/{file_token}/download"
        resp = self.session.get(url)
        if resp.status_code == 200:
            # Determine whether it is CSV or Excel through Content-Type, no need to specify, is_excel parameter does not take effect
            logger.info(resp.headers)
            content_type = resp.headers.get("Content-Type", "").lower()
            if "csv" in content_type:
                return pandas.read_csv(BytesIO(resp.content), **kwargs)
            return pandas.read_excel(resp.content, **kwargs)

        elif resp.status_code == 404:
            raise FeiShuReadExcelException("file not found")
        elif resp.status_code == 403:
            raise FeiShuReadExcelException("Bot has no access to this file")
        elif resp.status_code == 400:
            response = resp.json()
            raise FeiShuReadExcelException(f"read_feishuexcel: Unexpected error. response json:{response}")
        else:
            raise FeiShuReadExcelException(
                "read_feishuexcel: Unexpected error. " f"response text:{resp.text}, status_code: {resp.status_code}"
            )

    def create_folder(self, title, parent_node):
        folder_token_lst = self.get_children_token(children_type="folder", children_name=title, parent_node=parent_node)
        if folder_token_lst:
            logging.warning(f"Folder {title} already exists in parent_node={parent_node}")
            return

        path = f"/drive/explorer/v2/folder/{parent_node}"
        resp = self._request("POST", path, json={"title": title})
        if resp["code"] == 0:
            url = resp["data"]["url"]
            logger.info(f"Folder {title} url: {url}")
            return url
        else:
            raise FeiShuCreateFolderException(f"create_folder: Unexpected error. response json: {resp}")

    def delete_file_by_title(self, title, parent_node, keep_lst=[]):
        file_token_lst = self.get_children_token(children_type="file", children_name=title, parent_node=parent_node)
        if not file_token_lst:
            logging.warning(f"File {title} does not exist in parent_node={parent_node}")
            return

        for file_token in file_token_lst:
            if file_token in keep_lst:
                continue
            self.delete_file_by_token(file_token)

    def delete_file_by_token(self, file_token):
        # Only able to delete files where FeishuBot is the owner
        path = f"/drive/v1/files/{file_token}"
        resp = self._request("DELETE", path, params={"type": "file"})
        if resp["code"] == 0:
            logger.info(f"file_token={file_token} has been deleted")
        else:
            raise FeiShuDeleteFileException(f"delete_file: Unexpected error. response json: {resp}")

    def list_children(self, parent_node):
        path = f"/drive/explorer/v2/folder/{parent_node}/children"
        resp = self._request("GET", path)
        if resp["code"] == 0:
            children_lst = [v for k, v in resp["data"]["children"].items()]
            return children_lst
        else:
            raise FeiShuListChildrenException(f"list_children: Unexpected error. response json: {resp}")

    def get_children_token(self, children_type, children_name, parent_node):
        # children_type in ('doc', 'sheet', 'file', 'bitable', 'folder')
        token_lst = []
        children_lst = self.list_children(parent_node)
        if not children_lst:
            return token_lst
        for c in children_lst:
            if c["type"] == children_type and c["name"] == children_name:
                token_lst.append(c["token"])
        return token_lst

    def _get_bitable_tables(self, file_token: str) -> Dict[str, str]:
        """
        Get multi-dimensional table-data table list
        :param file_token: The token of the multi-dimensional table, which is the app_token in the Feishu development document
        :return: Dict<table_name,table_id>
        """
        path = f"/bitable/v1/apps/{file_token}/tables"
        gen = self._iter_pages(path, page_size=10)
        table_dict = {}
        for item in gen:
            table_dict[item["name"]] = item["table_id"]
        return table_dict

    def _get_bitable_table_fields(self, file_token: str, table_id: str) -> List:
        """
        Get multi-dimensional table-data table fields
        Field description check `https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/bitable-v1/app-table-field/guide`
        :param file_token: The token of the multi-dimensional table, which is the app_token in the Feishu development document
        :param table_id: Data table id
        :return: List[(field_id, field_name, multi-dimensional table field type, field property varies with field type)]
        """
        path = f"/bitable/v1/apps/{file_token}/tables/{table_id}/fields"
        fields = []
        gen = self._iter_pages(path, page_size=10)
        for item in gen:
            fields.append(Field(item["field_id"], item["field_name"], item["type"], item["property"]))
        return fields

    def _get_bitable_table_records(self, file_token: str, table_id: str, fields: List, **kwargs) -> pandas.DataFrame:
        """
        Get multi-dimensional table-data table records
        Field type (details refer to `https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/bitable-v1/app-table-field/guide`)
            1: Multi-line text
            2: Number
            3: Single selection
            4: Multiple selection
            5: Date
            7: Checkbox
            11: Personnel
            15: Hyperlink
            17: Attachment
            18: One-way association
            19: Find reference
            20: Formula
            21: Two-way association
            1001: Creation time
            1002: Last update time
            1003: Creator
            1004: Modifier
            1005: Automatic number
        :param file_token: The token of the multi-dimensional table, which is the app_token in the Feishu development document
        :param table_id: Data table id
        :param fields: Header field list
        :param pk: Primary key column name
        :param kwargs: Parameters passed to pandas
        :return: Data table record df
        """
        path = f"/bitable/v1/apps/{file_token}/tables/{table_id}/records"
        params = {
            "display_formula_ref": True,  # Control whether to display the complete original result of the formula and find reference, please refer to the Feishu development document for specific instructions
            "automatic_fields": True,  # Control whether to return automatically calculated fields, please refer to the Feishu development document for specific instructions
        }
        records = []
        gen = self._iter_pages(path, params=params, page_size=100)
        for item in gen:
            record = item.get("fields", {})
            bitable_raw_data = json.dumps(record, ensure_ascii=False)
            new_record = []
            for field in fields:
                field_name = field.field_name
                if record.get(field_name) is None:
                    value = None
                elif field.type in (1, 2, 3, 7, 20, 1005):
                    value = record[field_name]
                elif field.type in (4,):
                    value = str(record[field_name])
                elif field.type in (11,):
                    value = str([x["name"] for x in record[field_name]])
                elif field.type in (5, 1001, 1002):
                    value = datetime.datetime.fromtimestamp(record[field_name] / 1000)
                elif field.type in (17,):
                    value = str([x["url"] for x in record[field_name]])
                elif field.type in (15,):
                    value = record[field_name].get("link")
                elif field.type in (19,):
                    # todo: It seems that the find reference type supports multiple types of data, but currently only text type data is used in the demand, and the format of other types of data returned cannot be determined temporarily
                    value = str([x.get("text") for x in record[field_name].get("value", [])])
                elif field.type in (1003, 1004):
                    value = record.get(field.field_name, {}).get("name")
                else:
                    value = record[field_name]
                new_record.append(value)
            new_record.append(bitable_raw_data)
            records.append(new_record)

        col_names = [field.field_name for field in fields]
        col_names.append("bitable_raw_data")
        df = pandas.DataFrame(records, columns=col_names, **kwargs)
        # Filter out the automatic number field columns
        df.drop(labels=[field.field_name for field in fields if field.type == 1005], axis=1, inplace=True)
        return df

    def read_bitable(self, file_token: str, table_names: List[str] = None, **kwargs) -> Dict[str, pandas.DataFrame]:
        """
        Read the data of the Feishu multi-dimensional table, divided into 3 steps:
        1. Get the data table list of the multi-dimensional table
        2. Get the header field information according to the data table
        3. Get the data table records, and parse the data according to the different types of header fields
        :param table_names: List of data tables to be read, read all data tables by default
        :param file_token: The token of the multi-dimensional table, which is the app_token in the Feishu development document
        :param kwargs: Parameters passed to pandas
        :return: Map<Data table name, Data table DF>
        """
        file_token = self.get_real_file_token(file_token)
        table_dict = self._get_bitable_tables(file_token)
        table_df_dict = {}
        if table_names is None:
            table_names = table_dict.keys()

        # First check the table name
        for table_name in table_names:
            if table_dict.get(table_name) is None:
                raise ArgumentException(f"read_bitable: Wrong table name error: {table_name}")

        for table_name in table_names:
            table_id = table_dict[table_name]
            fields = self._get_bitable_table_fields(file_token, table_id)
            table_df = self._get_bitable_table_records(file_token, table_id, fields, **kwargs)
            table_df_dict[table_name] = table_df

        return table_df_dict

    def get_real_file_token(self, file_token) -> str:
        """Currently supports 3 types of file_token, the first 5 characters are fixed values
        Knowledge base - wikcn; Multi-dimensional table - bascn; Spreadsheet - shtcn; File - boxcn; New document - doxcn;
        Mind map - bmncn; doccn_- Document
        """
        # If it is a wiki, you need to request the file_token of the actual object once
        try:
            _, file_token = self.get_wiki_type_token(wiki_token=file_token)
            return file_token
        except Exception:
            return file_token

    def get_wiki_type_token(self, wiki_token: str) -> Tuple[str, str]:
        """
        Get the document type and token of a node in the Feishu knowledge base
        @param wiki_token: The node token of the Feishu knowledge base, sheet: `wikcn1MAs8sOhEUF1LhiKPHRPZe`, multi-dimensional table: `wikcnBJcryeMkPQP4gxmR6YXP8g`
        @return [obj_type, obj_token]
        """
        resp = self._request("GET", "/wiki/v2/spaces/get_node", params={"token": wiki_token})
        if resp["code"] == 0:
            obj_type = resp["data"]["node"]["obj_type"]
            obj_token = resp["data"]["node"]["obj_token"]
            return obj_type, obj_token
        else:
            raise FeiShuReadWikiException(f"get_wiki_type_token: Unexpected error. response json: {resp}")

    def get_document_metadata(self, file_tokens: List, with_url=False) -> dict:
        """
        Get document metadata: `https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/drive-v1/meta/batch_query`
        Note!! If an error occurs, please re-upload the file to confirm that the token has a file type prefix
        @param file_tokens: file token list ['boxcnlAUCgIesXRBgndlifeR7af', 'shtcnx8YVo30ML6G5GB6wjk6Pfh']
        @param with_url: Return the url corresponding to the file token
        """
        if not (1 <= len(file_tokens) <= 200):
            raise ArgumentException("range must be between 1 and 200")
        file_tokens = [self.get_real_file_token(x) for x in file_tokens]
        request_docs = []
        for token in file_tokens:
            doc_type = None
            for prefix, t in self.type_mapping.items():
                if token.startswith(prefix):
                    doc_type = t
                    break
            if not doc_type:
                raise FeiShuException(f"Unsupported doc-type with token: {token}")
            request_docs.append({"doc_token": token, "doc_type": doc_type})

        path = "/drive/v1/metas/batch_query"
        body = {"request_docs": request_docs, "with_url": with_url}
        resp = self._request("POST", path, json=body)
        if resp["code"] == 0:
            successe_list = resp["data"]["metas"]
            failed_list = []
            if resp["data"].get("failed_list"):
                reason_dict = {
                    970002: "Unsupported doc-type",
                    970003: "No permission to access met",
                    970005: "Record not found (不存在或者已被删除)",
                }
                for item in resp["data"]["failed_list"]:
                    failed_list.append(
                        {"doc_token": item["token"], "reason": reason_dict.get(item["code"], "Unknown reason")}
                    )
            return {"success": successe_list, "failed": failed_list}
        else:
            raise FeiShuException(f"get_document_metadata: Unexpected error. response json: {resp}")

    def get_file_object(self, file_token: str, save_path: str = None):
        """
        Get the file name and binary object: `https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/drive-v1/file/download`
        Notes: `https://yimiandata.feishu.cn/wiki/wikcnObMT9VE0Rc8J4FpR7ncWJf#UOS8fZ`
        @param file_token: file token, such as 'shtcnx8YVo30ML6G5GB6wjk6Pfh'
        @param save_path: Save path, such as /tmp, optional
        return File name and file binary object
        """
        file_token = self.get_real_file_token(file_token)
        url = f"https://open.feishu.cn/open-apis/drive/v1/files/{file_token}/download"
        resp = self.session.get(url)

        if resp.status_code == 200:
            content_disposition = resp.headers.get("Content-Disposition")
            filename = unquote(re.findall("""\'\'(.*?)$""", content_disposition)[-1])
            file_object = BytesIO(resp.content)
            if save_path:
                save_file_path = os.path.join(save_path, file_token)
                if not os.path.exists(save_file_path):
                    os.makedirs(save_file_path)
                    logger.info("Create directory: " + save_file_path)
                full_path = os.path.join(save_file_path, filename)
                try:
                    with open(full_path, "wb") as file:
                        logger.info(f"Start writing file {full_path}")
                        file.write(file_object.getvalue())
                        logger.info(f"File {filename} successfully written to {full_path}")
                except Exception as e:
                    raise Exception(f"Failed to write {full_path}: {e}")

            return filename, file_object
        elif resp.status_code == 404:
            raise FeiShuException("file not found")
        elif resp.status_code == 403:
            raise FeiShuException("Bot has no access to this file")
        else:
            raise FeiShuException(
                f"get_file_object: Unexpected error. response text:{resp.text}, status_code: {resp.status_code}"
            )

    def write_feishusheet(self, file_token: str, sheet: str, cell_range: str, values: List):
        """
        Write a specific cell range of a sheet in the Feishu electronic document (not excel or csv)
        Example url: `https://yimiandata.feishu.cn/sheets/shtcncglGS4VMi9CcU2GNaNhaVc?sheet=ep8dvw`
        @param file_token: The file token of the Feishu electronic document, `htcncglGS4VMi9CcU2GNaNhaVc`
        @param sheet: The token of a sheet in the electronic document, `ep8dvw`
        @param cell_range: The cell range where the data needs to be written A1:B1
        """
        file_token = self.get_real_file_token(file_token)
        path = f"/sheets/v2/spreadsheets/{file_token}/values"
        body = {"valueRange": {"range": f"{sheet}!{cell_range}", "values": values}}
        resp = self._request("PUT", path, json=body)
        if resp["code"] == 0:
            logger.info(f"write_sheet: {resp['data']}")
        else:
            raise FeiShuWriteSheetException(f"write_sheet: Unexpected error. response json: {resp}")

    def clear_sheet_contents(self, file_token: str, sheet: str):
        file_token = self.get_real_file_token(file_token)
        sheet_metainfo = self.get_sheet_metainfo(file_token, sheet)
        max_row = sheet_metainfo["rowCount"]
        max_col = sheet_metainfo["columnCount"]
        max_col_letter = self._get_column_letter(max_col)
        cell_range = f"A1:{max_col_letter}{max_row}"

        null_values = [[None] * max_col] * max_row
        self.write_feishusheet(file_token, sheet, cell_range, null_values)

    @staticmethod
    def _get_column_letter(col_id):
        if not (1 <= col_id <= 16384):
            # excel maximum column number 16384
            raise ValueError("column_id should be between 1 and 16384")
        letters = []
        while col_id > 0:
            col_id, remainder = divmod(col_id, 26)
            if remainder == 0:
                remainder = 26
                col_id -= 1
            letters.append(chr(remainder + 64))
        return "".join(reversed(letters))

    def create_sheet(self, file_token: str, sheet_name: str):
        """
        Feishu spreadsheet, create new sheet
        @param file_token: The file token of the Feishu electronic document, `htcncglGS4VMi9CcU2GNaNhaVc`
        @param sheet_name: The name of the sheet to be created, `sheet1`
        """
        meta_info = self.get_spreadsheets_metainfo(file_token)
        path = f"/sheets/v2/spreadsheets/{file_token}/sheets_batch_update"
        param = {
            "requests": [
                {
                    "addSheet": {
                        "properties": {"title": sheet_name, "index": meta_info.get("properties").get("sheetCount")}
                    }
                }
            ]
        }
        resp = self._request("POST", path, json=param)
        if resp["code"] == 0:
            return resp["data"]
        else:
            raise FeiShuException(f"code: {resp.get('code')}, msg: {resp.get('msg')}")

    def get_employees(self, view="basic", status=None, user_id_type="open_id", user_ids=None):
        """
        Get employee information
        https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/ehr/ehr-v1/employee/list
        :param view: basic: overview, only return id, name and other basic information; full: detail, return system standard fields and custom field collection, default is basic
        :param status: 1: To be hired, 2: In service, 3: Canceled entry, 4: To be resigned, 5: Resigned. Multiple states are separated by commas
        :param user_id_type: open_id/union_id/user_id, default open_id
        :param user_ids: User id corresponding to user_id_type
        :return: List of employee information
        """
        path = "/ehr/v1/employees"
        params = {"view": view, "status": status, "user_id_type": user_id_type, "user_ids": user_ids}
        member_lst = self._iter_pages(path, params=params)
        result = [i["system_fields"] for i in member_lst]
        return result
