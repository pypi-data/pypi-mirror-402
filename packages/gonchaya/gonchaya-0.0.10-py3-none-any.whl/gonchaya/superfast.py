"""Функции, требующие максимально быстрого времени реагирования."""
from __future__ import annotations  # [328, 293] us

# ЗАМЕЧАНИЕ ПО СТИЛЮ:
# 1. В этом модуле используются русские комментарии и Docstring-и. Причина:
# чисто англоязычные разработчики будут привлечены к проекту приблизительно
# никогда. В то же время рускоязычный интерфейс ускоряет отладку в несколько
# раз. Иначе говоря, прагматичная экономия ресурсов.
# 2. В генераторах списков, если они не находятся во внешних циклах, в
# качестве временного индекса используется "_". Это позволяет взгляду сходу
# определить индекс и не тратить времени на осмысление того, что именно там
# итерируется.
# 3. Временные индексы циклов, если они больше не нужны, удаляются явным
# образом оператором del. Это делаеется для того, чтобы, опять-таки, не
# держать в голове какой индекс где использовался. Это позволяет использовать
# это же имя в других циклах, не беспокоясь о несоблюдении типов.
# 4. Конкретно в этом файле у всех импортов указывается время, затрачиваемое на
# импорт. Это делается из-за жестких временных ограничений, чтобы легче было
# понять оставшийся бюджет.
from datetime import datetime, timedelta  # 1140 us
t0 = datetime.now() - timedelta(microseconds=1470)
from typing import (           # [342, 338] us + 8 us      # noqa: E402, F401
    TYPE_CHECKING,
    NamedTuple,
    Any,
    List,
    Dict,
    Set,
    Tuple,
    Type,
    IO,
    Callable,
    Iterator,
    Iterable,
    ClassVar,
    Protocol,
    TypeVar,
    Generic,
)
import importlib               # [287, 286] us                   # noqa: E402
import sys                     # [13, 26] us                     # noqa: E402
import os                      # [13, 12] us                     # noqa: E402
import copy                    # [15, 9] us                  # noqa: E402, F401
import re                      # [24, 7] us                      # noqa: E402
import inspect                 # [26, 8] us                      # noqa: E402
import weakref                 # [39] us                         # noqa: E402
from weakref import ref, ReferenceType                           # noqa: E402
import traceback               # [41] us                     # noqa: E402, F401
from collections import defaultdict                              # noqa: E402
from . import (  # noqa: E402
    GonchayaExeption,
    time_since_application_launch
    )
# module_load_time: dict[str, int] = {}

# ************ Сначала идут все элементы, работающие со временем **************


def get_time_import(modules: list[str]) -> dict[str, int]:  # [474, 472] us
    """Функция для вычисления времени, необходимого на импорт."""
    global_ = globals()
    import_time = {}
    for module in modules:
        t1 = datetime.now()
        global_[module] = importlib.import_module(module)
        t2 = datetime.now()
        import_time[module] = (t2 - t1).microseconds
    return import_time


# __2all__ = ['string', 'threading', 'logging', 'random', 'subprocess',
#            'colorama']
# Этот импорт виден ТОЛЬКО инструментам статического анализа (mypy)
# if TYPE_CHECKING:
if True:
    import string  # [996, 995] us
    import threading  # [2381, 2377] us
    import concurrent.futures  # [3443] us
#    import logging  # [4547, 4524] us
    import random  # [4621, 4319] us
    import subprocess  # [5875, 6623] us
    from colorama import Fore, Back, Style  # [6829, 6012] us
# else:
#    get_time_import(__2all__)
# t5 = datetime.now()
# print((t5 - t0).microseconds)
# t5-t0 = 28568

is_bash_completion = False if len(sys.argv) == 1 else (
    True if sys.argv[1] == 'bash_completion' else False)


# *****************************************************************************


def _format_colored_display_of_function(
        fun: Callable | None, color: str = '') -> str:
    """Возвращает подкрашеное имя функции и хеш ее адреса."""
    # Хеш нужен чтобы быстро, "на взгляд" видеть ссылки на одну и ту же
    # функцию.
    if not (callable(fun) or fun is None):
        raise TypeError('Ожидаемый тип: Callable | None. Передано: '
                        f'{type(fun)}.')
    if fun is None:
        return f"{color}None{Fore.RESET}"
    fun_module = fun.__module__
    fun_name = fun.__qualname__.split('.')
    # 1000003 и 4294967291 простые числа. Создаем хеш с равномерным
    # распределением и вероятностью коллизии ~ 10**-6 (5 hex знаков)
    hash_address = hex((id(fun) * 4294967291) % 1000003)[2:]
    return (f"{fun_module}:{'.'.join(fun_name[:-1] + [''])}"
            f"{color}{fun_name[-1]}{Fore.RESET} "
            f"{hash_address}")


def is_parameter_a_list_of_class_X(params: list[Any],
                                   myclass: Type[Any],  # Принимает класс
                                   # (например, int, str, CustomClass)
                                   *,
                                   file: IO[str] | None = None
                                   ) -> bool:
    """
    Проверяет, является ли параметр списком, состоящим только из экземпляров заданного класса.

    Функция возвращает True, если проверка пройдена, иначе False.
    """  # noqa: E501
    if not isinstance(params, list):
        if file:
            print('В качестве параметра должен быть передан тип list. '
                  f'Передано {type(params)}.', file=file)
        return False
    all_are_myclass = all(isinstance(par, myclass) for par in params)
    if not all_are_myclass:
        if file:
            print('Все элементы списка params должны быть экземплярами '
                  f' {myclass}. Передано: '
                  f'{[type(_) for _ in params]}.', file=file)
        return False
    return True


def clearing_color_from_a_text(text: str) -> str:
    """Очистка строки/сообщения от символов смены цвета/фона."""
    color_patterns: re.Pattern = re.compile("|".join(
        [i[0] + '\\' + i[1:] for i in Fore.__dict__.values()]
        + [i[0] + '\\' + i[1:] for i in Back.__dict__.values()]
        + [i[0] + '\\' + i[1:] for i in Style.__dict__.values()]
    ))
    return ''.join(color_patterns.split(text))


