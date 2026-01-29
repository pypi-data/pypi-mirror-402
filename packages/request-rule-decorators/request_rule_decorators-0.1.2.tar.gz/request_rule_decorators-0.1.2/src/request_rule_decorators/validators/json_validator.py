"""Валидатор для JSON данных с использованием jsonpath."""

import re
from typing import Any, List, Optional, Type, Union

from jsonpath_ng import parse as parse_jsonpath

from ..dto import ValidationError
from .base import BaseValidator
from .blacklist_whitelist import Blacklist, Whitelist


class JSONValidator(BaseValidator):
    """Валидатор для проверки JSON данных по jsonpath."""
    
    def __init__(self, json_path: str, error_key: str | None = None):
        """
        Инициализация JSON валидатора.
        
        Args:
            json_path: JSONPath выражение для извлечения значения
            error_key: Ключ ошибки для идентификации конкретного правила
        """
        super().__init__(error_key=error_key)
        self.json_path = json_path
        self._rule_name = f"JSONValidator({json_path})"
    
    def blacklist(self) -> Blacklist:
        """Возвращает объект Blacklist для создания правил черного списка."""
        return Blacklist(self)
    
    def whitelist(self) -> Whitelist:
        """Возвращает объект Whitelist для создания правил белого списка."""
        return Whitelist(self)
    
    def range(self, min_val: Union[int, float], max_val: Union[int, float]) -> "JSONValidator":
        """Проверка, что значение в заданном диапазоне."""
        return self._add_rule("range", min_val=min_val, max_val=max_val)
    
    def regex(self, pattern: str) -> "JSONValidator":
        """Проверка значения по регулярному выражению."""
        return self._add_rule("regex", pattern=pattern)
    
    def exists(self) -> "JSONValidator":
        """Проверка существования пути."""
        return self._add_rule("exists")
    
    def type(self, expected_type: Type) -> "JSONValidator":
        """Проверка типа значения."""
        return self._add_rule("type", expected_type=expected_type)
    
    def validate(self, json_data: dict | list) -> tuple[bool, Optional[ValidationError]]:
        """
        Выполняет валидацию JSON данных.
        
        Args:
            json_data: JSON данные для валидации
            
        Returns:
            Tuple[bool, Optional[ValidationError]]: (успешность валидации, ошибка если есть)
        """
        if not self._rules:
            return True, None
        
        # Извлекаем значения по jsonpath
        try:
            jsonpath_expr = parse_jsonpath(self.json_path)
            matches = [match.value for match in jsonpath_expr.find(json_data)]
        except Exception as e:
            return False, self._create_error(
                rule_type="exists",
                expected_values=[self.json_path],
                received_values=[],
                message=f"Не удалось распарсить jsonpath '{self.json_path}': {str(e)}",
            )
        
        # Если нет совпадений и требуется exists, это ошибка
        if not matches:
            for rule in self._rules:
                if rule["type"] == "exists":
                    return False, self._create_error(
                        rule_type="exists",
                        expected_values=[self.json_path],
                        received_values=[],
                        message=f"Путь '{self.json_path}' не существует",
                    )
            # Если нет правила exists, но нет значений - пропускаем
            return True, None
        
        # Применяем все правила к каждому найденному значению
        for value in matches:
            for rule in self._rules:
                rule_type = rule["type"]
                
                if rule_type == "exists":
                    continue  # Уже проверили выше
                
                elif rule_type == "blacklist_values":
                    if value in rule["values"]:
                        return False, self._create_error(
                            rule_type="blacklist.values",
                            expected_values=[f"не в {rule['values']}"],
                            received_values=[value],
                            message=f"Значение {value} находится в черном списке {rule['values']}",
                        )
                
                elif rule_type == "whitelist_values":
                    if value not in rule["values"]:
                        return False, self._create_error(
                            rule_type="whitelist.values",
                            expected_values=rule["values"],
                            received_values=[value],
                            message=f"Значение {value} не находится в белом списке {rule['values']}",
                        )
                
                elif rule_type == "blacklist_words":
                    if not isinstance(value, str):
                        return False, self._create_error(
                            rule_type="blacklist.words",
                            expected_values=["string"],
                            received_values=[type(value).__name__],
                            message=f"Значение {value} не является строкой, невозможно проверить слова",
                        )
                    value_lower = value.lower()
                    found_words = [word for word in rule["words"] if word.lower() in value_lower]
                    if found_words:
                        return False, self._create_error(
                            rule_type="blacklist.words",
                            expected_values=[f"не содержать слова: {rule['words']}"],
                            received_values=[f"содержит: {found_words}"],
                            message=f"Значение '{value}' содержит запрещенные слова: {found_words}",
                        )
                
                elif rule_type == "whitelist_words":
                    if not isinstance(value, str):
                        return False, self._create_error(
                            rule_type="whitelist.words",
                            expected_values=["string"],
                            received_values=[type(value).__name__],
                            message=f"Значение {value} не является строкой, невозможно проверить слова",
                        )
                    value_lower = value.lower()
                    found_words = [word for word in rule["words"] if word.lower() in value_lower]
                    if not found_words:
                        return False, self._create_error(
                            rule_type="whitelist.words",
                            expected_values=[f"содержать хотя бы одно слово из: {rule['words']}"],
                            received_values=[value],
                            message=f"Значение '{value}' не содержит ни одного разрешенного слова из {rule['words']}",
                        )
                
                elif rule_type == "blacklist_regex":
                    pattern = rule["pattern"]
                    value_str = str(value)
                    if re.match(pattern, value_str):
                        return False, self._create_error(
                            rule_type="blacklist.regex",
                            expected_values=[f"не соответствует паттерну '{pattern}'"],
                            received_values=[value],
                            message=f"Значение {value} соответствует запрещенному regex паттерну '{pattern}'",
                        )
                
                elif rule_type == "whitelist_regex":
                    pattern = rule["pattern"]
                    value_str = str(value)
                    if not re.match(pattern, value_str):
                        return False, self._create_error(
                            rule_type="whitelist.regex",
                            expected_values=[f"соответствует паттерну '{pattern}'"],
                            received_values=[value],
                            message=f"Значение {value} не соответствует требуемому regex паттерну '{pattern}'",
                        )
                
                elif rule_type == "range":
                    min_val = rule["min_val"]
                    max_val = rule["max_val"]
                    if not isinstance(value, (int, float)):
                        return False, self._create_error(
                            rule_type="range",
                            expected_values=[f"число в диапазоне [{min_val}, {max_val}]"],
                            received_values=[value],
                            message=f"Значение {value} не является числом",
                        )
                    if not (min_val <= value <= max_val):
                        return False, self._create_error(
                            rule_type="range",
                            expected_values=[f"число в диапазоне [{min_val}, {max_val}]"],
                            received_values=[value],
                            message=f"Значение {value} не находится в диапазоне [{min_val}, {max_val}]",
                        )
                
                elif rule_type == "regex":
                    pattern = rule["pattern"]
                    value_str = str(value)
                    if not re.match(pattern, value_str):
                        return False, self._create_error(
                            rule_type="regex",
                            expected_values=[f"соответствует паттерну '{pattern}'"],
                            received_values=[value],
                            message=f"Значение {value} не соответствует regex паттерну '{pattern}'",
                        )
                
                elif rule_type == "type":
                    expected_type = rule["expected_type"]
                    if not isinstance(value, expected_type):
                        return False, self._create_error(
                            rule_type="type",
                            expected_values=[expected_type.__name__],
                            received_values=[type(value).__name__],
                            message=f"Значение {value} имеет тип {type(value).__name__}, ожидалось {expected_type.__name__}",
                        )
                
                elif rule_type == "blacklist_words":
                    if not isinstance(value, str):
                        return False, self._create_error(
                            rule_type="blacklist_words",
                            expected_values=["string"],
                            received_values=[type(value).__name__],
                            message=f"Значение {value} не является строкой, невозможно проверить слова",
                        )
                    value_lower = value.lower()
                    found_words = [word for word in rule["words"] if word.lower() in value_lower]
                    if found_words:
                        return False, self._create_error(
                            rule_type="blacklist_words",
                            expected_values=[f"не содержать слова: {rule['words']}"],
                            received_values=[f"содержит: {found_words}"],
                            message=f"Значение '{value}' содержит запрещенные слова: {found_words}",
                        )

                elif rule_type == "whitelist_words":
                    if not isinstance(value, str):
                        return False, self._create_error(
                            rule_type="whitelist_words",
                            expected_values=["string"],
                            received_values=[type(value).__name__],
                            message=f"Значение {value} не является строкой, невозможно проверить слова",
                        )
                    value_lower = value.lower()
                    found_words = [word for word in rule["words"] if word.lower() in value_lower]
                    if not found_words:
                        return False, self._create_error(
                            rule_type="whitelist_words",
                            expected_values=[f"содержать хотя бы одно слово из: {rule['words']}"],
                            received_values=[value],
                            message=f"Значение '{value}' не содержит ни одного разрешенного слова из {rule['words']}",
                        )
        
        return True, None

