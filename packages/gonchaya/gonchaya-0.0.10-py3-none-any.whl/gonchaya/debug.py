"""Внутренние функции, требуемые для отладки модуля."""
# import os
import sys
import inspect
import typing
from typing import (                                               # noqa: F401
    Any,
    Dict,
    IO,
    Type,
    TypeVar,
    )
import collections.abc
from . import (  # noqa: E402
    GonchayaExeption,
    )

default: Dict[str, Any] = {
    'out': sys.stderr,
    'err': sys.stderr
}

# 1. Определяем Type Variable (переменную типа).
# Она служит "заполнителем" для конкретного типа класса,
# который будет передан во время вызова функции.
# bound=object означает, что T может быть любым классом.
T = TypeVar('T', bound=object)


def overwriting_default_values(**kwargs) -> None:
    """Перезапись умолчаний."""
    for k, v in kwargs.items():
        default[k] = v


def get_constructor_params(cls: type) -> Dict[str, inspect.Parameter]:
    """
    Возвращает словарь параметров конструктора класса.

    Ключи - имена параметров, значения - объекты Parameter.
    """
    if not isinstance(cls, type):
        raise TypeError('Ожидается объект типа type. Переданный объект имеет'
                        f' тип "{type(cls)}"', file=default['err'])

    init_method = getattr(cls, '__init__')
    if init_method is object.__init__:
        # Если конструктор не переопределен, параметров нет
        return {}

    # Получаем объект подписи (signature) метода __init__
    sig = inspect.signature(init_method)

    # Исключаем 'self' из параметров
    params = dict(sig.parameters)
    if 'self' in params:
        del params['self']

    return params


def variable_type_check(variable, target_type) -> bool:
    """
    Рекурсивно проверяет, соответствует ли переменная target_type.

    Включает поддержку List, Dict, Set, Tuple, Union и Optional.
    """
    # 1. Обработка базовых случаев (None, простые типы)
    if target_type is None:
        return variable is None

    if target_type is typing.Callable:
        # collections.abc.Callable охватывает функции, методы и лямбды [1]
        return isinstance(variable, collections.abc.Callable)

    if isinstance(target_type, type):
        return isinstance(variable, target_type)

    # Разбираем сложные типы с помощью typing API
    origin = typing.get_origin(target_type)
    args = typing.get_args(target_type)

    # случай для typing.Callable[..., T]
    if origin is collections.abc.Callable:
        # Здесь мы проверяем только то, что переменная является вызываемым
        # объектом. Проверка сигнатуры функции (аргументов и возвращаемого
        # типа) требует гораздо более сложной логики, что выходит за рамки
        # простой проверки isinstance.
        return isinstance(variable, collections.abc.Callable)

    # 3. Обработка Union и Optional
    if origin is typing.Union:
        for arg_type in args:
            if variable_type_check(variable, arg_type):
                return True
        return False

    # 4. Обработка коллекций
    if origin is list or origin is set:
        # Проверяем, что сама переменная является коллекцией нужного типа
        if not isinstance(variable, origin):
            return False
        # В List[T] и Set[T] аргумент типа item_type находится в args[0]
        item_type = args[0] if args else typing.Any
        # Рекурсивно проверяем каждый элемент
        for item in variable:
            if not variable_type_check(item, item_type):
                return False
        return True

    # 5. Обработка словарей
    if origin is dict:
        if not isinstance(variable, dict):
            return False
        # В Dict[K, V] args[0] это тип ключа, args[1] это тип значения
        key_type = args[0] if args else typing.Any
        value_type = args[1] if args else typing.Any
        # Рекурсивно проверяем каждый ключ и значение
        for key, value in variable.items():
            if ((not variable_type_check(key, key_type)) or (
                    not variable_type_check(value, value_type))):
                return False
        return True

    # 6. Обработка кортежей
    if origin is tuple:
        if not isinstance(variable, tuple):
            return False
        # Кортежи могут быть Tuple[T, ...] (все элементы одного типа) или
        # Tuple[T1, T2, ...]

        # Если последний аргумент — это Ellipsis (...), значит все элементы
        # одинаковы
        if len(args) == 2 and args[1] is Ellipsis:
            item_type = args[0]
            for item in variable:
                if not variable_type_check(item, item_type):
                    return False
        # Иначе, проверяем каждый элемент кортежа на соответствие его
        # позиции в args
        elif len(args) == len(variable):
            for item, item_type in zip(variable, args):
                if not variable_type_check(item, item_type):
                    return False
        else:
            # Кортеж не соответствует структуре типа по длине
            return False
        return True

    return False