def ljust_colored(text: str, width: int = 0, fillchar: str = ' ') -> str:
    """Левосторонее выравнивание для текста с цветом."""
    # 1. Вычисляем сколько пробелов нужно добавить, основываясь на
    # визуальной длине
    display_len: int = len(clearing_color_from_a_text(text))

    if display_len >= width:
        return text

    # 2. Рассчитываем необходимое количество символов заполнения
    padding_len: int = width - display_len
    padding: str = fillchar * padding_len

    # 3. Добавляем символы заполнения к концу оригинальной строки
    # (с кодами цвета)
    return text + padding


def generate_rnd_str(length_: int = 10) -> str:
    """Генерация случайной строки, пригодной для имен в postgres."""
    # string.ascii_letters - все буквы (строчные и прописные)
    # string.digits - все цифры
    # string.punctuation - знаки препинания
    characters = string.ascii_letters + string.digits
    # Имя базы данных PostgreSQL должно начинаться с буквы
    rnd_str: str = random.choices(string.ascii_letters, k=1)[0]
    rnd_str += ''.join(random.choices(characters, k=length_ - 1))
    return rnd_str


class BCEnter:
    """Получение текущей строки автодополнения bash_completion."""

    def __init__(
        self,
        words: list[str] | str | None = None,  # готовые слова
        unfinished_word: str | None = None  # незавершенное слово
    ) -> None:
        """
        Конструктор с 2 режимами.

        Если words = None (а не ""), то запускается считывание из переменных
        окружения. Иначе задается в ручном режиме.
        """
        self.cmd: str = ''
        self.words: list[str] = []
        self.unfinished_word: str | None = None
        # Для восстановления того, что уже набрал пользователь.
        self.raw_input_string: str | None = None

        if words is None:
            self.load()
            return
        # Проверяем, что прилетело то, что ожидали.
        if isinstance(words, str):
            self.words = words.split()
        else:
            assert is_parameter_a_list_of_class_X(words, str)
            self.words = words
        # Если прилетит бармалей типа int - сгенерировать исключение.
        assert unfinished_word is None or isinstance(unfinished_word, str)
        self.unfinished_word = unfinished_word

    def load(self) -> None:
        """Реализация считывания из переменных окружения."""
        # Первичная инициализация в __init__
        self.raw_input_string = os.getenv('COMP_LINE')

        # 1. Проверки для отладки
        assert is_bash_completion, f'comp_line={self.raw_input_string}'
        # При попытке ручного запуска вместо str прилетает None
        assert isinstance(self.raw_input_string, str)

        # 2. Получение имени программы, от которого прилетел completion
        comp_line_split = self.raw_input_string.split()
        len_comp_line_split = len(comp_line_split)
        assert len_comp_line_split > 0
        self.cmd = comp_line_split[0]  # имя программы

        # 3. Получение списка слов, которые пользователь ввел
        if len_comp_line_split == 1:  # Пока ничего полезного не ввели
            pass
        elif self.raw_input_string[-1] != ' ':  # продолжается набор слова
            self.words = comp_line_split[1:-1]
            self.unfinished_word = comp_line_split[-1]
        else:  # все слова закончены (comp_line заканчивается пробелом)
            self.words = comp_line_split[1:]

    def __repr__(self):
        """Как это будет выглядеть в консоли."""
        return f"BCEnter({self.words}, '{self.unfinished_word}')"

    def __str__(self):
        """Как это будет выглядеть в команде print."""
        return f'({self.words}, {self.unfinished_word})'


class _BashOut(NamedTuple):
    """Структура, описывающая компоненты имени для отображения."""

    cmd: str | list[str]
    stdout: str
    stderr: str
    screen: str
    returncode: int | None
    exception: BaseException | None
    comment: str | None = None


def bash(cmd: str | list[str],
         comment: str | None = None,
         *args,
         shell=False,
         stdout=True,  # Надо ли выводить stdout на экран?
         stderr=True,  # Надо ли выводить stderr на экран?
         **kwargs,
         ) -> _BashOut:
    """Выполнение команды shell."""
    # todo: ⚠️ для shell=True организовать внутренний парсинг
    screen = []  # Вспомогательный список, который собирает и stdout и
    # stderr, т.е. полная копия того, что отображается на экране.

    class TeeOutput:
        """
        Пользовательский класс для обработки вывода.

        По своей сути - пользовательский буфер для выбранного потока.
        """

        def __init__(self,
                     screen_stream,  # ex: sys.stderr, sys.stdout
                     to_scr  # надо ли выводить на физический экран?
                     ):
            """Конструктор."""
            self.screen, self.values, self.to_scr = screen_stream, [], to_scr

        def write(self, message):
            """Функция, перегружающая стандартный вывод."""
            # nonlocal screen  # list и так доступен на запись
            if self.to_scr:
                # Запись на экран
                self.screen.write(message)
                self.screen.flush()  # Важно для немедленного отображения
                screen.append(message)  # логируем экран в переменную
            # Запись в переменную
            self.values.append(message)

        def flush(self):
            """Перегруженая функция сброса кеша записи."""
            # Метод flush() необходим для совместимости
            self.screen.flush()

    def read_output_live(stream, tee_object):
        """
        Чтение вывода из pipe и передачи его в пользовательский класс.

        Функция для перекачки данных из буфера чтения процесса в
        пользовательский буфер. Необходима для предотвращения блокировки из-за
        заполнения буфера вывода процесса.
        """
        for line in iter(stream.readline, ''):
            tee_object.write(line)
        # stream.close()

    # Создаем буферы, куда будут скидываться основные потоки
    tee_stdout = TeeOutput(sys.stdout, stdout)
    tee_stderr = TeeOutput(sys.stderr, stderr)

    try:
        # Запускаем процесс с Popen и перехватываем stdout и stderr в PIPE
        process = subprocess.Popen(
            cmd,
            *args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,  # Работаем со строками, а не байтами
            shell=shell,  # Используем shell=True для простых команд
            # (типа echo), если это необходимо
            **kwargs,
        )

        # Запускаем потоки для одновременного чтения stdout и stderr
        stdout_thread = threading.Thread(
            target=read_output_live, args=(process.stdout, tee_stdout))
        stderr_thread = threading.Thread(
            target=read_output_live, args=(process.stderr, tee_stderr))

        stdout_thread.start()
        stderr_thread.start()
        # Ожидаем завершения потоков
        stdout_thread.join()
        stderr_thread.join()
        # Ожидаем завершения процесса
        process.wait()

        # прямое логирование убрал отсюда, чтобы корректно работало
        # динамическое логирование
        return _BashOut(cmd=cmd,
                        stdout=''.join(tee_stdout.values),
                        stderr=''.join(tee_stderr.values),
                        screen=''.join(screen),
                        returncode=process.returncode,
                        exception=None,
                        comment=comment
                        )
    except BaseException as e:
        return _BashOut(cmd=cmd,
                        stdout=''.join(tee_stdout.values),
                        stderr=''.join(tee_stderr.values),
                        screen=''.join(screen),
                        returncode=None,
                        exception=e,
                        comment=comment
                        )


