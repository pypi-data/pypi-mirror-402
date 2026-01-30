import csv

from recurvedata.pigeon.loader.base import BaseLoader
from recurvedata.pigeon.schema import Schema
from recurvedata.pigeon.utils import fs


class CSVToElasticSearchLoader(BaseLoader):
    def __init__(
        self,
        index,
        doc_type,
        filename,
        connector,
        id_field=None,
        generate_id=False,
        delete_file=False,
        csv_options=None,
    ):
        self.index = index
        self.doc_type = doc_type
        self.filename = filename
        self.id_field = id_field
        self.generate_id = generate_id
        self.delete_file = delete_file
        self.es = connector

        self.csv_options = csv_options or {"quoting": csv.QUOTE_ALL, "doublequote": True}

        super().__init__()

    def execute_impl(self):
        schema_file = fs.schema_filename(self.filename)
        if fs.exists(schema_file):
            schema = Schema.load(schema_file)
        else:
            schema = None

        self.es.load_csv(
            self.filename,
            self.index,
            self.doc_type,
            schema,
            id_field=self.id_field,
            generate_id=self.generate_id,
            **self.csv_options,
        )

        if self.delete_file:
            fs.remove_files_safely(self.filename)
            fs.remove_files_safely(schema_file)
