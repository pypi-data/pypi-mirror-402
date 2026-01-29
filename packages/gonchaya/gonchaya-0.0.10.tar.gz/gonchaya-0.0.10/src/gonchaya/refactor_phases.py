"""
Система управления фазами рефакторинга

Фазы рефакторинга:
0: Фризим состояние (навсегда оставляем как есть)
1: Временно оставляем все как есть
2: Косметический рефакторинг (читаемость, комментарии)
3: Структурный рефакторинг (разделение функций, DRY)
4: Оптимизация (производительность, алгоритмы)
5: Архитектурный рефакторинг (паттерны, зависимости)

ПРОЕКТНЫЕ ПРАВИЛА (применяются всегда):
1. Использовать str | None вместо Optional[str] (Python 3.10+ синтаксис)
2. Комментарии с двойной решеткой ## не удалять никогда
3. Type hints обязательны для всех публичных функций
4. Все комментарии в замороженных функциях сохранять как якоря логики
5. Не предлагать перевод docstring без явного указания (все разработчики
     русскоязычные. Перевод на стадии написания резко замедлит общую скорость
     написания).
"""

from typing import Any, Callable, Dict, List, Set, Optional
import inspect
import sys
import ast

# ========== КЛАСС ДЛЯ УПРАВЛЕНИЯ СТИЛЕМ ==========

class StyleManager:
    """Менеджер стиля кода проекта."""
    
    # ПРОЕКТНЫЕ ПРАВИЛА (применяются всегда ко всем функциям)
    PROJECT_RULES = {
        "use_union_types": True,           # Правило 1: str | None вместо Optional[str]
        "preserve_double_hash": True,      # Правило 2: ## комментарии не удалять
        "require_type_hints": True,        # Правило 3: Type hints обязательны
        "preserve_logic_anchors": True,    # Правило 4: Сохранять якорные комментарии
        "python_version": (3, 10)
    }
    
    @classmethod
    def enforce_project_rules(cls, func: Callable) -> Dict[str, Any]:
        """Применить все проектные правила к функции.
        
        Эта проверка выполняется для ВСЕХ функций независимо от декораторов.
        """
        results = {
            "function": func.__name__,
            "rules_applied": cls.PROJECT_RULES.copy(),
            "checks": {}
        }
        
        # 1. Проверка union-типов
        results["checks"]["union_types"] = cls.check_union_types(func)
        
        # 2. Проверка комментариев с ##
        results["checks"]["double_hash"] = cls.check_double_hash_comments(func)
        
        # 3. Проверка type hints
        results["checks"]["type_hints"] = cls.check_type_hints_presence(func)
        
        # 4. Проверка всех комментариев (для якорных функций)
        results["checks"]["all_comments"] = cls.check_all_comments(func)
        
        return results
    
    @classmethod
    def check_union_types(cls, func: Callable) -> Dict[str, Any]:
        """Проверить использование Union-типов вместо Optional."""
        try:
            source = inspect.getsource(func)
            tree = ast.parse(source)
        except (OSError, TypeError):
            return {"ok": True, "issues": []}
        
        issues = []
        suggestions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Проверяем возвращаемое значение
                if node.returns:
                    returns_str = ast.unparse(node.returns)
                    if "Optional[" in returns_str:
                        inner_type = returns_str.replace("Optional[", "").replace("]", "")
                        issues.append(f"Возвращаемое значение использует Optional[]")
                        suggestions.append(f"Заменить на: {inner_type} | None")
                
                # Проверяем аргументы
                for arg in node.args.args:
                    if arg.annotation:
                        annotation_str = ast.unparse(arg.annotation)
                        if "Optional[" in annotation_str:
                            inner_type = annotation_str.replace("Optional[", "").replace("]", "")
                            issues.append(f"Аргумент '{arg.arg}' использует Optional[]")
                            suggestions.append(f"Заменить на: {inner_type} | None")
        
        return {
            "ok": len(issues) == 0,
            "issues": issues,
            "suggestions": suggestions,
            "requires_fix": len(issues) > 0
        }
    
    @classmethod
    def check_double_hash_comments(cls, func: Callable) -> Dict[str, Any]:
        """Проверить наличие комментариев с ##."""
        try:
            source = inspect.getsource(func)
            lines = source.split('\n')
            
            double_hash_lines = []
            for i, line in enumerate(lines, 1):
                if '##' in line:
                    double_hash_lines.append({
                        "line": i,
                        "content": line.strip(),
                        "preservation_required": True
                    })
            
            return {
                "has_double_hash": len(double_hash_lines) > 0,
                "count": len(double_hash_lines),
                "lines": double_hash_lines,
                "preservation_required": True  # Правило 2
            }
        except:
            return {"has_double_hash": False, "count": 0, "lines": [], "preservation_required": True}
    
    @classmethod
    def check_type_hints_presence(cls, func: Callable) -> Dict[str, Any]:
        """Проверить наличие type hints."""
        signature = inspect.signature(func)
        
        # Проверяем аргументы
        args_without_hints = []
        for param_name, param in signature.parameters.items():
            if param.annotation == inspect.Parameter.empty and param_name != 'self':
                args_without_hints.append(param_name)
        
        # Проверяем возвращаемое значение
        return_hint = signature.return_annotation != inspect.Parameter.empty
        
        return {
            "has_return_hint": return_hint,
            "missing_arg_hints": args_without_hints,
            "requires_hints": len(args_without_hints) > 0 or not return_hint,
            "priority": "high" if func.__name__[0].isupper() or not func.__name__.startswith('_') else "medium"
        }
    
    @classmethod
    def check_all_comments(cls, func: Callable) -> Dict[str, Any]:
        """Проверить все комментарии в функции (для якорных функций)."""
        try:
            source = inspect.getsource(func)
            lines = source.split('\n')
            
            all_comments = []
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                if stripped.startswith('#') and not stripped.startswith('#!/'):
                    # Это комментарий
                    comment_type = "double_hash" if '##' in line else "regular"
                    all_comments.append({
                        "line": i,
                        "content": stripped,
                        "type": comment_type,
                        "preservation_priority": "high" if comment_type == "double_hash" else "medium"
                    })
            
            return {
                "total_comments": len(all_comments),
                "comments": all_comments,
                "has_comments": len(all_comments) > 0
            }
        except:
            return {"total_comments": 0, "comments": [], "has_comments": False}
    
    @classmethod
    def audit_function(cls, func: Callable) -> Dict[str, Any]:
        """Провести полный аудит функции с учетом ВСЕХ проектных правил."""
        audit_result = cls.enforce_project_rules(func)
        
        # Добавляем общую оценку
        issues_count = (
            len(audit_result["checks"]["union_types"]["issues"]) +
            len(audit_result["checks"]["type_hints"]["missing_arg_hints"]) +
            (0 if audit_result["checks"]["type_hints"]["has_return_hint"] else 1)
        )
        
        audit_result["overall"] = {
            "issues_count": issues_count,
            "requires_fixes": issues_count > 0,
            "compliance_level": "full" if issues_count == 0 else "partial",
            "mandatory_fixes": [
                rule for rule, check in [
                    ("union_types", audit_result["checks"]["union_types"]["requires_fix"]),
                    ("type_hints", audit_result["checks"]["type_hints"]["requires_hints"])
                ] if check
            ]
        }

        return audit_result

    @classmethod
    def audit_module(cls, module_name: str = None) -> Dict[str, Any]:
        """Провести аудит всего модуля."""
        if module_name is None:
            frame = inspect.currentframe()
            module_name = frame.f_back.f_globals['__name__']
        
        module = sys.modules.get(module_name)
        if not module:
            return {"error": f"Модуль {module_name} не найден"}
        
        functions = []
        for name, obj in inspect.getmembers(module):
            if inspect.isfunction(obj) and obj.__module__ == module_name:
                functions.append(obj)
        
        results = []
        for func in functions:
            results.append(cls.audit_function(func))
        
        # Статистика
        stats = {
            "total_functions": len(functions),
            "violates_union_rule": 0,
            "has_double_hash": 0,
            "missing_type_hints": 0,
            "fully_compliant": 0
        }
        
        for result in results:
            if not result["checks"]["union_types"]["ok"]:
                stats["violates_union_rule"] += 1
            if result["checks"]["double_hash"]["has_double_hash"]:
                stats["has_double_hash"] += 1
            if not result["type_hints"]["ok"]:
                stats["missing_type_hints"] += 1
            if (result["union_types"]["ok"] and 
                result["type_hints"]["ok"]):
                stats["fully_compliant"] += 1
        
        return {
            "module": module_name,
            "results": results,
            "stats": stats,
            "rules": cls.PROJECT_RULES
        }