class IterableClassMeta_BCParamType(type):
    """Метакласс, делающий сам класс итерируемым."""

    def __iter__(   # type: ignore[misc]
            cls: Type[BCParamType]) -> Iterator[BCParamType]:
        """Итератор по самому классу, возвращающий все его экземпляры."""
        # До окончания итерации будет жива сильная ссылка, а значит данные
        # не будут удалены сборщиком мусора до окончания итерации.
        # Количество элементов ожидается меньше 20, поэтому не заботимся об
        # эффективности сортировки.
        with BCParamType._class_lock:
            actual_list = sorted([_ for _ in cls._all_instances if _],
                                 key=lambda x: x.create_at,
                                 reverse=False)
        yield from actual_list

    def __getitem__(cls: Type[BCParamType],
                    index: int | slice | str
                    ) -> BCParamType | list[BCParamType]:
        """Доступ по индексу (int/slice по порядку создания, str по имени)."""
        # Доступ по индексам/срезам планируется в основном из консолни
        # интерпретатора, и в основном только для того, чтобы посмотреть
        # первый и последние элементы.

        # Сортируем каждый раз, т.к. там weakref.WeakSet
        with BCParamType._class_lock:
            actual_list = sorted([_ for _ in cls._all_instances if _],
                                 key=lambda x: x.create_at,
                                 reverse=False)
        if isinstance(index, (int, slice)):
            return actual_list[index]
        # Если тип index вне допустимых типов - громко ворчим.
        if not isinstance(index, str):
            raise TypeError('Ожидаются типы int | slice | str. Переданный '
                            'аргумент имеет тип: {type(index).__name__}')
        # остался тип str. Аннотации не верим. По факту может прилететь что
        # угодно.
        for item in actual_list:
            if item.name == index:
                return item
        names_list = {_.name for _ in actual_list}
        raise IndexError(f'Доступные индексы: {names_list}. Был запрошен "'
                         f'{index}".')


