import logging

logger = logging.getLogger(__name__)


# todo: move to common
def init_operator_web(op_cls, router, operator_params: dict):
    if not hasattr(op_cls, "init_web"):
        return
    logger.info(f"operator_params: {operator_params} {op_cls.name()}")
    init_func = getattr(op_cls, "init_web")
    try:
        init_func(router, operator_params.get(op_cls.name(), {}))
    except Exception as e:
        logger.error(f"{op_cls} init_web fail, {str(e)}")