# ========== КЛАСС ДЛЯ УПРАВЛЕНИЯ РЕФАКТОРИНГОМ ==========

class RefactorManager:
    """Менеджер рефакторинга с поддержкой фаз."""
    
    # Текущая фаза рефакторинга
    CURRENT_PHASE = 2
    
    # Уровни разрешений
    PERMISSION_LEVELS = {
        0: {"name": "Замораживание", "description": "Навсегда оставляем как есть"},
        1: {"name": "Только анализ", "description": "Временно оставляем все как есть"},
        2: {"name": "Косметический", "description": "Читаемость, комментарии"},
        3: {"name": "Структурный", "description": "Разделение функций, DRY"},
        4: {"name": "Оптимизация", "description": "Производительность, алгоритмы"},
        5: {"name": "Архитектурный", "description": "Паттерны, зависимости"}
    }
    
    # Разрешения для каждой фазы
    PHASE_PERMISSIONS = {
        0: set(),  # Ничего нельзя
        1: {"analyze"},  # Только анализ
        2: {"analyze", "rename", "comments", "formatting", "extract_constants"},
        3: {"analyze", "rename", "comments", "formatting", "extract_constants",
            "extract_functions", "split_functions", "dry", "restructure"},
        4: {"analyze", "rename", "comments", "formatting", "extract_constants",
            "extract_functions", "split_functions", "dry", "restructure",
            "optimize", "algorithms", "performance"},
        5: {"analyze", "rename", "comments", "formatting", "extract_constants",
            "extract_functions", "split_functions", "dry", "restructure",
            "optimize", "algorithms", "performance",
            "architecture", "patterns", "dependencies", "redesign"}
    }
    
    def __init__(self):
        self.style_manager = StyleManager()
    
    @classmethod
    def set_current_phase(cls, phase: int):
        """Установить текущую фазу рефакторинга.
        
        Args:
            phase: Номер фазы от 0 до 5
            
        Raises:
            ValueError: Если фаза вне допустимого диапазона
            
        Example:
            >>> RefactorManager.set_current_phase(3)
            Текущая фаза рефакторинга установлена: 3 - Структурный
        """
        if phase not in cls.PERMISSION_LEVELS:
            raise ValueError(f"Фаза должна быть от 0 до {len(cls.PERMISSION_LEVELS)-1}")
        cls.CURRENT_PHASE = phase
        # print(f"Текущая фаза рефакторинга установлена: {phase} - {cls.PERMISSION_LEVELS[phase]['name']}")
    
    @classmethod
    def get_permissions_for_phase(cls, phase: int) -> Set[str]:
        """Получить разрешения для указанной фазы.
        
        Args:
            phase: Номер фазы
            
        Returns:
            Множество разрешенных действий
            
        Example:
            >>> RefactorManager.get_permissions_for_phase(2)
            {'analyze', 'rename', 'comments', 'formatting', 'extract_constants'}
        """
        return cls.PHASE_PERMISSIONS.get(phase, set())
    
    @classmethod
    def get_current_permissions(cls) -> Set[str]:
        """Получить разрешения для текущей фазы.
        
        Returns:
            Множество разрешенных действий для текущей фазы
        """
        return cls.get_permissions_for_phase(cls.CURRENT_PHASE)
    
    @classmethod
    def can_refactor(cls, func: Callable, permission: str) -> bool:
        """Проверить, можно ли выполнить действие над функцией.
        
        Важно: проектные правила (type hints, ## комментарии, union типы) 
        применяются ВСЕГДА, даже если функция заморожена!

        Args:
            func: Функция для проверки
            permission: Действие для проверки
            
        Returns:
            True если действие разрешено, иначе False
            
        Example:
            >>> @cosmetic_only()
            >>> def example(): pass
            >>> RefactorManager.can_refactor(example, "rename")
            True
            >>> RefactorManager.can_refactor(example, "optimize")
            False
        """
        # Получаем разрешения из функции
        func_permissions = getattr(func, '__refactor_permissions__', None)
        func_phase = getattr(func, '__refactor_phase__', cls.CURRENT_PHASE)
        
        # Если функция заморожена
        if getattr(func, '__frozen__', False):
            # Для замороженных функций разрешены ТОЛЬКО проектные исправления
            project_fixes = {"fix_union_types", "add_type_hints", "preserve_double_hash"}
            return permission in project_fixes
        
        # Если для функции указана фаза
        if func_permissions is not None:
            return permission in func_permissions
        
        # Используем разрешения фазы функции
        phase_permissions = cls.get_permissions_for_phase(func_phase)
        return permission in phase_permissions
    
    def analyze_function(self, func: Callable) -> Dict[str, Any]:
        """Проанализировать функцию и дать рекомендации.

        Всегда включает проверку проектных правил, даже для замороженных функций.
        
        Args:
            func: Функция для анализа
            
        Returns:
            Словарь с анализом и рекомендациями
            
        Example:
            >>> manager = RefactorManager()
            >>> analysis = manager.analyze_function(some_function)
            >>> print(analysis["recommendations"])
            ["Заменить Optional[] на | None синтаксис"]
        """
        # Проверяем стиль (ВСЕГДА, даже для замороженных функций)
        style_audit = self.style_manager.audit_function(func)
        
        # Получаем статус рефакторинга
        refactor_phase = getattr(func, '__refactor_phase__', self.CURRENT_PHASE)
        is_frozen = getattr(func, '__frozen__', False)
        skip_reason = getattr(func, '__skip_reason__', '')
        preserve_all_comments = getattr(func, '__preserve_all_comments__', False)
        
        # ОБЯЗАТЕЛЬНЫЕ рекомендации (проектные правила)
        mandatory_recommendations = []
        
        if style_audit["checks"]["union_types"]["requires_fix"]:
            mandatory_recommendations.append("ЗАМЕНИТЬ Optional[] на | None синтаксис")
        
        if style_audit["checks"]["type_hints"]["requires_hints"]:
            missing_args = style_audit["checks"]["type_hints"]["missing_arg_hints"]
            if missing_args:
                mandatory_recommendations.append(f"ДОБАВИТЬ type hints для аргументов: {', '.join(missing_args)}")
            if not style_audit["checks"]["type_hints"]["has_return_hint"]:
                mandatory_recommendations.append("ДОБАВИТЬ type hint для возвращаемого значения")
        
        # Рекомендации по комментариям
        comment_recommendations = []
        
        if style_audit["checks"]["double_hash"]["has_double_hash"]:
            comment_recommendations.append("СОХРАНИТЬ комментарии с ## (проектное правило)")
        
        if preserve_all_comments:
            comment_recommendations.append("СОХРАНИТЬ ВСЕ комментарии (якоря логики)")
        
        # Определяем доступные действия
        available_actions = []
        
        if is_frozen:
            # Для замороженных функций доступны ТОЛЬКО исправления проектных правил
            available_actions = ["fix_union_types", "add_type_hints", "preserve_double_hash"]
        elif not is_frozen and refactor_phase <= self.CURRENT_PHASE:
            phase_perms = self.get_permissions_for_phase(refactor_phase)
            available_actions = list(phase_perms)
        
        return {
            "function": func.__name__,
            "module": func.__module__,
            "refactor_phase": refactor_phase,
            "is_frozen": is_frozen,
            "preserve_all_comments": preserve_all_comments,
            "skip_reason": skip_reason,
            
            # Проектные правила (всегда проверяются)
            "project_rules_applied": True,
            "mandatory_recommendations": mandatory_recommendations,
            "comment_recommendations": comment_recommendations,
            
            # Стилевые проверки
            "style_audit": {
                "union_issues": style_audit["checks"]["union_types"]["issues"],
                "type_hint_issues": style_audit["checks"]["type_hints"]["missing_arg_hints"],
                "missing_return_hint": not style_audit["checks"]["type_hints"]["has_return_hint"],
                "double_hash_count": style_audit["checks"]["double_hash"]["count"],
                "total_comments": style_audit["checks"]["all_comments"]["total_comments"]
            },
            
            # Доступные действия
            "available_actions": available_actions,
            "can_refactor": not is_frozen and refactor_phase <= self.CURRENT_PHASE,
            
            # Приоритеты
            "priority": "critical" if mandatory_recommendations else "normal"
        }