class BCParamType(metaclass=IterableClassMeta_BCParamType):
    """
    Тип параметров команд автодополнения.

    Обертка для тяжелых по времени операций, которые можно запустить в
    несколько потоков. Один тип параметров может использовать много команд
    (например, список доступных контейнеров).
    """

    _color_name: str = Fore.GREEN
    _color_variants: str = Fore.YELLOW
    _color_fun: str = Fore.BLUE
    _max_workers: int = 3
    # Переменная класса для хранения слабых ссылок на все экземпляры
    _all_instances: ClassVar[weakref.WeakSet[BCParamType]
                             ] = weakref.WeakSet()
    _class_lock: ClassVar[threading.Lock] = threading.Lock()

    def __iter__(self) -> Iterator[str]:
        """Возможность итерировать варианты."""
        variants = self.variants
        yield from variants

    @property
    def variants(self) -> list[str]:
        """Геттер для variants."""
        with self.lock:
            variants = self._variants.copy()
        return variants

    def __init__(self,
                 name: str | None = None,
                 fun_get_variants: Callable | None = None,
                 *args,
                 # порядок выполнения: 1 если данные получаются напрямую от
                 # внешней функции, 2 - если для получения данных нужны резуль-
                 # таты, полученные от функций с порядком выполнения 1. И т.д.
                 execution_order: int | None = 1,
                 **kwargs) -> None:
        """Конструктор."""
        if name is None:
            name = (f'ExampleBCPT_{generate_rnd_str(3)}')
        if not isinstance(name, str):
            raise TypeError('Первый параметр должен быть типа str | None. '
                            f'Передано: {type(name).__name__}.')

        self._variants: list[str] = []

        if fun_get_variants is None:
            if 'variants' in kwargs:
                variants = kwargs['variants']
                assert is_parameter_a_list_of_class_X(variants, str)
                self._variants = variants.copy()
            else:
                fun_get_variants = BCParamType.functions._example_function
                # Можно прокинуть аргументы в функцию, но дефолтная функция
                # не умеет с ними работать.
                # fun_get_variants: Callable = (
                #    lambda *args, **kwargs: BCParamType._example_function(
                #        *args, **kwargs)),
        if not (inspect.isfunction(fun_get_variants) or
                fun_get_variants is None):
            raise ValueError('Второй параметр должен быть функцией. Переданный'
                             f' тип {type(fun_get_variants)}.\n'
                             f'fun={fun_get_variants}, inspect.isfunction='
                             f'{inspect.isfunction(fun_get_variants)}.')
        self.fun_get_variants: Callable = fun_get_variants

        if execution_order is None:
            execution_order = 1
        self.execution_order: int = execution_order

        self._reload_was_used: bool = False
        self.lock: threading.Lock = threading.Lock()
        self.create_at: float = datetime.now().timestamp()
        with BCParamType._class_lock:
            for item in BCParamType._all_instances:
                if name == item.name:
                    raise ValueError(
                        'Имя для экземпляра BCParamType должно быть уникальным'
                        f'. Текущее: "{name}", уже существующее: '
                        f'{BCParamType[name]}.')
            self.name: str = name
            BCParamType._all_instances.add(self)  # Добавляем себя в weakset

    class functions:
        """Различные предподготовленные функции, которые можно использовать."""

        # Блокировка экземпляра не требуется, т.к. нет обращения к атрибутам
        # экземпляра (гарантируется использованием @staticmethod)

        @staticmethod
        def _example_function(count_variants: int = 3,
                              *args,
                              len_suffix_variants: int = 3,
                              **kwargs) -> list[str]:
            """
            Тестовая функция-генератор, которая "придумывает" варианты.

            Генерирует count_variants вариантов (str, начинающиеся с
            "testParamType_").
            """
            return [f'ExampleVariant_{generate_rnd_str(len_suffix_variants)}'
                    for _ in range(count_variants)]

        @staticmethod
        def get_all_service_names_for_all_profiles_in_a_docker_project(
                *args, **kwargs) -> list[str]:
            """
            Возвращает список всех возможных контейнеров для текущего проекта.

            Включаются варианты со всеми возможными профилями.
            """
            cmd = ['sudo', 'docker', 'compose', '--profile', '*', 'config']
            res = bash(cmd, shell=False, stdout=False)
            assert res.returncode == 0
            out = [_ for _ in res.stdout.split('\n')
                   if not _.startswith(' ' * 3)]
            is_services = False
            services = []
            for _ in out:
                if _.startswith("  "):
                    if is_services:
                        services.append(_.strip()[:-1])
                elif _ == 'services:':
                    is_services = True
                else:
                    is_services = False
            return services

    def __repr__(self) -> str:
        """Как это будет выглядеть в консоли, при вызове экземпляра."""
        fun = _format_colored_display_of_function(self.fun_get_variants,
                                                  self._color_fun)

        # Используем прямой доступ к данным, т.к. нужен снимок 2 приватных
        # атрибутов в один и тот же момент.
        with self.lock:
            is_loaded = (':' if self._reload_was_used
                         else f'{Fore.RED}:{Fore.RESET}')
            variants = self.variants.copy()
        return (f'<BCParamType: {self._color_name}{self.name}{Fore.RESET}'
                f'{is_loaded}'
                f'{self._color_variants}{variants}{Fore.RESET}'
                f'{self._color_name}{self.execution_order}'
                f'{Fore.RESET} {fun}>')

    def __str__(self) -> str:
        """Как это будет выглядеть, при попытке отправить в print."""
        with self.lock:
            # Тут прямой доступ по той же причине, что и в __repr__
            is_loaded = (':' if self._reload_was_used
                         else f'{Fore.RED}:{Fore.RESET}')
            variants = self._variants.copy()
        return (f'{self._color_name}{self.name}{Fore.RESET}{is_loaded}'
                f'{self._color_variants}{variants}{Fore.RESET}')

    @classmethod
    def reload(cls, *args, **kwargs) -> None:
        """
        Асинхронно обновить варианты всех экземпляров.

        Используются функции для получения вариантов.
        """
        # Порядок выполнения: некоторые функции зависят от других. Например
        # потушеные сервисы = все - активные
        list_of_variants_of_execution_order = sorted({
            _.execution_order for _ in BCParamType})
        # потокобезопасно, т.к. на запись .execution_order используется только
        # в конструкторе.
        for exe_ord in list_of_variants_of_execution_order:
            with concurrent.futures.ThreadPoolExecutor(
                    max_workers=cls._max_workers) as executor:
                # КЛЮЧ: future
                # ЗНАЧЕНИЕ: целевой экземпляр (wrapper), который нужно обновить
                future_to_instance = {
                    executor.submit(
                        wrapper.fun_get_variants, *args, **kwargs): wrapper
                    for wrapper in BCParamType
                    if (wrapper.execution_order == exe_ord and
                        wrapper.fun_get_variants is not None)}

                # Итерация по завершенным фьючерсам
                for future in concurrent.futures.as_completed(
                        future_to_instance):
                    # Получаем нужный экземпляр из словаря по завершенному
                    # future
                    instance_to_update = future_to_instance[future]
                    try:
                        # Получаем результат из потока
                        new_variants = future.result()
                        with instance_to_update.lock:
                            instance_to_update._variants = new_variants
                            instance_to_update._reload_was_used = True
                    except BaseException as e:
                        raise GonchayaExeption(
                            'Ошибка при обновлении '
                            f'{instance_to_update.name}.') from e
                        #      f'{traceback.format_exc()}')

    def __call__(self,
                 find: BCEnter | None = None
                 ) -> dict[str, weakref.ReferenceType[BCParamType]]:
        """Возвращает variants которые попадают под шаблон."""
        variants = self.variants
        self_weak_ref = ref(self)
        if find is None:
            return {_: self_weak_ref for _ in variants}
        if not isinstance(find, BCEnter):
            raise TypeError(f'Ожидается тип BCEnter. Передано {type(find)}.')
        finished = {_ for _ in find.words if _ in variants}
        if find.unfinished_word:
            unfinished = {_ for _ in variants
                          if _.startswith(find.unfinished_word)}
        else:
            if find.words:
                # Если есть завершенные слова, пустые незавершенные подавляем
                unfinished = set()
            else:
                # Иначе отдаем весь список
                unfinished = set(variants)
        return {_: self_weak_ref for _ in (finished | unfinished)}

    # дублирующийся функционал.
    # def items(self,
    #          find: BCEnter | None = None
    #          ) -> dict[str, weakref.ReferenceType[BCParamType]]:
    #    """Возвращает словарь {вариант: self_weak_ref}."""
    #    # Создаем слабую ссылку на текущий экземпляр (self)
    #    self_weak_ref = weakref.ref(self)
    #    variants = self.variants
    #    if find is None:
    #        result_dict = {variant: self_weak_ref for variant in variants}
    #    else:
    #        result_dict = {variant: self_weak_ref for variant in self(find)}
    #    return result_dict


