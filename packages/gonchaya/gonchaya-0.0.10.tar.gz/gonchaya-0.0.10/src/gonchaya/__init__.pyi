import inspect
import threading
from typing import Any, IO, TypeVar
from weakref import ReferenceType
from typing import Any, Callable, ClassVar, IO, Iterator, NamedTuple, Set, Tuple, Type
from collections import defaultdict
import weakref
from _typeshed import Incomplete
from datetime import datetime
from typing import Any, Dict

start_time: datetime
__version__: str
_time_of_import: Incomplete
default: Dict[str, Any]


def time_since_application_launch(end=...) -> str: ...


class GonchayaExeption(Exception):
    ...


def initialize_functions(modes: str | list[str]) -> None: ...


t0: Incomplete


def get_time_import(modules: list[str]) -> dict[str, int]: ...


is_bash_completion: Incomplete


def _format_colored_display_of_function(
    fun: Callable | None,
    color: str = '') -> str: ...


def is_parameter_a_list_of_class_X(
    params: list[Any],
    myclass: Type[Any],
    *,
    file: IO[str] | None = None) -> bool: ...


def clearing_color_from_a_text(text: str) -> str: ...
def ljust_colored(text: str, width: int = 0, fillchar: str = ' ') -> str: ...
def generate_rnd_str(length_: int = 10) -> str: ...


class BCEnter:
    cmd: str
    words: Incomplete
    unfinished_word: Incomplete
    raw_input_string: Incomplete

    def __init__(
        self,
        words: list[str] | str | None = None,
        unfinished_word: str | None = None) -> None: ...

    def load(self) -> None: ...
    def __repr__(self) -> str: ...
    def __str__(self) -> str: ...


class _BashOut(NamedTuple):
    cmd: str | list[str]
    stdout: str
    stderr: str
    screen: str
    returncode: int | None
    exception: BaseException | None
    comment: str | None = ...


def bash(
    cmd: str | list[str],
    comment: str | None = None,
    *args,
    shell: bool = False,
    stdout: bool = True,
    stderr: bool = True,
    **kwargs) -> _BashOut: ...


class IterableClassMeta_BCParamType(type):
    def __iter__(cls) -> Iterator[BCParamType]: ...
    def __getitem__(cls, index: int | slice |
                    str) -> BCParamType | list[BCParamType]: ...


class BCParamType(metaclass=IterableClassMeta_BCParamType):
    _color_name: str
    _color_variants: str
    _color_fun: str
    _max_workers: int
    _all_instances: ClassVar[weakref.WeakSet[BCParamType]]
    _class_lock: ClassVar[threading.Lock]
    def __iter__(self) -> Iterator[str]: ...
    @property
    def variants(self) -> list[str]: ...
    _variants: Incomplete
    fun_get_variants: Incomplete
    execution_order: Incomplete
    _reload_was_used: bool
    lock: Incomplete
    create_at: Incomplete
    name: Incomplete

    def __init__(
        self,
        name: str | None = None,
        fun_get_variants: Callable | None = None,
        *args,
        execution_order: int | None = 1,
        **kwargs) -> None: ...

    class functions:
        @staticmethod
        def _example_function(
            count_variants: int = 3,
            *args,
            len_suffix_variants: int = 3,
            **kwargs) -> list[str]: ...

        @staticmethod
        def get_all_service_names_for_all_profiles_in_a_docker_project(
            *args, **kwargs) -> list[str]: ...

    def __repr__(self) -> str: ...
    def __str__(self) -> str: ...
    @classmethod
    def reload(cls, *args, **kwargs) -> None: ...

    def __call__(self,
                 find: BCEnter | None = None) -> dict[str,
                                                      weakref.ReferenceType[BCParamType]]: ...


class IterableClassMeta_BCParamInstance(type):
    def __iter__(cls) -> Iterator[BCParamInstance]: ...
    def __getitem__(cls, index: int |
                    slice) -> BCParamInstance | list[BCParamInstance]: ...


class BCParamInstance(metaclass=IterableClassMeta_BCParamInstance):
    _all_instances: ClassVar[weakref.WeakSet[BCParamInstance]]
    _class_lock: ClassVar[threading.Lock]
    param: Incomplete
    required: Incomplete
    truncate: Incomplete
    multiply: Incomplete
    variants_is_uniq: Incomplete
    evoked_variants: Incomplete
    lock: Incomplete
    create_at: Incomplete
    name: Incomplete

    def __init__(
        self,
        name: str | None = None,
        param: BCParamType | None = None,
        *args,
        required: bool | None = True,
        truncate: bool | None = False,
        multiply: bool | None = False,
        variants_is_uniq: bool | None = True,
        **kwargs) -> None: ...

    class _NameComponents(NamedTuple):
        name: str
        prefix: str
        suffix: str

    def _get_name(self) -> _NameComponents: ...
    def __repr__(self) -> str: ...
    def __str__(self) -> str: ...
    def __call__(self, find: BCEnter | None = None) -> dict[str, None]: ...


class IterableClassMeta_BCCommands(type):
    def __iter__(cls) -> Iterator[BCCommands]: ...
    def __getitem__(
        cls, index: int | slice) -> Type[BCCommands] | list[BCCommands]: ...


class BCCommands(metaclass=IterableClassMeta_BCCommands):
    _color_cmd: str
    _color_pararm: str
    _color_comment: str
    _all_instances: ClassVar[weakref.WeakSet[BCCommands]]
    _class_lock: ClassVar[threading.Lock]
    current_command: None | None

    class _LenName(NamedTuple):
        name: int
        params: int
    params: Incomplete
    comment: Incomplete
    fun: Incomplete
    _len_str_name: Incomplete
    _len_str_params: Incomplete
    lock: Incomplete
    create_at: Incomplete
    name: Incomplete

    def __init__(
        self,
        name: str = ...,
        *args,
        params: list[BCParamInstance] | None = None,
        comment: str = '',
        fun: Callable | None = None,
        **kwargs) -> None: ...

    def _get_param_names(self, ljust: int = 0) -> str: ...
    def to_str(self, ljust_name: int = 0, ljust_param: int = 0) -> str: ...
    @classmethod
    def generate_aligned_command_help(cls, set_cmd: set[str]) -> str: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...
    def __getitem__(self, index: int | slice | str) -> BCParamInstance: ...

    def __call__(self,
                 find: BCEnter | None = None) -> defaultdict[str,
                                                             list[Tuple[ReferenceType[BCCommands],
                                                                        ReferenceType[BCParamInstance]]]]: ...


class BashCompletion:
    options: Set[str]
    def __init__(self) -> None: ...
    def parse(self, bce: BCEnter | None = None, *args, **kwargs): ...


default: dict[str, Any]
T = TypeVar('T', bound=object)


def overwriting_default_values(**kwargs) -> None: ...
def get_constructor_params(cls) -> dict[str, inspect.Parameter]: ...
def variable_type_check(variable, target_type) -> bool: ...


def make_instance(
    my_class: type[T], potential_parameters: dict[str, Any]) -> T: ...


def _print_views(
    myclass: Any,
    n: int = 2,
    *args,
    file: IO[str] = ...,
    **kwargs) -> None: ...