# ========== ДЕКОРАТОРЫ РЕФАКТОРИНГА (9 штук) ==========

# 1. Заморозка навсегда с сохранением комментариев-якорей
def freeze_permanently(reason: str = "Критическая стабильность", preserve_comments_as_anchors: bool = True):
    """
    Заморозить функцию навсегда с сохранением комментариев как якорей логики.
    
    ПРАВИЛА ДЛЯ ЗАМОРОЖЕННЫХ ФУНКЦИЙ:
    - ❌ Никаких изменений в логике и реализации
    - ❌ Никаких изменений в обычных комментариях
    - ❌ Никаких изменений в форматировании (кроме очевидных исправлений)
    
    ОБЯЗАТЕЛЬНЫЕ ИСПРАВЛЕНИЯ (даже для замороженных функций):
    - ✅ Исправить Optional[] на | None (проектное правило 1)
    - ✅ Добавить type hints если их нет (проектное правило 3)
    - ✅ Сохранить комментарии с ## (проектное правило 2)
    - ✅ Сохранить ВСЕ существующие комментарии как якоря логики (preserve_comments_as_anchors=True)
    
    ПРИМЕР:
        @freeze_permanently("Расчет налога по старому законодательству")
        def calculate_tax_2019(income: Optional[float]) -> Optional[float]:
            # Этот комментарий объясняет формулу 2019 года
            tax = income * 0.13  # Ставка НДФЛ 2019
            return tax
        # Будет исправлено на:
        # def calculate_tax_2019(income: float | None) -> float | None:
        # (все комментарии сохранены)
    """
    def decorator(func: Callable) -> Callable:
        func.__frozen__ = True
        func.__frozen_reason__ = reason
        func.__refactor_phase__ = 0
        func.__refactor_permissions__ = {"fix_union_types", "add_type_hints", "preserve_comments"}
        
        # Автоматически применяем сохранение всех комментариев для замороженных функций
        if preserve_comments_as_anchors:
            func.__preserve_all_comments__ = True
            func.__comment_preservation__ = "all_comments_as_logic_anchors"
        
        func.__refactor_status__ = "frozen_permanently_with_rules"
        func.__rules_note__ = "Заморожена, но проектные правила применяются"
        return func
    return decorator

