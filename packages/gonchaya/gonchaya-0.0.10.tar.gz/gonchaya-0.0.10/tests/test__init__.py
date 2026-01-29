from __future__ import annotations
import gonchaya
import pytest
from colorama import Fore, Back, Style
import random
import string
import itertools
import hashlib
import sys
import inspect
import typing

pp = pytest.param
is_fast = True
need_print = True

gonchaya.initialize_functions(['superfast', 'debug'])
from gonchaya import (  # noqa: E402, F401
    BCParamType,
    BCParamInstance,
    BCCommands,
    BCEnter,
    get_constructor_params,
    variable_type_check,
    make_instance,
)


# *****************   Вспомогательные функции   ********************
def sha(data):
    sha1 = hashlib.sha1()
    sha1.update(data.encode('utf-8'))
    return sha1.hexdigest()[:6]  # допускаем вероятность коллизии 10**-7
# ******************************************************************

def data_clearing_color_from_a_text():
    """
    Каждый кортеж содержит (текст_с_цветом, чистый_текст).
    """
    scenarios = []
    for category in ['Fore', 'Back', 'Style']:
        sym_in_category = {f'{category}.{k}':v 
                           for k, v in globals()[category].__dict__.items()
                           if not k.startswith('_')}
        for k, v in sym_in_category.items():
            scenarios.append(pytest.param(f'word1{v}word2',
                                          'word1word2',
                                          id=k))
    return scenarios

@pytest.mark.skipif(
    is_fast, 
    reason="Прямо сейчас тест не нужен (быстрая проверка).",
)
@pytest.mark.parametrize("colored_text, expected_text",
                         data_clearing_color_from_a_text())
def test_clearing_color_from_a_text(colored_text, expected_text):
    """
    Тестирует, что функция очистки цвета возвращает ожидаемый чистый текст.
    """
    actual_cleaned_text = gonchaya.clearing_color_from_a_text(colored_text)
    assert actual_cleaned_text == expected_text

def data_ljust_colored():
    pp = pytest.param
    d = f'1234{Fore.RED}5678'
    ru = f'абвг{Fore.RED}деёж'
    scenarios = [
        pp(d, 2, f'{d}', id='d:13:8:2'),
        pp(d, 6, f'{d}', id='d:13:8:6'),
        pp(d, 12, f'{d}    ', id='d:13:8:6'),
        pp(ru, 2, f'{ru}', id='ru:13:8:2'),
        pp(ru, 6, f'{ru}', id='ru:13:8:6'),
        pp(ru, 12, f'{ru}    ', id='ru:13:8:6')
        ]
    return scenarios

@pytest.mark.parametrize("colored_text, width, expected_text",
                         data_ljust_colored())
def test_ljust_colored(colored_text, width, expected_text):
    actual_text = gonchaya.ljust_colored(colored_text, width)
    assert actual_text == expected_text


#*******************  BCParamType   *********************



# --- Раздел 1: Тесты конструктора (используют параметризацию функции test__init__) ---
def TestBCParamType_init_scenarios():

    def fun_TestBCParamType():
        """Функция обратного вызова для получения вариантов для BCParamType."""
        return ['aaa', 'bbb', 'ccc']

    input_params = [
        {},
        {'name': 'Jfsa'},
        {'fun_get_variants': fun_TestBCParamType},
        {'execution_order':46},
        {'name': 'Jfsa', 'fun_get_variants': fun_TestBCParamType},
        {'fun_get_variants': fun_TestBCParamType, 'execution_order': 46},
        {'name': 'Jfsa', 'execution_order': 46},
        {'name': 'Jfsa', 'fun_get_variants': fun_TestBCParamType, 'execution_order': 46},
    ]
    param = []
    for dic in input_params:
        # fun_name = fun_input.__name__ if fun_input else 'None'
        scenario_id = 'BCParamType('
        if 'name' in dic:
            scenario_id += dic['name']
        if 'fun_get_variants' in dic:
            if scenario_id[-1] != '(':
                scenario_id += ', '
            fun_name = dic['fun_get_variants'].__name__ if inspect.isfunction(dic['fun_get_variants']) else None
            scenario_id += fun_name
        if 'execution_order' in dic:
            if scenario_id[-1] != '(':
                scenario_id += ', '
            scenario_id += f'execution_order={dic["execution_order"]}'
        scenario_id += ')'
        param_tuple = pp(dic, id=scenario_id)
        param.append(param_tuple)
    return param


