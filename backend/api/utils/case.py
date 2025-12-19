import re
from typing import Any, List, Union

CAMEL_REGEX = re.compile('(?<=.)_(\\w)')
SNAKE_REGEX = re.compile('(?<=[a-z])([A-Z])')

def match_upper(match: Any) -> Any:
    return match.group(1).upper()

def match_snake(match: Any) -> Any:
    return f'_{match.group(1).lower()}'

def to_camelcase(text: Any) -> Any:
    return CAMEL_REGEX.sub(match_upper, text)

def to_snake_case(text: Any) -> Any:
    return SNAKE_REGEX.sub(match_snake, text)

JsonValue = Union[None, str, int, float, bool,
                  List[Any], dict[str, Any]]

def to_camelcase_data(data: JsonValue) -> JsonValue:
    if isinstance(data, dict):
        return {to_camelcase(k): to_camelcase_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [to_camelcase_data(datum) for datum in data]
    else:
        return data

def to_snake_case_data(data: JsonValue) -> JsonValue:
    if isinstance(data, dict):
        return {to_snake_case(k): to_snake_case_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [to_snake_case_data(datum) for datum in data]
    else:
        return data