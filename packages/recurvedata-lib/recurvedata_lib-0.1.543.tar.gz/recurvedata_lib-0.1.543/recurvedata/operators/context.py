import contextvars
import functools
import inspect
import os
import warnings
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from recurvedata.operators.task import BaseTask

try:
    from fsspec.asyn import get_running_loop, sync  # todo
except ImportError:
    pass

from recurvedata.operators.operator import BaseOperator, _registry, get_operator_class


class Context(object):
    """
    Web/Worker 调用的对象，提供：
    1. 注册函数功能
        调用之前需要注册一些函数，用于 config_schema 以及 validate，包括：
            get_connection_names_by_type: 根据连接源 type 返回连接源 names。支持同步/异步写法
            get_connection_by_name: 根据连接源 name 返回连接源对象。支持同步/异步写法 todo
    2. list_config_schemas
    3. get_supported_operators
    4. get_config_schema
    5. Worker 执行时，需要的一些函数

    sync/async 调用
    Context 支持同步/异步的调用方式，
    1. Web 调用是异步，Worker 调用是同步；Web 端注册的 get_connection_names_by_type 等函数是异步的，Worker 端注册的函数是同步的
    2. 为了避免在 operator 里引入 async/await 语法，保持 operator 代码的简洁，
        各个 Operator 里，统一使用同步的写法，
        Operator 里只提供同步的 config_schema, validate, execute 写法，
        context 也提供同步的 get_connection_names_by_type 等方法，供 operator 调用
    3. Web 注册的 get_connection_names_by_type 是异步的，Context 提供的 get_connection_names_by_type 是同步的。
        Context 为了提供同步的 get_connection_names_by_type，把 Web 注册的异步的 get_connection_names_by_type 转成了同步
    4. Operator 的 config_schema 是同步的，而 Web 端调用需要异步的方法，
        所以 Context.get_config_schema 方法通过异步的方式调用 Operator.config_schema
    """

    def __init__(self):
        # 根据连接源 type 返回连接源 names。支持同步/异步写法
        self._get_connection_names_by_type: Callable = None

        # 根据连接源 name 返回连接源对象。支持同步/异步写法
        self._get_connection_by_name: Callable = None

        self.current_project_id = contextvars.ContextVar("Recurve Project ID")

        self._pid = os.getpid()
        self._loop = None
        self.async_mode = False
        self._functions = {}

    def init_context(self, get_connection_names_by_type: Callable = None, get_connection_by_name: Callable = None):
        """
        :param get_connection_names_by_type: 根据连接源 type 返回连接源 names。支持同步/异步写法
                get_connection_names_by_type 函数定义: get_connection_names_by_type(project_id, connection_type)
        :param get_connection_by_name: 根据连接源 name 返回连接源对象。支持同步/异步写法
                get_connection_by_name 函数定义：get_connection_by_name(project_id, connection_name)
        """
        self._get_connection_names_by_type = get_connection_names_by_type
        self._get_connection_by_name = get_connection_by_name
        if inspect.iscoroutinefunction(self._get_connection_names_by_type):
            self.async_mode = True
        else:
            self.async_mode = False

    @property
    def loop(self):
        if self._pid != os.getpid():
            raise RuntimeError("This class is not fork-safe")
        if self._loop:
            return self._loop
        # self._loop = asyncio.get_event_loop() # todo: get_running_loop?
        self._loop = get_running_loop()
        # self._loop = get_loop() # todo: maybe have problem
        return self._loop

    def get_connection_names_by_type(self, connection_type: str) -> list[str]:
        """
        根据连接源类型，返回连接源名称
        Web 端调用的时候，self._get_connection_names_by_type 是异步方法
        Worker 端调用，self._get_connection_names_by_type 是同步方法
        :param connection_type:
        :return:
        """
        project_id = self.current_project_id.get()
        if inspect.iscoroutinefunction(self._get_connection_names_by_type):
            return sync(self.loop, self._get_connection_names_by_type, project_id, connection_type)
        return self._get_connection_names_by_type(project_id, connection_type)

    def get_connection_by_name(self, connection_name: str):
        project_id = self.current_project_id.get()
        if inspect.iscoroutinefunction(self._get_connection_by_name):
            return sync(self.loop, self._get_connection_by_name, project_id, connection_name)
        return self._get_connection_by_name(project_id, connection_name)

    def get_connection_choices_by_type(self, connection_type):
        warnings.warn(
            "This function is deprecated. Please use `get_connection_names_by_type`",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.get_connection_names_by_type(connection_type)

    async def async_call_synchronous_func(self, func, *args):
        project_id = self.current_project_id.get()
        loop = self.loop
        res = await loop.run_in_executor(None, self.contextvars_wrapper(project_id, func), *args)
        return res

    def must_get_connection_by_name(self, connection_name: str):
        connection = self.get_connection_by_name(connection_name)
        if not connection:
            raise ValueError(f"connection {connection_name} not exists")
        return connection

    async def validate_operator_configuration(self, operator_name: str, configuration: dict, project_id: str):
        self.current_project_id.set(project_id)
        operator_cls: BaseOperator = get_operator_class(operator_name)
        if not operator_cls:
            raise ValueError(f"no operator {operator_name}")
        return await self.async_call_synchronous_func(operator_cls.ui_validate, configuration)

    def validate_operator_configuration_synchronously(self, operator_name: str, configuration: dict, project_id: str):
        self.current_project_id.set(project_id)
        operator_cls: BaseOperator = get_operator_class(operator_name)
        if not operator_cls:
            raise ValueError(f"no operator {operator_name}")
        if not self.async_mode:
            return operator_cls.ui_validate(configuration)
        else:
            return sync(self.loop, operator_cls.ui_validate, configuration)

    # validate_operator_configuration_synchronously = sync_wrapper(validate_operator_configuration)

    @staticmethod
    def get_ds_name_field_values(operator_name: str, rendered_config: dict) -> list[str]:
        operator_cls: BaseOperator = get_operator_class(operator_name)
        if not operator_cls:
            raise ValueError(f"no operator {operator_name}")
        return operator_cls.get_ds_name_field_values(rendered_config)

    def contextvars_wrapper(self, project_id, func):
        """
        init contextvars in asyncio
        """

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            token = self.current_project_id.set(project_id)
            res = func(*args, **kwargs)
            self.current_project_id.reset(token)
            return res

        return wrapper

    async def get_config_schema(self, operator_name: str, project_id: str):
        """
        默认返回的是 get_ui_config_schema
        :param operator_name:
        :param project_id:
        :return:
        """
        self.current_project_id.set(project_id)
        operator_cls: BaseOperator = get_operator_class(operator_name)
        if operator_cls:
            return await self.async_call_synchronous_func(operator_cls.ui_config_schema)

    def get_config_schema_synchronously(self, operator_name: str, project_id: str):
        self.current_project_id.set(project_id)
        operator_cls: BaseOperator = get_operator_class(operator_name)
        if not operator_cls:
            raise ValueError(f"no operator {operator_name}")
        if not self.async_mode:
            return operator_cls.ui_config_schema()
        else:
            return sync(self.loop, operator_cls.ui_config_schema)

    # get_config_schema_synchronously = sync_wrapper(get_config_schema)

    @staticmethod
    def get_supported_operators() -> list[str]:
        res_lst = []
        for op_name, op_cls in _registry.items():
            if not op_cls.enabled:
                continue
            res_lst.append(op_name)
        return res_lst

    async def list_config_schemas(self, project_id: str):
        self.current_project_id.set(project_id)
        res_lst = []

        for operator_name, operator_cls in _registry.items():
            res_lst.append(
                {
                    "name": operator_name,
                    "config_schema": await self.async_call_synchronous_func(operator_cls.config_schema),
                }
            )
        return res_lst

    def list_config_schemas_synchronously(self, project_id: str):
        self.current_project_id.set(project_id)
        res_lst = []

        for operator_name, operator_cls in _registry.items():
            res_lst.append(
                {
                    "name": operator_name,
                    "config_schema": self.get_config_schema_synchronously(operator_name, project_id),
                }
            )
        return res_lst

    # list_config_schemas_synchronously = sync_wrapper(list_config_schemas)

    @property
    def client(self):
        return self._client

    @client.setter
    def client(self, client):
        self._client = client

    def register_function(self, name: str, function: Callable):
        self._functions[name] = function

    def init_task_instance_on_task_start(self, task: "BaseTask", *args, **kwargs) -> int:
        func = self._functions.get("init_task_instance_on_task_start")
        if func:
            return func(task, *args, **kwargs)

    def update_task_instance_on_task_finish(
        self,
        task: "BaseTask",
        ti_id: int,
        task_status: str,
        meta: Any,
        error: Exception,
        error_stack: str,
        *args,
        **kwargs,
    ):
        func = self._functions.get("update_task_instance_on_task_finish")
        if func:
            return func(task, ti_id, task_status, meta, error, error_stack, *args, **kwargs)


context = Context()
