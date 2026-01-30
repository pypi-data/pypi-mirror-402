import copy
import datetime
import inspect
import re
import types
from typing import Any, Callable, TypeVar

import jinja2.nodes
from jinja2 import Environment, TemplateSyntaxError, meta, pass_context
from jinja2.runtime import Context

from recurvedata.utils.crontab import previous_schedule
from recurvedata.utils.registry import jinja2_template_funcs_registry

T = TypeVar("T")

# {% set navigation = [('index.html', 'Index'), ('about.html', 'About')] %} -> navigation
# {% set key, value = call_something() %} -> key, value
_jinja2_set_p = re.compile(r"\{%\s*set\s([\w,\s]+?)\s*=.*")


def get_template_env() -> Environment:
    env = Environment(
        cache_size=0,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    for func_name, func in jinja2_template_funcs_registry.items():
        env.globals[func_name] = func
    return env


def extract_vars_from_template_code(template_code: str) -> list[str]:
    """
    This function is copied from recurve-server recurve.library.jinja_utils
    """
    env = Environment(autoescape=True)
    ast = env.parse(template_code)

    extracted_var_names = []

    # Helper function to recursively walk through nodes
    def visit_node(node: jinja2.nodes.Node):
        # We're looking for Call nodes where the function is 'var'
        if isinstance(node, jinja2.nodes.Call) and isinstance(node.node, jinja2.nodes.Name) and node.node.name == "var":
            # The first argument of the Call node is the variable name
            arguments = [arg.value for arg in node.args if isinstance(arg, jinja2.nodes.Const)]
            extracted_var_names.append(arguments[0])

        # Recursively visit child nodes
        for child_node in node.iter_child_nodes():
            visit_node(child_node)

    # Start the traversal
    visit_node(ast)

    return extracted_var_names


@pass_context
def var_function(context: Context, name: str, default: Any = None) -> Any:
    return context.get(name, default)


class Renderer(object):
    def __init__(self):
        self.env = get_template_env()
        self.env.globals["var"] = var_function

    @staticmethod
    def init_context(execution_date: datetime.datetime, schedule_interval: str):
        yesterday_dttm = execution_date - datetime.timedelta(days=1)
        tomorrow_dttm = execution_date + datetime.timedelta(days=1)
        data_interval_start = previous_schedule(schedule_interval, execution_date)

        template_context = {
            "dt": execution_date.date(),
            "yesterday": yesterday_dttm,
            "yesterday_dt": yesterday_dttm.date(),
            "tomorrow": tomorrow_dttm,
            "tomorrow_dt": tomorrow_dttm.date(),
            # "execution_date": execution_date,
            "logical_date": execution_date,
            "data_interval_start": data_interval_start,
            "data_interval_end": execution_date,
            "data_interval_start_dt": data_interval_start and data_interval_start.date(),
            "data_interval_end_dt": execution_date.date(),
        }
        return template_context

    @staticmethod
    def get_functions() -> dict[str, Callable]:
        return dict(jinja2_template_funcs_registry.items())

    def render_template(self, tmpl: T, context: dict) -> T:
        if isinstance(tmpl, str):
            result = self.env.from_string(tmpl).render(**context)
        elif isinstance(tmpl, (tuple, list)):
            result = [self.render_template(x, context) for x in tmpl]
        elif isinstance(tmpl, dict):
            result = {k: self.render_template(v, context) for k, v in tmpl.items()}
        else:
            # raise TypeError(f'Type {type(tmpl)} is not supported for templating')
            result = tmpl
        return result

    def extract_variables(self, tmpl: str) -> list[str]:
        ast = self.env.parse(tmpl)
        var_variables: list[str] = extract_vars_from_template_code(tmpl)
        variables: set[str] = meta.find_undeclared_variables(ast)
        variables.update(var_variables)

        # exclude assignments within if blocks.
        # e.g. for this template, the undefined variables are ['yesterday_ds']
        # WITHOUT 'dedup_order', which is a local variable defined by set
        #  {% if yesterday_ds <= '2020-09-25' %}
        #    {% set dedup_order = "snapshot_time ASC" %}
        #  {% else %}
        #    {% set dedup_order = "sell_count DESC NULLS LAST" %}
        #  {% endif %}
        assignments: list[str] = _jinja2_set_p.findall(tmpl)
        for vs in set(assignments):
            for v in vs.split(","):
                v = v.strip()
                if v in variables:
                    variables.remove(v)

        return sorted(variables)

    def _prepare_jinja_context(
        self, exist_variables: dict, execution_date: datetime.datetime, schedule_interval: str
    ) -> dict:
        template_var_dct = self.init_context(execution_date, schedule_interval)
        context = copy.copy(template_var_dct)  # shallow copy
        context.update(exist_variables)  # python code may use exist_variables
        for func_name, func in self.get_functions().items():
            context.setdefault(func_name, func)

        return context

    def render_variables(
        self, variables: dict[str, Any], execution_date: datetime.datetime, schedule_interval: str
    ) -> dict:
        """
        Renders variables in a dictionary using Jinja2 templating.

        This method processes each string value in the input dictionary,
        rendering it with Jinja2 if it contains template variables. The
        rendered values are then updated in the original dictionary.

        Args:
            variables: A dictionary of variables to render.
            execution_date: a given date that some date function can be used to calculate
            schedule_interval: A string representing the schedule interval (crontab expression).
        Returns:
            A dictionary with the same keys as the input, but with rendered values.
        """
        context = self._prepare_jinja_context(variables, execution_date, schedule_interval)
        update_dct = {}
        for name, val in variables.items():
            if not isinstance(val, str):
                # Process only the Jinja variables within the string.
                continue
            try:
                jinja_variables = self.extract_variables(val)
            except TemplateSyntaxError:
                # invalid jinja, leave it unrendered
                continue
            if not jinja_variables:
                continue

            rendered_val = self.render_template(val, context)
            if rendered_val != val:
                update_dct[name] = rendered_val
                context[name] = rendered_val
        variables.update(update_dct)
        return variables

    def extract_python_code_variable(
        self, python_code: str, exist_variables: dict, execution_date: datetime.datetime, schedule_interval: str
    ) -> dict:
        result = {}
        name_space = self._prepare_jinja_context(exist_variables, execution_date, schedule_interval)
        orig_name_space = copy.copy(name_space)
        rendered_code = self.render_template(python_code, name_space)

        compiled_code = compile(rendered_code, "", "exec")
        exec(compiled_code, name_space)

        for key2, value2 in name_space.items():
            if key2 == "__builtins__":
                continue
            if isinstance(value2, types.ModuleType):
                continue
            if inspect.isclass(value2):
                continue
            if key2 in orig_name_space and orig_name_space[key2] == value2:  # only return defined/updated var
                continue
            result[key2] = value2
        return result


if __name__ == "__main__":
    import doctest

    doctest.testmod()