# 2. Пропустить в текущей фазе
def skip_for_now(reason: str = "", phase: int = 3):
    """
    Пропустить рефакторинг функции до указанной фазы.
    
    ПРИМЕНЕНИЕ:
    - Временная мера для сложного кода
    - Когда нет времени/ресурсов на рефакторинг сейчас
    - Для кода, который скоро будет заменен
    - Для функций с высоким риском при изменении
    
    ПРАВИЛА ДО УКАЗАННОЙ ФАЗЫ:
    - ✅ Применить ВСЕ проектные правила (type hints, union types, ##)
    - ✅ Можно анализировать и документировать проблемы
    - ❌ Нельзя вносить другие изменения
    
    ПРИМЕР:
        @skip_for_now("Интеграция с устаревшей системой", phase=4)
        def legacy_integration(data):  # Будет исправлен type hint
            # TODO: переписать когда обновим API
            return process(data)
        # Type hint будет добавлен, остальное - в фазе 4
    """
    def decorator(func: Callable) -> Callable:
        func.__skip_reason__ = reason or "Сложная логика, требует отдельного внимания"
        func.__refactor_phase__ = phase
        func.__refactor_status__ = "skipped_until_phase"
        func.__project_rules_applied__ = True  # Проектные правила все равно применяются
        return func
    return decorator

# 3. Только косметические изменения
def cosmetic_only():
    """
    Разрешить только косметический рефакторинг (фаза 2).
    
    ПРИМЕНЕНИЕ:
    - Для кода, который работает правильно, но плохо читается
    - Когда нужно подготовить код к будущему структурному рефакторингу
    - Для улучшения сопровождения без риска внесения ошибок

    АВТОМАТИЧЕСКО ПРИМЕНЯЕТСЯ:
    - ✅ Все проектные правила (type hints, union types, ## комментарии)
    
    
    РАЗРЕШЕНО:
    - ✅ Переименование переменных и функций для ясности
    - ✅ Форматирование кода (пробелы, отступы, переносы строк)
    - ✅ Добавление/улучшение комментариев
    - ✅ Удаление мертвого кода и неиспользуемых импортов
    - ✅ Вынос магических чисел в константы
    
    ЗАПРЕЩЕНО:
    - ❌ Изменение алгоритмов и логики
    - ❌ Оптимизация производительности
    - ❌ Изменение архитектуры
    - ❌ Разделение функций на подфункции
    
    ПРИМЕР:
        @cosmetic_only()
        def calc(x, y):
            a = x * y  ## важный коэффициент из документации
            return a
        # Станет:
        # def calc(price: float, quantity: int) -> float:
        #     total = price * quantity  ## важный коэффициент из документации
        #     return total
    """
    def decorator(func: Callable) -> Callable:
        func.__refactor_phase__ = 2
        func.__refactor_scope__ = "cosmetic"
        func.__refactor_status__ = "ready_for_cosmetic"
        func.__project_rules_applied__ = True
        return func
    return decorator

