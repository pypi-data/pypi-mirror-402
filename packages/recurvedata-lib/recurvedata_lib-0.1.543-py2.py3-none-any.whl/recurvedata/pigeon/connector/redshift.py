import hashlib
import os

import cytoolz as toolz

from recurvedata.pigeon.connector._registry import register_connector_class
from recurvedata.pigeon.connector.awss3 import S3Connector
from recurvedata.pigeon.connector.postgresql import PostgresConnector, canonical_type_to_pg_type
from recurvedata.pigeon.utils import fs


@register_connector_class("redshift")
class RedshiftConnector(PostgresConnector):
    _max_text = "VARCHAR(MAX)"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.s3_bucket_name = self.kwargs.get("s3_options", {}).get("bucket")

    def is_redshift(self):
        return True

    @toolz.memoize
    def create_s3_connector(self):
        s3_options = self.kwargs.get("s3_options")
        if not s3_options:
            return None
        return S3Connector(**s3_options)

    def load_csv(
        self,
        table,
        filename,
        schema="public",
        columns=None,
        delimiter=",",
        quotechar='"',
        lineterminator="\r\n",
        escapechar=None,
        skiprows=0,
        using_insert=False,
        **kwargs,
    ):
        table = self._format_table_name(table, schema)
        s3 = self.create_s3_connector()
        if using_insert or s3 is None:
            self.load_csv_by_inserting(
                table, filename, columns, delimiter, quotechar, lineterminator, escapechar, skiprows=skiprows, **kwargs
            )
        else:
            self.load_csv_by_s3(table, filename, columns, skiprows, **kwargs)

    def load_csv_by_s3(self, table, filename, columns=None, skiprows=0, **kwargs):
        s3 = self.create_s3_connector()
        bucket = self.generate_s3_bucket_name()
        if filename.endswith(".gz"):
            file_to_upload = filename
        else:
            self.logger.info("compressing %s", filename)
            file_to_upload = fs.gzip_compress(filename, using_cmd=True)
        s, t = self._get_schema_table(table, schema=None)
        key_name = f"{self.database}/{s}/{t}/{os.path.basename(file_to_upload)}"
        key_uri = self.format_s3_key_uri(bucket, key_name)
        self.logger.info("upload %s to %s", file_to_upload, key_uri)
        s3.upload(bucket, file_to_upload, key_name)

        if columns:
            field_names = "({})".format(", ".join([self.quote_identifier(x) for x in columns]))
        else:
            field_names = ""

        # TODO: null
        if skiprows:
            ignore_header = f"IGNOREHEADER AS {int(skiprows)}"
        else:
            ignore_header = ""
        stmt = f"""
            COPY {table} {field_names} FROM '{key_uri}'
            credentials 'aws_access_key_id={s3.aws_access_key_id};aws_secret_access_key={s3.aws_secret_access_key}'
            region '{s3.region}'
            CSV GZIP ACCEPTINVCHARS EMPTYASNULL {ignore_header}
        """

        try:
            self.logger.info("running COPY command")
            self.execute(stmt, autocommit=False, commit_on_close=True)
            self.logger.info("COPY finished")
        except Exception as e:
            self.logger.exception("failed to copy data to Redshift")
            raise e
        finally:
            if file_to_upload != filename:
                self.logger.info("delete %s", file_to_upload)
                fs.remove_files_safely(file_to_upload)

            self.logger.info("delete S3 file: %s", key_uri)
            try:
                s3.delete_key(key_name, bucket)
            except Exception as e:
                self.logger.error(f"operation on s3 bucket fails: {e}")

    @staticmethod
    def from_canonical_type(canonical_type, size):
        rv = canonical_type_to_pg_type.get(canonical_type, "VARCHAR(MAX)")
        if rv == "TEXT":
            rv = "VARCHAR(MAX)"
        return rv

    @staticmethod
    def get_key_name(filename):
        return os.path.basename(filename)

    @staticmethod
    def format_s3_key_uri(bucket, key_name):
        return f"s3://{bucket}/{key_name}"

    def generate_s3_bucket_name(self):
        if self.s3_bucket_name:
            return self.s3_bucket_name
        cluster_name = self.host.split(".", 1)[0]
        digest = hashlib.md5(self.host.encode()).hexdigest()
        return f"pigeon-{cluster_name}-{digest[:15]}"
