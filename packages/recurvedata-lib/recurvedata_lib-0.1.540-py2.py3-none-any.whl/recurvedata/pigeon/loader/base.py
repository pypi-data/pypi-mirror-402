import os

from recurvedata.pigeon.schema import Schema
from recurvedata.pigeon.utils import LoggingMixin, fs, sql


class BaseLoader(LoggingMixin):
    def __init__(self, *args, **kwargs):
        pass

    def before_execute(self):
        pass

    def after_execute(self):
        pass

    def execute(self):
        self.before_execute()
        self.execute_impl()
        self.after_execute()

    def execute_impl(self):
        raise NotImplementedError("execute_impl must be implemented by subclass")


class CSVToDBAPIMixin(object):
    @property
    def schema_filename(self) -> str:
        return fs.schema_filename(self.filename)

    def _prepare_target_table(self):
        # add schema for azure data warehouse
        if self.connector.has_table(table=self.table, schema=getattr(self, "schema", None)):
            return

        self.logger.info("table not found, try to create it")
        ddl = self._infer_create_table_ddl()
        if not ddl:
            raise ValueError("table not found, create_table_ddl is required")
        ddl = ddl.strip().rstrip(";")
        self.logger.info("create table ddl: %s\n", ddl)
        with self.connector.cursor() as cursor:
            cursor.execute(ddl)

    def _infer_create_table_ddl(self):
        if not self.create_table_ddl:
            # infer by schema
            schema_file = self.schema_filename
            self.logger.info("infer ddl by schema file %s", schema_file)
            return self._generate_ddl_from_schema(schema_file)

        if "CREATE TABLE" in self.create_table_ddl.upper():
            self.logger.info("self.create_table_ddl contains `CREATE TABLE`, use it")
            create_table_ddl = self.create_table_ddl

            # Safely get schema, defaulting to None if not present
            schema = getattr(self, "schema", None)
            if not schema:
                return create_table_ddl

            self.logger.info(f"add schema {schema} to create table ddl")
            return sql.add_schema_to_create_table(create_table_ddl, schema, self.connector.quote_identifier)

        if os.path.isfile(self.create_table_ddl):
            self.logger.info("self.create_table_ddl is a filename, treat it as schema file")
            return self._generate_ddl_from_schema(self.create_table_ddl)
        return None

    def _generate_ddl_from_schema(self, schema_file):
        if not os.path.exists(schema_file):
            self.logger.error("file not exists, not able to infer DDL")
            return None

        try:
            schema = Schema.load(schema_file)
        except Exception:
            self.logger.exception("failed to load schema from %s", schema_file)
            return None

        ddl_options = getattr(self, "ddl_options", {})
        table_name = getattr(self, "full_table_name", self.table)
        ddl = self.connector.generate_create_table_ddl(table_name, schema, **ddl_options)
        return ddl