class IterableClassMeta_BCParamInstance(type):
    """Метакласс, делающий сам класс итерируемым."""

    def __iter__(   # type: ignore[misc]
            cls: Type[BCParamInstance]) -> Iterator[BCParamInstance]:
        """Итератор по самому классу, возвращающий все его экземпляры."""
        # Количество элементов ожидается меньше 20, поэтому не заботимся об
        # эффективности сортировки.
        with BCParamInstance._class_lock:
            actual_list = sorted([_ for _ in cls._all_instances if _],
                                 key=lambda x: x.create_at,
                                 reverse=False)
        yield from actual_list

    def __getitem__(cls: Type[BCParamInstance],
                    index: int | slice
                    ) -> BCParamInstance | list[BCParamInstance]:
        """Доступ по индексу (int/slice по порядку создания, str по имени)."""
        # Доступ по индексам/срезам планируется в основном из консолни
        # интерпретатора, и в основном только для того, чтобы посмотреть
        # первый и последние элементы.

        # Сортируем каждый раз, т.к. там weakref.WeakSet
        with BCParamInstance._class_lock:
            actual_list = sorted([_ for _ in cls._all_instances if _],
                                 key=lambda x: x.create_at,
                                 reverse=False)
        if isinstance(index, (int, slice)):
            return actual_list[index]
        # Если тип index вне допустимых типов - громко ворчим.
        if not isinstance(index, str):
            raise TypeError('Ожидаются типы int | slice | str. Переданный '
                            'аргумент имеет тип: {type(index).__name__}')
        # остался тип str. Аннотации не верим. По факту может прилететь что
        # угодно.
        for item in actual_list:
            if item.name == index:
                return item
        names_list = {_.name for _ in actual_list}
        raise IndexError(f'Доступные индексы: {names_list}. Был запрошен "'
                         f'{index}".')


class BCParamInstance(metaclass=IterableClassMeta_BCParamInstance):
    """Экземпляр параметров для конкретной команды."""

    # Для каждой команды тип параметров оборачивается в доп. параметры.
    # Например, обработка доступных котнейнеров Docker. Сам список получается
    # единоразово в классе BCParamType, тут же указываем, что, например,
    # существует вариант для некой команды ps, такой что: он может не
    # указываться вовсе (тогда выдаем сводку по всем контейнерам), а может
    # указываться 1, 2 или больше вариантов. А вот для команды  heartbeat имя
    # контейнера обязательно и единственно.

    _all_instances: ClassVar[weakref.WeakSet[BCParamInstance]
                             ] = weakref.WeakSet()
    _class_lock: ClassVar[threading.Lock] = threading.Lock()

    def __init__(self,
                 name: str | None = None,
                 param: BCParamType | None = None,
                 *args,
                 required: bool | None = True,  # обязателен ли?
                 truncate: bool | None = False,  # усечение валидно?
                 multiply: bool | None = False,
                 variants_is_uniq: bool | None = True,
                 **kwargs
                 ) -> None:
        """Конструктор."""
        # название
        if name is None:
            name = (f'ExampleTCPI_{generate_rnd_str(3)}')
        if not isinstance(name, str):
            raise TypeError('Первый параметр должен быть типа str | None. '
                            f'Передано: {type(name).__name__}.')

        # тип параметра
        if param is None:
            param = BCParamType()
        if not isinstance(param, BCParamType):
            raise TypeError(
                'Второй параметр должен быть экземпляром класса BCParamType. '
                f'Передано {type(param)}.')
        self.param: BCParamType = param
        # обязательность параметра
        self.required: bool = (
            bool(random.getrandbits(1)) if required is None else required)
        # У этого параметра на всегда работает усечение
        self.truncate: bool = (
            bool(random.getrandbits(1)) if truncate is None else truncate)
        self.multiply: bool = (
            bool(random.getrandbits(1)) if multiply is None else multiply)
        self.variants_is_uniq: bool = (bool(random.getrandbits(
            1)) if variants_is_uniq is None else variants_is_uniq)
        # После разбора командной строки тут будут выбранные варианты.
        # Логичнее зарезервировать место прямо тут, чем использовать внешние
        # переменные где-то еще.
        self.evoked_variants: list[str] | None = None
        self.lock: threading.Lock = threading.Lock()
        self.create_at: float = datetime.now().timestamp()
        with BCParamInstance._class_lock:
            for item in BCParamInstance._all_instances:
                if name == item.name:
                    raise ValueError(
                        'Имя для экземпляра BCParamInstance должно быть '
                        f'уникальным. Текущее: "{name}", уже существующее: '
                        f'{BCParamInstance[name]}.')
            self.name = name
            BCParamInstance._all_instances.add(self)

    class _NameComponents(NamedTuple):
        """Структура, описывающая компоненты имени для отображения.

        На текущий момент подразумевается для использования в синтаксисе
        [.name] для обозначения обязательности/возможности усечения.
        """

        name: str
        prefix: str
        suffix: str

    def _get_name(self) -> _NameComponents:
        """Возвращает 3 компонента имени: само имя, и пре/суфиксы, для визуального отображения."""  # noqa: E501
        if self.required:
            prefix = ''
            suffix = ''
        else:
            prefix = '['
            suffix = ']'
        if self.variants_is_uniq:
            prefix += '!'
        if self.multiply:
            prefix += '*'
        if self.truncate:
            prefix += '.'
        ret = BCParamInstance._NameComponents(self.name, prefix, suffix)
        return ret

    def __repr__(self) -> str:
        """Как это будет выглядеть в консоли, при вызове экземпляра."""
        name = self._get_name()
        fun = _format_colored_display_of_function(self.param.fun_get_variants,
                                                  BCParamType._color_fun)
        with self.lock:
            is_loaded = (':' if self.param._reload_was_used
                         else f'{Fore.RED}:{Fore.RESET}')
            variants = self.param._variants.copy()
        return (
            f'<BCParamInstance: {name.prefix}'
            f'{BCParamType._color_name}{name.name}{Fore.RESET}{name.suffix} '
            f'{BCParamType._color_fun}{self.param.name}{Fore.RESET}'
            f'{is_loaded}'
            f'{BCParamType._color_variants}{variants}{Fore.RESET} '
            f'{fun}>')

    def __str__(self) -> str:
        """Как это будет выглядеть, при попытке отправить в print."""
        name = self._get_name()
        with self.lock:
            is_loaded = (':' if self.param._reload_was_used
                         else f'{Fore.RED}:{Fore.RESET}')
            variants = self.param._variants.copy()
        return (
            f'{name.prefix}{BCParamType._color_name}'
            f'{name.name}{Fore.RESET}{name.suffix}{is_loaded}'
            f'{BCParamType._color_variants}{variants}{Fore.RESET}'
        )

    def __call__(self, find: BCEnter | None = None
                 ) -> dict[str, ReferenceType(BCParamInstance)]:
        """Возвращает variants которые попадают под шаблон."""
        self_weak_ref = ref(self)
        variants = self.param.variants
        if find is None:
            return {_: self_weak_ref for _ in variants}
        if not isinstance(find, BCEnter):
            raise TypeError(f'Ожидается тип BCEnter. Передано {type(find)}.')
        result = set()
        if self.required and len(
                find.words) == 0 and find.unfinished_word == '':
            result |= {''}
        if self.truncate:
            all_BCEnter = [BCEnter('', _) for _ in (
                find.words + [find.unfinished_word])]
            for _ in all_BCEnter:
                result |= set(self.param(_))
        else:
            result |= set(self.param(find))
        if len(result) == 0:
            return {}
        return {_: self_weak_ref for _ in result}

    # к удалению. Функционал дублирует __call__
    # def items(self,
    #          find: BCEnter | None = None
    #          ) -> dict[str, weakref.ReferenceType[BCParamInstance]]:
    #    """Возвращает словарь {вариант: self_weak_ref}."""
    #    # Создаем слабую ссылку на текущий экземпляр (self)
    #    self_weak_ref = weakref.ref(self)
    #
    #    if find is None:
    #        result_dict = {variant: self_weak_ref
    #                       for variant in self.param.variants}
    #    else:
    #        result_dict = {variant: self_weak_ref
    #                       for variant in self(find)}
    #    return result_dict