# --- Раздел 2: Тесты использования методов (используют параметризованную фикстуру) ---

# TestBCParamType_fixture_variants = [
#    # name, variants, order
#    pp((None, ['qwe', 'qert', 'tett'], None), id='d*'),
#    pp((None, ['12d' , 'gsd'], 1), id='None1')
# ]

def TestBCParamType_fixture_variants():

    def generate_fixture_id(input_param):
        """Генерирует строку ID (comment) заранее."""
        comment = 'BCParam('
        if 'name' in input_param:
            comment += f"{input_param['name']}"
        if 'variants' in input_param:
            if len(comment) > 1: comment += ', '
            comment += f"{input_param['variants']}"
        if 'execution_order' in input_param:
            if len(comment) > 1: comment += ', '
            comment += f"order={input_param['execution_order']}"
        comment += ')'
        return comment

    TestBCParamType_InitParam_variants = [
        {'name':None, 'variants':['qwe', 'qert', 'tett'], 'execution_order':None},
        {'name':None, 'variants':['12d' , 'gsd'], 'execution_order':1},
        {'name':None, 'variants':['12d' , 'gsd', 'saq'], 'execution_order':1},
        {'name':None, 'variants':['яввар' , 'яdhr', ' яaq'], 'execution_order':1},
        {'name':None, 'variants':['.#fre' , 'sdfsd', 'saq'], 'execution_order':1},
        {'name':None, 'variants':['54757' , 'agasda', 'Gsaq'], 'execution_order':1},
        {'name':None, 'variants':['postgres' , 'django', 'mysql'], 'execution_order':1},
        {'name':None, 'variants':['ps' , 'ls', 'up', 'down'], 'execution_order':1},
    ]

    TestBCParamType_fixture_variants_params = []
    for variant_data in TestBCParamType_InitParam_variants:
        fixture_id= generate_fixture_id(variant_data)
        variant_data['fixture_id'] = fixture_id
        TestBCParamType_fixture_variants_params.append(
            pytest.param(variant_data, id=fixture_id)
        )
    return TestBCParamType_fixture_variants_params

def TestBCParamType__call__BCE():

    TestBCParamType___call__BCenters = [
        BCEnter('', 'q'),
        BCEnter('', 'E'),
        BCEnter('up', 'я'),
        BCEnter('do', 'я'),
        BCEnter('Gsaq', 'p'),
        BCEnter('Gsaq', ''),
        BCEnter('', 's'),
        BCEnter('up down', None),
    ]

    params = []
    for param in TestBCParamType___call__BCenters:
        params.append(
            pytest.param(param, id=param.__repr__())
        )
    return params

@pytest.fixture(params=TestBCParamType_fixture_variants())
def instance_BCParamType(request):
    """
    Параметризованная фикстура, которая создает экземпляр BCParamType
    с разными функциями обратного вызова (fun_get_variants).
    """
    input_param = request.param.copy()
    fixture_id = input_param['fixture_id']
    args = []
    kwargs = {}
    fun_name = None

    if 'name' in input_param:
        args.append(input_param['name'])

    if 'fun_get_variants' not in input_param:
        if 'variants' in input_param:
            def f():
                return input_param['variants']
            args.append(f)
            input_param['fun_get_variants'] = f
            f.variants = input_param['variants']
        else:
            # Если нет ни функции ни вариантов, то ничего и не передаем в 
            # конструктор.
            pass
    else:
        assert inspect.isfunction(input_param['fun_get_variants'])
        fun_name = input_param['fun_get_variants'].__name__

    if 'execution_order' in input_param:
        kwargs['execution_order'] = input_param['execution_order']

    instance = BCParamType(*args, **kwargs)
    instance.fixture_id = fixture_id
    return instance