def make_instance(my_class: Type[T],
                  potential_parameters: Dict[str, Any]) -> T:
    """На основе словаря параметров создает объект заданного класса."""
    assert inspect.isclass(my_class)
    assert isinstance(potential_parameters, dict)
    # Возвращает словарь параметров конструктора класса без self.
    # Ключи - имена параметров, значения - объекты Parameter.
    param = get_constructor_params(my_class)
    POSITIONAL_ONLY = {k: v for k, v in param.items()
                       if v.kind == v.POSITIONAL_ONLY}
    # Проверяем, принимает ли конструктор **kwargs (VAR_KEYWORD)
    KWARGS = any(p.kind == p.VAR_KEYWORD for p in param.values())
    if len(POSITIONAL_ONLY) != 0:
        raise GonchayaExeption('В конструкторе имеются чисто позиционные '
                               f'аргументы {POSITIONAL_ONLY}. Требуется '
                               'корректировка скрипта.')
    try:
        # get_type_hints умеет резолвить строки аннотаций в реальные типы
        type_hints = typing.get_type_hints(my_class.__init__)
    except Exception as e:
        raise GonchayaExeption('Внимание: Не удалось получить type hints для '
                               f'{my_class.__name__}.') from e
        # type_hints = {}
    kwargs = {}
    unknown = {}
    for key, value in potential_parameters.items():
        if key not in param:
            unknown[key] = value
            continue
        # annotation_str = param[key].annotation
        # Используем полученный объект типа, а не строковую аннотацию
        expected_type = type_hints.get(key)
        type_is_correct = variable_type_check(value, expected_type)
        if expected_type and not type_is_correct:
            print(f'Потенциальный параметр {key} имеет несовместимый тип '
                  f'(ожидается "{expected_type}", получено "{type(value)}")',
                  file=sys.stderr)
        kwargs[key] = value
    if KWARGS:
        obj = my_class(**kwargs, **unknown)
    else:
        obj = my_class(**kwargs)
    obj.init_param = {'kwargs': kwargs, 'unknown': unknown}
    return obj


def _print_views(myclass: Any, n: int = 2, *args,
                 file: IO[str] = sys.stderr, **kwargs) -> None:
    """Генерирует n экземпляров класса, и выводит str и repr на экран."""  # noqa: E501
    msg1 = f'\t\t{myclass.__name__}.repr'
    msg2 = f'\t\t{myclass.__name__}.str'
    msg3 = f'\t\t{myclass.__name__}._print_views_special'
    if hasattr(myclass, '_gen_test_items'):
        test_item = [myclass._gen_test_item() for _ in range(n)]
    else:
        try:
            test_item = [myclass(*args, **kwargs) for _ in range(n)]
        except BaseException as e:
            print(f'Ошибка при создании экземпляров {myclass.__name__}'
                  f': {e}\nПредполагаемые параметры:\n.'
                  f'{get_constructor_params(myclass)}')
            return
    print(msg1)
    for i in range(n):
        print(f'"{test_item[i].__repr__()}"')
    print(msg2)
    for i in range(n):
        print(f'"{test_item[i].__str__()}"')
    if hasattr(myclass, '_print_views_special'):
        print(msg3)
        for i in range(n):
            print(test_item[i]._print_views_special())