def allow_logic_change() -> Callable[[F], F]:
    """
    Декоратор, разрешающий изменение бизнес-логики функции.
    Используется, когда требуется изменить ЧТО делает функция (её цель и результат),
    а не КАК она это делает (оптимизация) или как она выглядит (косметика).
    """
    def decorator(func: F) -> F:
        func.__refactor_phase__ = "logic_change_allowed"
        return func
    return decorator

# 4. Готово к структурному рефакторингу
def allow_for_restructure():
    """
    Функция готова к структурному рефакторингу (фаза 3).
    
    ПРИМЕНЕНИЕ:
    - Для функций, которые слишком длинные (>30 строк)
    - Для кода с нарушением принципа DRY (повторения)
    - Когда функцию нужно разделить на логические части
    - Для улучшения тестируемости через выделение чистых функций

    АВТОМАТИЧЕСКО ПРИМЕНЯЕТСЯ:
    - ✅ Все проектные правила (type hints, union types, ## комментарии)
    
    РАЗРЕШЕНО ДОПОЛНИТЕЛЬНО:
    - ✅ Всё что разрешено в косметическом рефакторинге
    - ✅ Разделение длинных функций на меньшие
    - ✅ Выделение общих частей в отдельные функции
    - ✅ Изменение структуры кода без изменения поведения
    - ✅ Упрощение сложных условных выражений
    - ✅ Применение паттернов рефакторинга (Extract Method и др.)
    
    ЗАПРЕЩЕНО:
    - ❌ Оптимизация производительности (кроме очевидных улучшений)
    - ❌ Изменение архитектурных решений
    - ❌ Изменение публичного API без необходимости
    
    ПРИМЕР:
        @ready_for_restructure()
        def process_order(order):  # Будет разделена с применением проектных правил
            # validate, calculate, apply_discounts, create_invoice
            pass
    """
    def decorator(func: Callable) -> Callable:
        func.__refactor_phase__ = 3
        func.__refactor_scope__ = "structural"
        func.__refactor_status__ = "ready_for_restructure"
        func.__project_rules_applied__ = True
        return func
    return decorator

# 5. Можно оптимизировать
def allow_optimization():
    """
    Разрешить оптимизацию производительности (фаза 4).
    
    ПРИМЕНЕНИЕ:
    - Для функций с известными проблемами производительности
    - Когда код работает правильно, но слишком медленно
    - Для замены неэффективных алгоритмов
    - Для добавления кэширования и мемоизации

    АВТОМАТИЧЕСКО ПРИМЕНЯЕТСЯ:
    - ✅ Все проектные правила (type hints, union types, ## комментарии)
    
    РАЗРЕШЕНО ДОПОЛНИТЕЛЬНО:
    - ✅ Всё что разрешено в структурном рефакторинге
    - ✅ Замена алгоритмов на более эффективные
    - ✅ Добавление кэширования
    - ✅ Оптимизация циклов и структур данных
    - ✅ Использование более эффективных структур данных
    - ✅ Векторизация операций (если применимо)
    
    ЗАПРЕЩЕНО:
    - ❌ Изменение архитектуры без веской причины
    - ❌ Изменение публичного API
    - ❌ Ухудшение читаемости без значительного выигрыша в производительности
    
    ПРИМЕР:
        @allow_optimization()
        def find_duplicates(items):  # O(n²) → O(n)
            # Медленная реализация с вложенными циклами
            # Заменяется на использование множества
    
    ПРЕДУПРЕЖДЕНИЕ:
    - Всегда проверять оптимизации профилированием
    - Сохранять обратную совместимость
    """
    def decorator(func: Callable) -> Callable:
        func.__refactor_phase__ = 4
        func.__refactor_scope__ = "optimization"
        func.__refactor_status__ = "ready_for_optimization"
        func.__project_rules_applied__ = True
        return func
    return decorator

# 6. Архитектурные изменения
def allow_architectural():
    """
    Разрешить архитектурные изменения (фаза 5).
    
    ПРИМЕНЕНИЕ:
    - Для рефакторинга, затрагивающего несколько модулей
    - При изменении паттернов проектирования
    - Для перехода на другую архитектурную парадигму
    - При значительном изменении зависимостей

    АВТОМАТИЧЕСКО ПРИМЕНЯЕТСЯ:
    - ✅ Все проектные правила (type hints, union types, ## комментарии)
    
    РАЗРЕШЕНО:
    - ✅ Всё что разрешено в оптимизации
    - ✅ Изменение архитектурных решений
    - ✅ Внедрение паттернов проектирования
    - ✅ Реорганизация зависимостей между модулями
    - ✅ Значительные изменения публичного API
    - ✅ Переход на асинхронную модель (если нужно)
    
    ПРЕДУСЛОВИЯ:
    - Должны быть написаны интеграционные тесты
    - Необходимо согласование с командой
    - Требуется обновление документации
    
    ПРИМЕР:
        @allow_architectural()
        class OrderProcessor:  # Может быть разделен на:
            # OrderValidator, OrderCalculator, OrderNotifier
            # С внедрением Dependency Injection
    
    ОГРАНИЧЕНИЕ:
    - Самый рискованный тип рефакторинга
    - Требует тщательного планирования
    """
    def decorator(func: Callable) -> Callable:
        func.__refactor_phase__ = 5
        func.__refactor_scope__ = "architectural"
        func.__refactor_status__ = "ready_for_architectural"
        func.__project_rules_applied__ = True
        return func
    return decorator