data_for_call__ = {
    ("BCParam(None, ['qwe', 'qert', 'tett'], order=None)", "BCEnter([], 'q')"):{'qwe', 'qert'},
    ("BCParam(None, ['12d', 'gsd'], order=1)", "BCEnter([], 'q')"):set(),
    ("BCParam(None, ['qwe', 'qert', 'tett'], order=None)", "BCEnter([], 'E')"):set(),
    ("BCParam(None, ['12d', 'gsd'], order=1)", "BCEnter([], 'E')"):set(),
    ("BCParam(None, ['12d', 'gsd', 'saq'], order=1)", "BCEnter([], 'q')"):set(),
    ("BCParam(None, ['12d', 'gsd', 'saq'], order=1)", "BCEnter([], 'E')"):set(),
    ("BCParam(None, ['яввар', 'яdhr', ' яaq'], order=1)", "BCEnter([], 'q')"):set(),
    ("BCParam(None, ['яввар', 'яdhr', ' яaq'], order=1)", "BCEnter([], 'E')"):set(),
    ("BCParam(None, ['.#fre', 'sdfsd', 'saq'], order=1)", "BCEnter([], 'q')"):set(),
    ("BCParam(None, ['.#fre', 'sdfsd', 'saq'], order=1)", "BCEnter([], 'E')"):set(),
    ("BCParam(None, ['54757', 'agasda', 'Gsaq'], order=1)", "BCEnter([], 'q')"):set(),
    ("BCParam(None, ['54757', 'agasda', 'Gsaq'], order=1)", "BCEnter([], 'E')"):set(),
    ("BCParam(None, ['postgres', 'django', 'mysql'], order=1)", "BCEnter([], 'q')"):set(),
    ("BCParam(None, ['postgres', 'django', 'mysql'], order=1)", "BCEnter([], 'E')"):set(),
    ("BCParam(None, ['ps', 'ls', 'up', 'down'], order=1)", "BCEnter([], 'q')"):set(),
    ("BCParam(None, ['ps', 'ls', 'up', 'down'], order=1)", "BCEnter([], 'E')"):set(),
    ("BCParam(None, ['qwe', 'qert', 'tett'], order=None)", "BCEnter(['up'], 'я')"):set(),
    ("BCParam(None, ['qwe', 'qert', 'tett'], order=None)", "BCEnter(['do'], 'я')"):set(),
    ("BCParam(None, ['qwe', 'qert', 'tett'], order=None)", "BCEnter(['Gsaq'], 'p')"):set(),
    ("BCParam(None, ['qwe', 'qert', 'tett'], order=None)", "BCEnter(['Gsaq'], '')"):set(),
    ("BCParam(None, ['qwe', 'qert', 'tett'], order=None)", "BCEnter([], 's')"):set(),
    ("BCParam(None, ['12d', 'gsd'], order=1)", "BCEnter(['up'], 'я')"):set(),
    ("BCParam(None, ['12d', 'gsd'], order=1)", "BCEnter(['do'], 'я')"):set(),
    ("BCParam(None, ['12d', 'gsd'], order=1)", "BCEnter(['Gsaq'], 'p')"):set(),
    ("BCParam(None, ['12d', 'gsd'], order=1)", "BCEnter(['Gsaq'], '')"):set(),
    ("BCParam(None, ['12d', 'gsd'], order=1)", "BCEnter([], 's')"):set(),
    ("BCParam(None, ['12d', 'gsd', 'saq'], order=1)", "BCEnter(['up'], 'я')"):set(),
    ("BCParam(None, ['12d', 'gsd', 'saq'], order=1)", "BCEnter(['do'], 'я')"):set(),
    ("BCParam(None, ['12d', 'gsd', 'saq'], order=1)", "BCEnter(['Gsaq'], 'p')"):set(),
    ("BCParam(None, ['12d', 'gsd', 'saq'], order=1)", "BCEnter(['Gsaq'], '')"):set(),
    ("BCParam(None, ['12d', 'gsd', 'saq'], order=1)", "BCEnter([], 's')"):{'saq'},
    ("BCParam(None, ['яввар', 'яdhr', ' яaq'], order=1)", "BCEnter(['up'], 'я')"):{'яввар', 'яdhr'},
    ("BCParam(None, ['яввар', 'яdhr', ' яaq'], order=1)", "BCEnter(['do'], 'я')"):{'яввар', 'яdhr'},
    ("BCParam(None, ['яввар', 'яdhr', ' яaq'], order=1)", "BCEnter(['Gsaq'], 'p')"):set(),
    ("BCParam(None, ['яввар', 'яdhr', ' яaq'], order=1)", "BCEnter(['Gsaq'], '')"):set(),
    ("BCParam(None, ['яввар', 'яdhr', ' яaq'], order=1)", "BCEnter([], 's')"):set(),
    ("BCParam(None, ['.#fre', 'sdfsd', 'saq'], order=1)", "BCEnter(['up'], 'я')"):set(),
    ("BCParam(None, ['.#fre', 'sdfsd', 'saq'], order=1)", "BCEnter(['do'], 'я')"):set(),
    ("BCParam(None, ['.#fre', 'sdfsd', 'saq'], order=1)", "BCEnter(['Gsaq'], 'p')"):set(),
    ("BCParam(None, ['.#fre', 'sdfsd', 'saq'], order=1)", "BCEnter(['Gsaq'], '')"):set(),
    ("BCParam(None, ['.#fre', 'sdfsd', 'saq'], order=1)", "BCEnter([], 's')"):{'sdfsd', 'saq'},
    ("BCParam(None, ['54757', 'agasda', 'Gsaq'], order=1)", "BCEnter(['up'], 'я')"):set(),
    ("BCParam(None, ['54757', 'agasda', 'Gsaq'], order=1)", "BCEnter(['do'], 'я')"):set(),
    ("BCParam(None, ['54757', 'agasda', 'Gsaq'], order=1)", "BCEnter(['Gsaq'], 'p')"):{'Gsaq'},
    ("BCParam(None, ['54757', 'agasda', 'Gsaq'], order=1)", "BCEnter(['Gsaq'], '')"):{'Gsaq'},
    ("BCParam(None, ['54757', 'agasda', 'Gsaq'], order=1)", "BCEnter([], 's')"):set(),
    ("BCParam(None, ['postgres', 'django', 'mysql'], order=1)", "BCEnter(['up'], 'я')"):set(),
    ("BCParam(None, ['postgres', 'django', 'mysql'], order=1)", "BCEnter(['do'], 'я')"):set(),
    ("BCParam(None, ['postgres', 'django', 'mysql'], order=1)", "BCEnter(['Gsaq'], 'p')"):{'postgres'},
    ("BCParam(None, ['postgres', 'django', 'mysql'], order=1)", "BCEnter(['Gsaq'], '')"):set(),
    ("BCParam(None, ['postgres', 'django', 'mysql'], order=1)", "BCEnter([], 's')"):set(),
    ("BCParam(None, ['ps', 'ls', 'up', 'down'], order=1)", "BCEnter(['up'], 'я')"):{'up'},
    ("BCParam(None, ['ps', 'ls', 'up', 'down'], order=1)", "BCEnter(['do'], 'я')"):set(),
    ("BCParam(None, ['ps', 'ls', 'up', 'down'], order=1)", "BCEnter(['Gsaq'], 'p')"):{'ps'},
    ("BCParam(None, ['ps', 'ls', 'up', 'down'], order=1)", "BCEnter(['Gsaq'], '')"):set(),
    ("BCParam(None, ['ps', 'ls', 'up', 'down'], order=1)", "BCEnter([], 's')"):set(),
    ("BCParam(None, ['qwe', 'qert', 'tett'], order=None)", "BCEnter(['up', 'down'], 'None')"):set(),
    ("BCParam(None, ['12d', 'gsd'], order=1)", "BCEnter(['up', 'down'], 'None')"):set(),
    ("BCParam(None, ['12d', 'gsd', 'saq'], order=1)", "BCEnter(['up', 'down'], 'None')"):set(),
    ("BCParam(None, ['яввар', 'яdhr', ' яaq'], order=1)", "BCEnter(['up', 'down'], 'None')"):set(),
    ("BCParam(None, ['.#fre', 'sdfsd', 'saq'], order=1)", "BCEnter(['up', 'down'], 'None')"):set(),
    ("BCParam(None, ['54757', 'agasda', 'Gsaq'], order=1)", "BCEnter(['up', 'down'], 'None')"):set(),
    ("BCParam(None, ['postgres', 'django', 'mysql'], order=1)", "BCEnter(['up', 'down'], 'None')"):set(),
    ("BCParam(None, ['ps', 'ls', 'up', 'down'], order=1)", "BCEnter(['up', 'down'], 'None')"):{'up', 'down'},

}


