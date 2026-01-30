"""Base classes for Stream Operator tasks"""

import logging
from abc import abstractmethod
from typing import TYPE_CHECKING

from recurvedata.executors.models import DataSource
from recurvedata.operators.task import BaseTask

if TYPE_CHECKING:
    from recurvedata.server.stream.flink.schema import SinkConfig, SourceConfig

logger = logging.getLogger(__name__)


class StreamTask(BaseTask):
    """
    Base class for stream tasks (sources and sinks).

    Unlike batch tasks that run once, stream tasks generate configuration
    for long-running Flink CDC jobs.
    """

    def __init__(self, dag, node, execution_date, variables, config):
        super().__init__(dag, node, execution_date, variables)
        self.config = config
        self.stream_config = {}

    @classmethod
    @abstractmethod
    def config_schema(cls):
        """
        JSON schema for task configuration.

        Returns:
            dict: JSON schema
        """
        raise NotImplementedError


class StreamSourceTask(StreamTask):
    """
    Base class for CDC source tasks.

    Represents the data source (database) for streaming replication.
    """

    @staticmethod
    @abstractmethod
    def build_cdc_config_by_datasource(datasource: DataSource, source_config: "SourceConfig") -> dict:
        """
        Build CDC-specific configuration for the source by datasource.
        """
        raise NotImplementedError


class StreamSinkTask(StreamTask):
    """
    Base class for sink tasks.

    Represents the data target (database, data warehouse, or message queue).
    """

    @staticmethod
    @abstractmethod
    def build_sink_config_by_datasource(datasource: DataSource, sink_config: "SinkConfig") -> dict:
        """
        Build sink-specific configuration by datasource.
        """
        raise NotImplementedError
