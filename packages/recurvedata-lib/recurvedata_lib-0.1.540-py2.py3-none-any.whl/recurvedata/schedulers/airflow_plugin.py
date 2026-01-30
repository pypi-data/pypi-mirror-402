from airflow.plugins_manager import AirflowPlugin


class RecurveAirflowPlugin(AirflowPlugin):
    name = "recurvedata"

    @classmethod
    def on_load(cls, *args, **kwargs):
        import recurvedata.schedulers.debug_celery  # noqa: F401
