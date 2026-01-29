"""Мои функции в модуле."""
# Делает аннотации "отложенными" (строковыми)
from __future__ import annotations
from datetime import datetime, timedelta  # , tzinfo, timezone
if 'start_time' not in globals():
    start_time: datetime = datetime.now() - timedelta(microseconds=1470)
__version__ = "0.00.03"
# import os                                                        # noqa: E402
import sys                                                         # noqa: E402
from typing import (                                         # noqa: E402, F401
    TYPE_CHECKING,
    NamedTuple,
    Any,
    List,
    Dict,
    Set,
    Type,
    IO,
    Callable,
    Iterator,
    Iterable,
    ClassVar,
    Protocol,
    )


_time_of_import = {}

default: Dict[str, Any] = {
    'out': sys.stderr,
    'err': sys.stderr
}


def time_since_application_launch(end=datetime.now()) -> str:
    """время_с_запуска_приложения."""
    dt = (end - start_time)
    return f'{dt.seconds + (dt.microseconds / 1000000):.3f}"'


class GonchayaExeption(Exception):
    """Исключения для модуля gonchaya."""

    pass


get_time_import: Any = None
is_parameter_a_list_of_class_X: Any = None
_print_views: Any = None
clearing_color_from_a_text: Any = None
ljust_colored: Any = None
generate_rnd_str: Any = None
BCEnter: Any = None
BCParamType: Any = None
BCParamInstance: Any = None
BCCommands: Any = None
BashCompletion: Any = None
_BashOut: Any = None
bash: Any = None
get_constructor_params: Any = None
variable_type_check: Any = None
make_instance: Any = None

StyleManager: Any = None
RefactorManager: Any = None
freeze_permanently: Any = None
skip_for_now: Any = None
cosmetic_only: Any = None
ready_for_restructure: Any = None
allow_optimization: Any = None
allow_architectural: Any = None
preserve_all_comments_as_anchors: Any = None
experimental_refactor: Any = None
waiting_for_dependencies: Any = None
analyze_module: Any = None
print_analysis_report: Any = None


def initialize_functions(modes: str | list[str]) -> None:
    """
    Инициализация.

    В зависимости от потребностей в скорости возвращает разное количество
    функций, что в свою очередь, влияет на скорость загрузки.
    """
    global is_parameter_a_list_of_class_X, _print_views, BCEnter
    global clearing_color_from_a_text, ljust_colored, generate_rnd_str
    global BCParamType, BCParamInstance, BCCommands, BashCompletion
    global bash, _BashOut
    global get_time_import
    global get_constructor_params
    global variable_type_check
    global make_instance

    if isinstance(modes, str):
        modes = [modes]
    for mode in modes:
        if mode in ['superfast', 'debug']:
            _ = datetime.now()
            # from . import superfast
            from .superfast import (
                is_parameter_a_list_of_class_X,
                clearing_color_from_a_text,
                ljust_colored,
                generate_rnd_str,
                BCEnter,
                BCParamType,
                BCParamInstance,
                BCCommands,
                BashCompletion,
                bash,
                _BashOut,
                get_time_import,
            )
            _time_of_import['superfast'] = (datetime.now() - _).microseconds
            del _

        if mode in ['debug']:
            from .debug import (
                _print_views,
                get_constructor_params,
                variable_type_check,
                make_instance,
            )
        if mode in ['refactor_phases']:
            from .refactor_phases import (
                StyleManager,
                RefactorManager,
                freeze_permanently,
                skip_for_now,
                cosmetic_only,
                ready_for_restructure,
                allow_optimization,
                allow_architectural,
                preserve_all_comments_as_anchors,
                experimental_refactor,
                waiting_for_dependencies,
                analyze_module,
                print_analysis_report,
            )


if __name__ == "__main__":
    # Код внутри этого блока выполняется только при прямом запуске файла
    print("Модуль запущен как основное приложение.")

_time_of_import['__init__'] = (datetime.now() - start_time).microseconds