class IterableClassMeta_BCCommands(type):
    """Метакласс, делающий сам класс итерируемым."""

    def __iter__(  # type: ignore[misc]
            cls: Type[BCCommands]) -> Iterator[BCCommands]:
        """Итератор по самому классу, возвращающий все его экземпляры."""
        # Количество элементов ожидается меньше 20, поэтому не заботимся об
        # эффективности сортировки.
        with BCCommands._class_lock:
            actual_list = sorted([_ for _ in cls._all_instances if _],
                                 key=lambda x: x.create_at,
                                 reverse=False)
        yield from actual_list

    def __getitem__(cls: Type[BCCommands],
                    index: int | slice
                    ) -> Type[BCCommands] | list[BCCommands]:
        """Доступ по индексу."""
        # Доступ по индексам/срезам планируется в основном из консолни
        # интерпретатора, и в основном только для того, чтобы посмотреть
        # первый и последние элементы.

        # Сортируем каждый раз, т.к. там weakref.WeakSet
        with BCCommands._class_lock:
            actual_list = sorted([_ for _ in cls._all_instances if _],
                                 key=lambda x: x.create_at,
                                 reverse=False)
        if isinstance(index, (int, slice)):
            return actual_list[index]
        # Если тип index вне допустимых типов - громко ворчим.
        if not isinstance(index, str):
            raise TypeError('Ожидаются типы int | slice | str. Переданный '
                            'аргумент имеет тип: {type(index).__name__}')
        # остался тип str. Аннотации не верим. По факту может прилететь что
        # угодно.
        for item in actual_list:
            if item.name == index:
                return item
        names_list = {_.name for _ in actual_list}
        raise IndexError(f'Доступные индексы: {names_list}. Был запрошен "'
                         f'{index}".')