# 7. СОХРАНИТЬ ВСЕ КОММЕНТАРИИ КАК ЯКОРИ ЛОГИКИ
def preserve_all_comments_as_anchors(reason: str = "Комментарии объясняют сложную логику"):
    """
    СОХРАНИТЬ ВСЕ существующие комментарии в функции как якоря для понимания логики.
    
    ПРИМЕНЕНИЕ:
    - Для функций со сложной бизнес-логикой
    - Когда комментарии объясняют нетривиальные решения
    - Для исторического кода с важными заметками
    - Когда комментарии служат документацией
    
    ПРАВИЛА:
    - ✅ ВСЕ комментарии (# и ##) должны быть сохранены
    - ✅ Комментарии нельзя удалять или существенно изменять
    - ✅ Можно исправлять опечатки в комментариях
    - ✅ Можно добавлять новые комментарии для пояснения
    - ✅ Комментарии можно перемещать вместе с кодом
    
    ОТЛИЧИЕ ОТ ПРОЕКТНЫХ ПРАВИЛ:
    - Проектное правило: сохранять только ## комментарии
    - Этот декоратор: сохранять ВСЕ комментарии
    
    ПРИМЕР:
        @preserve_all_comments_as_anchors("Логика расчета скидок 2020-2023")
        def calculate_discount(customer_type, amount):
            # Правила до 2020 года
            if customer_type == "VIP":
                discount = 0.15  # Фиксированная скидка для VIP
            # Новые правила с 2021
            elif amount > 10000:
                discount = 0.10  ## Изменено по требованию отдела продаж
            # Все комментарии будут сохранены при любом рефакторинге
    """
    def decorator(func: Callable) -> Callable:
        func.__preserve_all_comments__ = True
        func.__preserve_all_comments_reason__ = reason
        func.__comment_preservation__ = "all_comments_as_logic_anchors"
        func.__refactor_note__ = "Все комментарии обязательны к сохранению"
        return func
    return decorator

# 8. Экспериментальный рефакторинг
def experimental_refactor():
    """
    Разрешить экспериментальный рефакторинг с тестами.
    
    ПРИМЕНЕНИЕ:
    - Для тестирования новых подходов и паттернов
    - Когда есть хорошее тестовое покрытие
    - Для A/B тестирования разных реализаций
    - В исследовательских целях

    АВТОМАТИЧЕСКО ПРИМЕНЯЕТСЯ:
    - ✅ Все проектные правила (type hints, union types, ## комментарии)

    
    УСЛОВИЯ:
    - ✅ Должны быть юнит-тесты с покрытием >80%
    - ✅ Должна быть возможность отката
    - ✅ Изменения должны быть изолированы
    - ✅ Нужно сохранять обратную совместимость
    
    РАЗРЕШЕНО:
    - ✅ Любые изменения с соблюдением условий выше
    - ✅ Можно менять сигнатуру (с обновлением всех вызовов)
    - ✅ Можно полностью переписать логику
    
    ОГРАНИЧЕНИЯ:
    - ❌ Нельзя нарушать существующие тесты
    - ❌ Нельзя изменять поведение для корректных входных данных
    - ❌ Нельзя удалять функциональность без депривации
    
    ПРИМЕР:
        @experimental_refactor()
        def search_algorithm(query):  # Можно пробовать разные алгоритмы
            # Реализация 1: бинарный поиск
            # Реализация 2: хеш-таблицы
            # Реализация 3: инвертированный индекс
    
    ПРЕДУПРЕЖДЕНИЕ:
    - Использовать с осторожностью в production коде
    - Всегда иметь план отката
    """
    def decorator(func: Callable) -> Callable:
        func.__experimental__ = True
        func.__refactor_phase__ = RefactorManager.CURRENT_PHASE
        func.__refactor_status__ = "experimental"
        func.__project_rules_applied__ = True
        return func
    return decorator

# 9. Ожидание зависимостей
def waiting_for_dependencies(deps: List[str]):
    """
    Отложить рефакторинг из-за зависимостей.
    
    ПРИМЕНЕНИЕ:
    - Когда функция зависит от кода, который тоже требует рефакторинга
    - Для координации изменений в распределенной команде
    - Когда есть внешние зависимости, которые скоро изменятся

    АВТОМАТИЧЕСКО ПРИМЕНЯЕТСЯ:
    - ✅ Все проектные правила (type hints, union types, ## комментарии)
    - Даже при ожидании зависимости нужно применять проектные правила!
    
    ПРАВИЛА В ОЖИДАНИИ:
    - ✅ Можно анализировать и планировать изменения
    - ✅ Можно писать тесты для будущего рефакторинга
    - ✅ Можно обновлять документацию
    - ❌ Нельзя вносить изменения в реализацию
    
    КОГДА СТАТУС МЕНЯЕТСЯ:
    - Когда все зависимости обновлены
    - Когда внешние API стабилизировались
    - По решению команды
    
    ПРИМЕР:
        @waiting_for_dependencies(["database_schema", "external_api_v2"])
        def import_data(source):
            # Зависит от обновления БД и внешнего API
            # Пока использует старые интерфейсы
    
    ОТСЛЕЖИВАНИЕ:
    - В отчетах будет показано "ожидает: [список зависимостей]"
    - Можно устанавливать сроки ожидания
    """
    def decorator(func: Callable) -> Callable:
        func.__dependencies__ = deps
        func.__blocked_by__ = deps
        func.__refactor_status__ = "waiting_for_dependencies"
        func.__project_rules_applied__ = True  # Правила все равно применяются
        return func
    return decorator

