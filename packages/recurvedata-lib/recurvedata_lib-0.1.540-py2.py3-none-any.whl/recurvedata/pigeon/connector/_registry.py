from recurvedata.pigeon.utils import ensure_str_list

_registry = {}


class register_connector_class(object):
    def __init__(self, ctype):
        self.ctype = ensure_str_list(ctype)

    def __call__(self, connector):
        for t in self.ctype:
            _registry[t] = connector
        return connector


def get_connector_class(ctype):
    return _registry[ctype]