class BCCommands(metaclass=IterableClassMeta_BCCommands):
    """
    Описание того, какой может быть команда.

    Может содержать несколько параметров, которые могут быть необязательными.
    """

    _color_cmd: str = BCParamType._color_name
    _color_pararm: str = BCParamType._color_variants
    _color_comment: str = Fore.RESET
    _all_instances: ClassVar[weakref.WeakSet[BCCommands]
                             ] = weakref.WeakSet()
    _class_lock: ClassVar[threading.Lock] = threading.Lock()
    # После парсинга командной строки тут окажется нужная команда
    current_command: ReferenceType(BCCommands) | None = None

    class _LenName(NamedTuple):
        """Структура, описывающая длинну имени и параметров."""

        name: int
        params: int

    def __init__(self,
                 name: str = (f'ExampleBCC_{generate_rnd_str(3)}'),
                 *args,
                 params: list[BCParamInstance] | None = None,
                 comment: str = '',
                 fun: Callable | None = None,  # резерв под функцию, которая
                 # собственно комманду выполнит.
                 **kwargs) -> None:
        """Конструктор."""
        if name is None:
            name = (f'ExampleTCC_{generate_rnd_str(3)}')
        if not isinstance(name, str):
            raise TypeError('Первый параметр должен быть типа str | None. '
                            f'Передано: {type(name).__name__}.')

        # Проверяем, что все элементы params - элементы _bc_param_instance
        if params is None:
            params = [BCParamInstance(required=None, truncate=None)
                      for _ in range(random.randint(1, 3))]
        assert is_parameter_a_list_of_class_X(params,
                                              BCParamInstance,
                                              file=sys.stderr)
        self.params: list[BCParamInstance] = params
        self.comment: str = comment
        self.fun: Callable | None = fun
        # визуальная длинна имени и параметров. Т.е. без цветовых кодов.
        self._len_str_name = len(name)
        self._len_str_params = len(
            clearing_color_from_a_text(self._get_param_names()))
        self.lock: threading.Lock = threading.Lock()
        self.create_at: float = datetime.now().timestamp()
        with BCCommands._class_lock:
            for item in BCCommands._all_instances:
                if name == item.name:
                    raise ValueError(
                        'Имя для экземпляра BCParamInstance должно быть '
                        f'уникальным. Текущее: "{name}", уже существующее: '
                        f'{BCParamInstance[name]}.')
            self.name = name
            BCCommands._all_instances.add(self)

    def _get_param_names(self, ljust: int = 0) -> str:
        """Возвращает выровненный раскрашеный список имен параметров."""
        # Получаем по 3 компонента в объекте [name, prefix, suff]
        raw_names = [_._get_name() for _ in self.params]
        str_names = ' '.join(
            [f'{prefix}{self._color_pararm}{name}{Fore.RESET}{suffix}'
             for name, prefix, suffix in raw_names])
        return ljust_colored(str_names, ljust)

    def to_str(self, ljust_name: int = 0, ljust_param: int = 0) -> str:
        """
        Возвращает описание команды, с вставленными отступами.

        Отличие от __str__: для нескольких комманд устанавливает единообразный
        отступ.
        """
        return (f'{self._color_cmd}{self.name.ljust(ljust_name)}{Fore.RESET} '
                f'{ljust_colored(self._get_param_names(), ljust_param)} '
                f'{self._color_comment}{self.comment}{Fore.RESET}')

    @classmethod
    def generate_aligned_command_help(cls, set_cmd: set[str]) -> str:
        """Возвращает выровненный текст описания для нескольких команд."""
        with cls._class_lock:
            commands_list = [_ for _ in cls._all_instances
                             if _.name in set_cmd]
        if not commands_list:
            return ''
        len_tup = [(_._len_str_name, _._len_str_params) for _ in commands_list]
        max_name, max_params = tuple(max(_) for _ in zip(*len_tup))
        result = [_.to_str(max_name, max_params) for _ in commands_list]
        return '\n'.join(result)

    def __str__(self) -> str:
        """Возвращает описание команды."""
        return self.to_str()

    def __repr__(self) -> str:
        """Как экземпляр будет выглядеть в консоли."""
        fun = _format_colored_display_of_function(self.fun,
                                                  BCParamType._color_fun)
        return ('<BCCommands: '
                f'{self._color_cmd}{self.name}{Fore.RESET}, '
                f'{self._get_param_names()}, '
                f'{self._color_comment}{self.comment}{Fore.RESET}, '
                f'{fun}'
                '>')

    def __getitem__(self,
                    index: int | slice | str) -> BCParamInstance:
        """Доступ по индексу к экземпляру параметров."""
        if isinstance(index, (int, slice)):
            return self.params[index]
        if isinstance(index, str):
            instance_names = {_.name: _ for _ in self.params}
            if index in instance_names:
                return instance_names[index]
            else:
                raise IndexError(f'Доступные индексы: {instance_names.keys()}.'
                                 f'Был запрошен "{index}".')
        # Не доверяем аннотации
        raise TypeError('Ожидаются типы int | slice | str. Переданный '
                        f'аргумент имеет тип: {type(index).__name__}')

    def __call__(self, find: BCEnter | None = None) -> (
            defaultdict[str, list[Tuple[ReferenceType[BCCommands],
                                        ReferenceType[BCParamInstance]]]]):
        """Возвращает variants которые попадают под шаблон."""
        self_weak_ref = ref(self)
        if find is None:
            find = BCEnter('', None)
        if not isinstance(find, BCEnter):
            raise TypeError(f'Ожидается тип BCEnter. Передано {type(find)}.')
        Find = [_ for param in self.params if (_ := param(find))]
        # В Find теперь словари {key:param}
        variants = defaultdict(list)
        for param in Find:
            for k, ParamInstance_weak_ref in param.items():
                variants[k].append((self_weak_ref, ParamInstance_weak_ref))
        return variants