# ========== УТИЛИТЫ ДЛЯ РАБОТЫ ==========

def analyze_module(module_name: str = None, include_project_rules: bool = True) -> Dict[str, Any]:
    """Проанализировать весь модуль с учетом ВСЕХ проектных правил."""
    manager = RefactorManager()
    
    if module_name is None:
        frame = inspect.currentframe()
        module_name = frame.f_back.f_globals['__name__']
    
    module = sys.modules.get(module_name)
    if not module:
        return {"error": f"Модуль {module_name} не найден"}
    
    functions = []
    for name, obj in inspect.getmembers(module):
        if inspect.isfunction(obj) and obj.__module__ == module_name:
            functions.append(obj)
    
    analysis = []
    project_rule_violations = []
    
    for func in functions:
        func_analysis = manager.analyze_function(func)
        analysis.append(func_analysis)
        
        # Собираем нарушения проектных правил
        if func_analysis["mandatory_recommendations"]:
            project_rule_violations.append({
                "function": func.__name__,
                "violations": func_analysis["mandatory_recommendations"],
                "priority": func_analysis["priority"]
            })
    
    # Группируем по статусу
    by_status = {
        "frozen": [],
        "can_refactor": [],
        "waiting": [],
        "needs_attention": [],
        "project_rule_violations": project_rule_violations
    }
    
    for result in analysis:
        if result["is_frozen"]:
            by_status["frozen"].append(result)
        elif result["can_refactor"]:
            by_status["can_refactor"].append(result)
        elif getattr(module, result["function"]).__dict__.get('__refactor_status__') == "waiting":
            by_status["waiting"].append(result)
        else:
            by_status["needs_attention"].append(result)
    
    # Общая статистика по проектным правилам
    project_stats = {
        "total_functions": len(functions),
        "needs_union_fix": sum(1 for a in analysis if a["style_audit"]["union_issues"]),
        "needs_type_hints": sum(1 for a in analysis if a["style_audit"]["type_hint_issues"] or a["style_audit"]["missing_return_hint"]),
        "has_double_hash": sum(1 for a in analysis if a["style_audit"]["double_hash_count"] > 0),
        "preserves_all_comments": sum(1 for a in analysis if a["preserve_all_comments"]),
        "fully_compliant": sum(1 for a in analysis if not a["mandatory_recommendations"])
    }
    
    return {
        "module": module_name,
        "current_phase": RefactorManager.CURRENT_PHASE,
        "total_functions": len(functions),
        "analysis": analysis,
        "grouped": by_status,
        "project_rules_stats": project_stats,
        "project_rules": StyleManager.PROJECT_RULES
    }

def print_analysis_report(module_name: str = None):
    """Вывести отчет по анализу модуля с акцентом на проектные правила."""
    result = analyze_module(module_name)
    
    if "error" in result:
        print(f"Ошибка: {result['error']}")
        return
    
    print(f"\n{'='*80}")
    print(f"АНАЛИЗ РЕФАКТОРИНГА С ПРОЕКТНЫМИ ПРАВИЛАМИ".center(80))
    print(f"Модуль: {result['module']}")
    print(f"Текущая фаза: {result['current_phase']}")
    print(f"{'='*80}")
    
    # Выводим проектные правила
    print(f"\n📋 ПРОЕКТНЫЕ ПРАВИЛА (применяются ВСЕГДА):")
    rules = StyleManager.PROJECT_RULES
    print(f"  1. Union типы: {'✅' if rules['use_union_types'] else '❌'} str | None вместо Optional[str]")
    print(f"  2. ## комментарии: {'✅' if rules['preserve_double_hash'] else '❌'} не удалять никогда")
    print(f"  3. Type hints: {'✅' if rules['require_type_hints'] else '❌'} обязательны для публичных функций")
    print(f"  4. Якорные комментарии: {'✅' if rules['preserve_logic_anchors'] else '❌'} сохранять в замороженных функциях")
    
    print(f"\n📊 СТАТИСТИКА ПО ПРОЕКТНЫМ ПРАВИЛАМ:")
    stats = result["project_rules_stats"]
    print(f"  Всего функций: {stats['total_functions']}")
    print(f"  Нарушают union правило: {stats['needs_union_fix']}")
    print(f"  Нуждаются в type hints: {stats['needs_type_hints']}")
    print(f"  Имеют ## комментарии: {stats['has_double_hash']}")
    print(f"  Сохраняют все комментарии: {stats['preserves_all_comments']}")
    print(f"  Полностью соответствуют: {stats['fully_compliant']} ({stats['fully_compliant']/max(stats['total_functions'],1)*100:.1f}%)")
    
    # Критические нарушения
    if result["grouped"]["project_rule_violations"]:
        print(f"\n⚠️  КРИТИЧЕСКИЕ НАРУШЕНИЯ ПРОЕКТНЫХ ПРАВИЛ:")
        for violation in result["grouped"]["project_rule_violations"][:10]:  # Показываем первые 10
            print(f"\n  {violation['function']}:")
            for v in violation["violations"]:
                print(f"    • {v}")
    
    # Статус рефакторинга
    print(f"\n📈 СТАТУС РЕФАКТОРИНГА:")
    print(f"  Заморожено: {len(result['grouped']['frozen'])}")
    print(f"  Готово к рефакторингу: {len(result['grouped']['can_refactor'])}")
    print(f"  Ожидает зависимостей: {len(result['grouped']['waiting'])}")
    print(f"  Требует внимания: {len(result['grouped']['needs_attention'])}")
    
    # Выводим рекомендации
    print(f"\n🔧 Рекомендации по функциям:")
    for func_analysis in result["analysis"]:
        if func_analysis["recommendations"]:
            print(f"\n  {func_analysis['function']}:")
            for rec in func_analysis["recommendations"]:
                print(f"    • {rec}")
    
    print(f"\n{'='*80}")

