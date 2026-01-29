"""Валидатор для HTML данных с использованием xpath."""

import re
from typing import Any, List, Optional, Type, Union

from lxml import html

from ..dto import ValidationError
from .base import BaseValidator
from .blacklist_whitelist import Blacklist, Whitelist


class HTMLValidator(BaseValidator):
    """Валидатор для проверки HTML данных по xpath."""
    
    def __init__(self, xpath: str, error_key: Optional[str] = None):
        """
        Инициализация HTML валидатора.
        
        Args:
            xpath: XPath выражение для извлечения значения
            error_key: Ключ ошибки для идентификации конкретного правила
        """
        super().__init__(error_key=error_key)
        self.xpath = xpath
        self._rule_name = f"HTMLValidator({xpath})"
    
    def blacklist(self) -> Blacklist:
        """Возвращает объект Blacklist для создания правил черного списка."""
        return Blacklist(self)
    
    def whitelist(self) -> Whitelist:
        """Возвращает объект Whitelist для создания правил белого списка."""
        return Whitelist(self)
    
    def range(self, min_val: Union[int, float], max_val: Union[int, float]) -> "HTMLValidator":
        """Проверка, что значение в заданном диапазоне."""
        return self._add_rule("range", min_val=min_val, max_val=max_val)
    
    def regex(self, pattern: str) -> "HTMLValidator":
        """Проверка значения по регулярному выражению."""
        return self._add_rule("regex", pattern=pattern)
    
    def exists(self) -> "HTMLValidator":
        """Проверка существования пути."""
        return self._add_rule("exists")
    
    def type(self, expected_type: Type) -> "HTMLValidator":
        """Проверка типа значения."""
        return self._add_rule("type", expected_type=expected_type)
    
    def validate(self, html_data: str | bytes) -> tuple[bool, Optional[ValidationError]]:
        """
        Выполняет валидацию HTML данных.
        
        Args:
            html_data: HTML данные для валидации (строка или bytes)
            
        Returns:
            Tuple[bool, Optional[ValidationError]]: (успешность валидации, ошибка если есть)
        """
        if not self._rules:
            return True, None
        
        # Парсим HTML
        try:
            if isinstance(html_data, bytes):
                tree = html.fromstring(html_data)
            else:
                tree = html.fromstring(html_data.encode('utf-8') if isinstance(html_data, str) else html_data)
        except Exception as e:
            return False, self._create_error(
                rule_type="exists",
                expected_values=[self.xpath],
                received_values=[],
                message=f"Не удалось распарсить HTML: {str(e)}",
            )
        
        # Извлекаем значения по xpath
        try:
            matches = tree.xpath(self.xpath)
            # Преобразуем элементы в строки или текстовое содержимое
            matches = [elem.text if hasattr(elem, 'text') and elem.text else str(elem) for elem in matches]
        except Exception as e:
            return False, self._create_error(
                rule_type="exists",
                expected_values=[self.xpath],
                received_values=[],
                message=f"Не удалось распарсить xpath '{self.xpath}': {str(e)}",
            )
        
        # Если нет совпадений и требуется exists, это ошибка
        if not matches:
            for rule in self._rules:
                if rule["type"] == "exists":
                    return False, self._create_error(
                        rule_type="exists",
                        expected_values=[self.xpath],
                        received_values=[],
                        message=f"XPath '{self.xpath}' не существует",
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
                    value_str = str(value)
                    value_lower = value_str.lower()
                    found_words = [word for word in rule["words"] if word.lower() in value_lower]
                    if found_words:
                        return False, self._create_error(
                            rule_type="blacklist.words",
                            expected_values=[f"не содержать слова: {rule['words']}"],
                            received_values=[f"содержит: {found_words}"],
                            message=f"Значение '{value_str}' содержит запрещенные слова: {found_words}",
                        )
                
                elif rule_type == "whitelist_words":
                    value_str = str(value)
                    value_lower = value_str.lower()
                    found_words = [word for word in rule["words"] if word.lower() in value_lower]
                    if not found_words:
                        return False, self._create_error(
                            rule_type="whitelist.words",
                            expected_values=[f"содержать хотя бы одно слово из: {rule['words']}"],
                            received_values=[value_str],
                            message=f"Значение '{value_str}' не содержит ни одного разрешенного слова из {rule['words']}",
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
                    try:
                        num_value = float(value) if not isinstance(value, (int, float)) else value
                    except (ValueError, TypeError):
                        return False, self._create_error(
                            rule_type="range",
                            expected_values=[f"число в диапазоне [{min_val}, {max_val}]"],
                            received_values=[value],
                            message=f"Значение {value} не является числом",
                        )
                    if not (min_val <= num_value <= max_val):
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
                    value_str = str(value)
                    value_lower = value_str.lower()
                    found_words = [word for word in rule["words"] if word.lower() in value_lower]
                    if found_words:
                        return False, self._create_error(
                            rule_type="blacklist_words",
                            expected_values=[f"не содержать слова: {rule['words']}"],
                            received_values=[f"содержит: {found_words}"],
                            message=f"Значение '{value_str}' содержит запрещенные слова: {found_words}",
                        )
                
                elif rule_type == "whitelist_words":
                    value_str = str(value)
                    value_lower = value_str.lower()
                    found_words = [word for word in rule["words"] if word.lower() in value_lower]
                    if not found_words:
                        return False, self._create_error(
                            rule_type="whitelist_words",
                            expected_values=[f"содержать хотя бы одно слово из: {rule['words']}"],
                            received_values=[value_str],
                            message=f"Значение '{value_str}' не содержит ни одного разрешенного слова из {rule['words']}",
                        )
        
        return True, None