class BashCompletion:
    """Класс, группирующий все возможные варианты команд и их параметров."""

    options: Set[str] = {'-i', '-force', '-info'}

    def __init__(self):
        """Конструктор."""
        pass

    def parse(self, bce: BCEnter | None = None, *args, **kwargs):
        """Парсинг командной строки."""
        mode = 'bash_completion'
        all_options: Set[str] = {'-i'}
        if bce is None:
            bce = BCEnter()  # то, что ввел пользователь
        words, uf_word = bce.words.copy(), bce.unfinished_word
        # Если ввели '-', то в выводе дополнительно будем отображать опции.
        print_options = '-' in {_[0] for _ in words + [uf_word] if bool(_)}
        # Получаем актуальное значение всех вариантов параметров
        BCParamType.reload()
        all_param_variants = set().union(*[_ for _ in BCParamType])
        all_commands = {_.name for _ in BCCommands}
        # В уголке отображаем время обслуживания запроса. Для комфортной работы
        # не должно превышать 0,3". Текущий бюджет с анализом профилей докера
        # 0.009"
        print(f'\t\t\t{Fore.RED}{time_since_application_launch()}{Fore.RESET}',
              file=sys.stderr)

        # Вариант: еще ничего не ввели. Выводим микросправку по всем командам
        # и все варианты значений параметров.
        if not words and not uf_word:
            if mode == 'bash_completion':
                print(BCCommands.generate_aligned_command_help(all_commands),
                      file=sys.stderr)
                _ = all_commands | all_param_variants
                if print_options:
                    _ |= all_options
                print('\n'.join(_))
                print(bce.raw_input_string, file=sys.stderr, end='')
                exit(0)
            if mode == 'command':
                BCCommands.current_command = {'cmd': 'usage',
                                              'param': [],
                                              'options': [],
                                              'unparsed_words': []}
                return

        commands_reg = BCParamType(  # регистрируем тип: команды
            'commands', variants=[_.name for _ in BCCommands])
        commands_filtred_by_name = commands_reg(bce)
        f_comm = [_ for _ in commands_filtred_by_name if _ in words]
        uf_comm = [_ for _ in commands_filtred_by_name if _ not in words]

        # Вариант: как минимум одно из слов было распознано как команда.
        # Выбираем из списка слов, распознаных как команды, первое, выводим
        # микросправку по нему, и из всех вариантов параметров оставляем
        # только принадлежащие конкретно этой команде.
        if f_comm:
            current_command = [_ for _ in BCCommands if _.name == f_comm[0]][0]
            # Остальные оставляем на тот случай, если значение параметра
            # совпадает с именем команды. Если и первое совпадает - то
            # директивно считаем, что в этом случае это команда, а значение
            # идет после команды.
            if mode == 'bash_completion':
                print(f'{current_command}', file=sys.stderr)
            elif mode == 'command':
                # Пока только декларируем. Callback в основном модуле еще не
                # готов.
                BCCommands.current_command['cmd'] = current_command.name
            words.remove(f_comm[0])
            bce_updated = BCEnter(words, uf_word)
            # получаем варианты параметров конкретно для нашей команды
            available_params = current_command(bce_updated)

            # Очистку структуры отключил. Пока вроде не нужно.
            if False:
                # Удаляем из полученного словаря ставшей ненужной информацию о
                # команде
                reformatted_params = {}
                for param, v_list in available_params.items():
                    reformatted_params[param] = []
                    for tuple_weakref in v_list:
                        if tuple_weakref[0]() is not current_command:
                            raise GonchayaExeption(
                                'Слабая ссылка на команду указывает не на нашу'
                                ' команду.')
                            # Если такое приключится - будем разбираться потом,
                            # что произошло. В нормальной ситуации такого быть
                            # не должно.
                        reformatted_params[param].append(tuple_weakref[1])

            params_candidate = available_params.keys()
            # Пока список, чтобы сохранить порядок следования
            recognized_params = [_ for _ in words if _ in params_candidate]
            # Кажется не должно быть ситуации, чтобы один и тот же параметр
            # требовал бы указания дважды. Поэтому вырезаем. Возможно потом
            # придется скорректировать логику.
            for _ in recognized_params:
                words.remove(_)

            # итерируемся по отсортированным по времени значениям
            # BCParamItems для выбранной команды.
            remaining_recognized_parameters = recognized_params.copy()
            for bcpi in current_command:
                cut_out_param_list: list[str] = [
                    _ for _ in remaining_recognized_parameters if _ in bcpi]
                if cut_out_param_list:
                    cut_out_param: str | None = cut_out_param_list[0]
                    remaining_recognized_parameters.remove(cut_out_param)
                else:
                    cut_out_param: str | None = None
                BCCommands.current_command.append(cut_out_param)
            result_params = set(params_candidate) - set(recognized_params)
            options = {_ for _ in all_options if _ not in words}
            not_recognized = result_params
            if print_options:
                not_recognized |= options
            ufw = '' if uf_word is None else uf_word
            _ = {_ for _ in not_recognized if _.startswith(ufw)}
            print(_, file=sys.stderr)
            print('\n'.join(_))
            print(bce.raw_input_string, file=sys.stderr, end='')
            exit(0)
            # print(f'{recognized_parameters=}', file=sys.stderr)

        param_filtred_by_name = defaultdict(list)
        uniq_comm_in_filtred_type = set()
        uniq_item_in_filtred_type = set()

        # получаем обратный словарь вариант_в_типе -> где используется
        for command_name in [_(bce) for _ in BCCommands]:
            for k, v_list in command_name.items():
                actual_v_list = [
                    (CMD, PI) for weak_cmd_ref, weak_pi_ref in v_list
                    if (CMD := weak_cmd_ref()) and (PI := weak_pi_ref())]
                param_filtred_by_name[k].extend(actual_v_list)
                cmd, pi = map(set, zip(*actual_v_list))
                uniq_comm_in_filtred_type |= cmd
                uniq_item_in_filtred_type |= pi
        for k, l in param_filtred_by_name.items():
            print(f'param:{k}:', file=sys.stderr)
            for v in l:
                print(f'\t{v}', file=sys.stderr)
        all_lists = [all_options, all_param_variants, all_commands, f_comm,
                     uf_comm, uniq_comm_in_filtred_type,
                     uniq_item_in_filtred_type, param_filtred_by_name.keys()]
        list_names = ['all_options', 'all_param_variants', 'all_commands',
                      'f_comm', 'uf_comm', 'uniq_comm_in_filtred_type',
                      'uniq_item_in_filtred_type', 'param_filtred_by_name']
        word_to_lists_map = defaultdict(set)

        for name_of_list, current_list in zip(list_names, all_lists):
            # Используем set для обработки уникальных вхождений в одном списке
            for word in set(current_list):
                word_to_lists_map[word].add(name_of_list)
        word_to_lists_map = {k: sorted(list(v))
                             for k, v in word_to_lists_map.items()}

        words_map = [word_to_lists_map.get(word, list()) for word in words]
        words_zip = {w: m for w, m in zip(words, words_map)}
        print(f'{param_filtred_by_name=}\n'
              f'{uniq_comm_in_filtred_type=}\n'
              f'{uniq_item_in_filtred_type=}',
              file=sys.stderr)
        print(f'{f_comm}|{uf_comm} ', file=sys.stderr)
        print(f'{words_zip=}', file=sys.stderr)
        # Вариант: распознаных команд нет.
        # если доступных команд 0 - выплюнуть все варианты комманд и
        # параметров, которые начинаются с
        if not f_comm:
            if uf_word is None:
                uf_word = ''
            comm_param_opt = all_commands | all_param_variants | all_options
            slice_variants = {_ for _ in (comm_param_opt)
                              if _.startswith(uf_word)}
            print('\n'.join(slice_variants))
            print(bce.raw_input_string, file=sys.stderr, end='')
            return
        print(bce.raw_input_string, file=sys.stderr, end='')
