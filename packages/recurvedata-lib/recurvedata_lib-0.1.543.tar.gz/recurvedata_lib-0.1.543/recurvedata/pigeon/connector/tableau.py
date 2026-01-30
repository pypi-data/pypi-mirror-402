"""
official API doc: https://tableau.github.io/server-client-python/docs/api-ref#views
tableau-api-lib：https://github.com/divinorum-webb/tableau-api-lib
"""
import logging
import time
from typing import Optional

import pandas as pd
import tableauserverclient as TSC
from tableau_api_lib import TableauServerConnection
from tableau_api_lib.utils.querying import (
    get_datasource_connections_dataframe,
    get_datasources_dataframe,
    get_embedded_datasources_dataframe,
    get_projects_dataframe,
    get_sites_dataframe,
    get_views_dataframe,
    get_workbooks_dataframe,
)
from tableauserverclient import Server


class TableauConnector:
    def __init__(self, user: str = None, password: str = None, server_url: str = None, site: str = None):
        self.user = user
        self.password = password
        self.server_url = server_url
        self.site = site
        self.server: Optional[Server] = None
        self.library: Optional[TableauServerConnection] = None
        self._sign_in()

    def _sign_in(self):
        tableau_auth = TSC.TableauAuth(self.user, self.password, self.site)
        self.server = TSC.Server(
            self.server_url, use_server_version=True
        )  # https://community.tableau.com/s/question/0D54T00000ti0eOSAQ/api-version-upgrade
        self.server.auth.sign_in(tableau_auth)

        self.library = TableauServerConnection(
            {
                "my_env": {
                    "api_version": self.server.version,
                    "server": self.server_url,
                    "username": self.user,
                    "password": self.password,
                    "site_name": self.site,
                    "site_url": self.site,
                }
            },
            env="my_env",
        )
        self.library.sign_in()

    @staticmethod
    def check_columns(df: pd.DataFrame, cols: list) -> pd.DataFrame:
        if not cols:
            return df
        if not set(cols).issubset(df.columns):
            raise Exception(
                f"Contain wrong columns, target dataframe has {df.columns.to_list()} columns, while input has {cols}"
            )
        return df[cols]

    def get_sites_df(self, cols: list = None):
        df = get_sites_dataframe(self.library).rename(columns={"id": "site_id", "name": "site_name"})
        return self.check_columns(df, cols)

    def get_projects_df(self, cols: list = None):
        df = get_projects_dataframe(self.library).rename(columns={"id": "project_id", "name": "project_name"})
        return self.check_columns(df, cols)

    def get_workbooks_df(self, cols: list = None):
        df = get_workbooks_dataframe(self.library).rename(columns={"id": "workbook_id", "name": "workbook_name"})
        df["project_id"], df["project_name"] = zip(*df["project"].apply(lambda x: (x["id"], x["name"])))
        # df.drop(columns=["project"], inplace=True)
        return self.check_columns(df, cols)

    def get_views_df(self, cols: list = None):
        df = get_views_dataframe(self.library).rename(columns={"id": "view_id", "name": "view_name"})
        df["workbook_id"], df["workbook_name"] = zip(*df["workbook"].apply(lambda x: (x["id"], x["name"])))
        project_df = self.get_projects_df(cols=["project_id", "project_name"])
        df["project_id"] = df["project"].apply(lambda x: x["id"])
        df = df.merge(project_df, on="project_id", how="left")
        return self.check_columns(df, cols)

    def get_datasources_df(self, cols: list = None):
        df = get_datasources_dataframe(self.library).rename(columns={"id": "datasource_id", "name": "datasource_name"})
        df["project_id"], df["project_name"] = zip(*df["project"].apply(lambda x: (x["id"], x["name"])))
        return self.check_columns(df, cols)

    def get_embedded_datasources_df(self, workbook_df: pd.DataFrame, cols: list = None):
        """
        先筛选指定的 workbook，不然很慢
        """
        df = get_embedded_datasources_dataframe(
            self.library, workbook_df, id_col="workbook_id", name_col="workbook_name"
        )
        return self.check_columns(df, cols)

    def get_datasource_connections_df(self, datasources_df: pd.DataFrame = None, cols: list = None):
        if datasources_df is None:
            datasources_df = self.get_datasources_df(cols=["datasource_id", "datasource_name"])
        else:
            datasources_df = self.check_columns(datasources_df, cols=["datasource_id", "datasource_name"])
        connections = []
        for index, row in datasources_df.iterrows():
            ds_conn = get_datasource_connections_dataframe(self.library, row["datasource_id"])
            ds_conn["datasource_id"] = row["datasource_id"]
            connections.append(ds_conn)
        connections_df = pd.concat(connections, ignore_index=True)
        connections_df = connections_df.merge(datasources_df, on="datasource_id", how="left")
        return self.check_columns(connections_df, cols)

    def get_job_status(self, job_id: str):
        return self.server.jobs.get_by_id(job_id)

    def wait_to_finish(self, job_id, timeout, retry_interval):
        abort_time = time.time() + timeout
        job_info = self.get_job_status(job_id)
        while job_info.completed_at is None:
            logging.info(
                f"finish_code: {job_info.finish_code}, progress: {job_info.progress} %. Sleep for {retry_interval} s."
            )
            time.sleep(retry_interval)
            if time.time() > abort_time:
                logging.warning(f"Timeout {timeout} s. Job_info: {job_info}")
                break
            job_info = self.get_job_status(job_id)
        if job_info.finish_code != 0:
            logging.warning(f"Job {job_id} is not success")
        return job_info

    def refresh_workbook(self, workbook_id: str, timeout=600, retry_interval=5):
        logging.info(f"Start refreshing workbook: {workbook_id}")
        res = self.server.workbooks.refresh(workbook_id)
        job_info = self.wait_to_finish(res.id, timeout, retry_interval)
        logging.info(f"Finish refreshing: {job_info}")

    def refresh_datasource(self, datasource_id: str, timeout=600, retry_interval=5):
        logging.info(f"Start refreshing datasource: {datasource_id}")
        res = self.server.datasources.refresh(datasource_id)
        job_info = self.wait_to_finish(res.id, timeout, retry_interval)
        logging.info(f"Finish refreshing: {job_info}")

    def screenshot(self, workbook_id: str, view_id: str, save_path: str, maxage: int = 1):
        """
        截图可能有延迟
        """
        logging.info(f"Start taking screenshot with workbook_id {workbook_id}, view_id {view_id}")
        workbook = self.server.workbooks.get_by_id(workbook_id)
        self.server.workbooks.populate_views(workbook)

        view = self.server.views.get_by_id(view_id)
        image_req_option = TSC.ImageRequestOptions(
            imageresolution=TSC.ImageRequestOptions.Resolution.High, maxage=maxage
        )
        self.server.views.populate_image(view, image_req_option)
        with open(save_path, "wb") as f:
            f.write(view.image)
        logging.info(f"Finish saving screenshot to {save_path}")
