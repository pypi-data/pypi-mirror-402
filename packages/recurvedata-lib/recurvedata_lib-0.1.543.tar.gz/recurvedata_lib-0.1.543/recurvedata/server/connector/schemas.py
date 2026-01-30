from recurvedata.executors.schemas import (
    ColumnItem,
    FullDatabaseItem,
    ListDatabases,
    Pagination,
    ResponseModel,
    TableItem,
)


class TestConnectionResponse(ResponseModel):
    pass


class ListDatabasesResponse(ResponseModel):
    data: ListDatabases | None


class ListTablesResponse(ResponseModel):
    data: Pagination[TableItem] | None


class ListColumnsResponse(ResponseModel):
    data: Pagination[ColumnItem] | None


class ListFullDatabasesResponse(ResponseModel):
    data: Pagination[FullDatabaseItem] | None