# ========== ДЕМОНСТРАЦИОННЫЙ КОД ==========

if __name__ == "__main__":
    # Устанавливаем фазу
    RefactorManager.set_current_phase(2)
    
    # Примеры функций для демонстрации
    
    @freeze_permanently("Критический расчет платежей 2022")
    def calculate_payment_2022(amount: Optional[float], days: int) -> Optional[float]:
        """
        Расчет платежа по старым правилам 2022 года.
        Не менять логику! Комментарии объясняют бизнес-правила.
        """
        # Базовая ставка 2022 года
        base_rate = 0.05  # Утверждено приказом №123
        
        if amount is None:
            return None  ## Особый случай для неопределенных сумм
        
        # Применяем дневной коэффициент
        daily_coeff = 1 + (days * 0.001)  # Формула из методички
        payment = amount * base_rate * daily_coeff
        
        return payment
    
    @cosmetic_only()
    @preserve_all_comments_as_anchors("Комментарии объясняют эвристики поиска")
    def search_products(query: str, filters: Optional[dict] = None) -> list:
        # Инициализируем результат
        results = []  ## Кэшируемый список
        
        # Применяем базовые фильтры
        if filters:  # TODO: оптимизировать фильтрацию
            # Проверка наличия цены
            if 'price_range' in filters:
                min_price = filters['price_range'][0]
                # Фильтрация по цене
                pass
        
        # Возвращаем результаты
        return results  ## Может быть пустым
    
    @skip_for_now("Сложная интеграция с SOAP API", phase=4)
    def call_soap_api(endpoint: str, data: dict):
        """Вызов устаревшего SOAP API."""
        # Создание SOAP конверта
        envelope = f"""<?xml version="1.0"?>
        <soap:Envelope>
            <soap:Body>
                <Request>{data}</Request>
            </soap:Body>
        </soap:Envelope>"""
        # TODO: заменить на REST когда API обновят
        return envelope
    
    @ready_for_restructure()
    def process_order(order_data: dict, customer_info: Optional[dict]):
        """Обработка заказа - требует разделения."""
        # Валидация данных
        if not order_data.get('items'):
            raise ValueError("Нет товаров в заказе")
        
        # Расчет суммы
        total = 0
        for item in order_data['items']:
            price = item.get('price', 0)
            quantity = item.get('quantity', 1)
            total += price * quantity  ## Базовая формула
        
        # Применение скидки
        if customer_info and customer_info.get('vip', False):
            total *= 0.9  # Скидка 10% для VIP
        
        # Создание записи
        record = {
            'total': total,
            'customer': customer_info,
            'timestamp': '2024-01-01'
        }
        
        return record
    
    # Генерируем отчет
    print_analysis_report(__name__)
    
    # Демонстрация применения правил
    print(f"\n{'='*80}")
    print(f"ПРИМЕРЫ ПРИМЕНЕНИЯ ПРАВИЛ:".center(80))
    print(f"{'='*80}")
    
    manager = RefactorManager()
    
    # Проверяем замороженную функцию
    frozen_analysis = manager.analyze_function(calculate_payment_2022)
    print(f"\n1. ЗАМОРОЖЕННАЯ ФУНКЦИЯ (но правила применяются):")
    print(f"   Функция: {frozen_analysis['function']}")
    print(f"   Статус: {'❄️ ЗАМОРОЖЕНА' if frozen_analysis['is_frozen'] else '✅ Активна'}")
    print(f"   Проектные правила: {'✅ Применены' if frozen_analysis['project_rules_applied'] else '❌ Не применены'}")
    if frozen_analysis['mandatory_recommendations']:
        print(f"   Обязательные исправления:")
        for rec in frozen_analysis['mandatory_recommendations']:
            print(f"     • {rec}")
    
    # Проверяем функцию с сохранением всех комментариев
    anchored_analysis = manager.analyze_function(search_products)
    print(f"\n2. ФУНКЦИЯ С ЯКОРНЫМИ КОММЕНТАРИЯМИ:")
    print(f"   Функция: {anchored_analysis['function']}")
    print(f"   Сохранять все комментарии: {'✅ Да' if anchored_analysis['preserve_all_comments'] else '❌ Нет'}")
    print(f"   Комментариев с ##: {anchored_analysis['style_audit']['double_hash_count']}")
    print(f"   Всего комментариев: {anchored_analysis['style_audit']['total_comments']}")
    
    print(f"\n{'='*80}")
    print(f"ВЫВОД: Проектные правила применяются ВСЕГДА ко ВСЕМ функциям.")
    print(f"Даже замороженные функции получат исправления type hints и union типов.")
    print(f"{'='*80}")