class TestBCParamType:

    # Этот тест проверяет ТОЛЬКО конструктор, используя TestBCParamType_init_scenarios()
    @pytest.mark.parametrize("dic", TestBCParamType_init_scenarios())
    def test__init__(self, dic):
        instance = make_instance(BCParamType, dic)

        if 'name' in dic:
            len_name = len(dic['name'])
            self_name_startswith = dic['name']
            name = dic['name']
        else:
            len_name = 15
            self_name_startswith = 'ExampleBCPT_'
            name = None
        name_is_ok = (instance.name.startswith(self_name_startswith) and
            len(instance.name) == len_name)
        assert name_is_ok, f'self.name={instance.name}, input.name={name}, len={len_name}'

        if 'fun_get_variants' in  dic:
            fun_name = dic['fun_get_variants'].__name__
            expected_fun = dic['fun_get_variants']
            fun_is_ok = instance.fun_get_variants is expected_fun
        else:
            fun_name = 'None'
            expected_fun = BCParamType.functions._example_function
            fun_is_ok = instance.fun_get_variants is instance.functions._example_function
        assert fun_is_ok, f'self.fun={instance.fun_get_variants}, input.fun={fun_name}, expected.fun={expected_fun}'
 
        if 'execution_order' not in dic:
            order = 1
            input_order = None
        elif dic['execution_order'] is None:
            order = 1
            input_order = None
        else:
            order = dic['execution_order']
            input_order = dic['execution_order']
        order_is_ok = instance.execution_order == order
        assert order_is_ok, f'self.execution_order={instance.execution_order}, input.expected_order={input_order}, expected.execution_order{order}'

    @pytest.mark.parametrize("bce", TestBCParamType__call__BCE())
    def test__call__(self, instance_BCParamType, bce, new_data_collector, *args, **kwargs):
        """Проверка метода __call__(self, BCEnter)."""
#        print(f'\nДо reload: {instance_BCParamType=}')  # <- тут еще корректно
        # Фактически просто заполняем self.variants с помощью вызова
        # self.fun_get_variants(*args, **kwargs)
        BCParamType.reload()
#        print(f'\nПосле reload: {instance_BCParamType=}')  # <- тут еще корректно
        # Подготавиливаем объект-фильтр. В данном случае должны вернуться все
        # варианты из self.variants, начинающиеся с 'q'
        # bce = BCEnter('', 'q')
        # Применяем фильтр.
        out = instance_BCParamType(bce)
        key = (instance_BCParamType.fixture_id, bce.__repr__())
        if key not in data_for_call__:
            # используем сборщик в conftest.py
            if 'TestBCParamType:data_for_call__' not in new_data_collector:
                new_data_collector['TestBCParamType:data_for_call__'] = []
            # Вывод хука сразу можно копировать в data_for_call__
            comment_to_print = f"    {key}:{out},"
            new_data_collector['TestBCParamType:data_for_call__'
                ].append(comment_to_print)
        assert key in data_for_call__, 'Новые данные.'
        expected_result = data_for_call__[key]
        assert out == expected_result, f'init:{instance_BCParamType.fixture_id} out:{out} expected:{expected_result}'

