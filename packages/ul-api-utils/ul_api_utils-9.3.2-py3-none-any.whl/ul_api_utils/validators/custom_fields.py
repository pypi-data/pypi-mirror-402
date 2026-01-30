import csv
from typing import TypeVar, Generic, List, Union, Annotated, Any, get_args
from uuid import UUID

from pydantic import Field, StringConstraints, BeforeValidator

from ul_api_utils.const import CRON_EXPRESSION_VALIDATION_REGEX, MIN_UTC_OFFSET_SECONDS, MAX_UTC_OFFSET_SECONDS

NotEmptyListAnnotation = Annotated[list[Any], Field(min_length=1)]
NotEmptyListStrAnnotation = Annotated[list[str], Field(min_length=1)]
NotEmptyListIntAnnotation = Annotated[list[int], Field(min_length=1)]
NotEmptyListUUIDAnnotation = Annotated[list[UUID], Field(min_length=1)]
CronScheduleAnnotation = Annotated[str, StringConstraints(pattern=CRON_EXPRESSION_VALIDATION_REGEX)]
WhiteSpaceStrippedStrAnnotation = Annotated[str, StringConstraints(strip_whitespace=True)]
UTCOffsetSecondsAnnotation = Annotated[int, Field(ge=MIN_UTC_OFFSET_SECONDS, le=MAX_UTC_OFFSET_SECONDS)]
PgTypePasswordStrAnnotation = Annotated[str, StringConstraints(min_length=6, max_length=72)]
PgTypeShortStrAnnotation = Annotated[str, StringConstraints(min_length=0, max_length=255)]
PgTypeLongStrAnnotation = Annotated[str, StringConstraints(min_length=0, max_length=1000)]
PgTypeInt16Annotation = Annotated[int, Field(ge=-32768, le=32768)]
PgTypePositiveInt16Annotation = Annotated[int, Field(ge=0, le=32768)]
PgTypeInt32Annotation = Annotated[int, Field(ge=-2147483648, le=2147483648)]
PgTypePositiveInt32Annotation = Annotated[int, Field(ge=0, le=2147483648)]
PgTypeInt64Annotation = Annotated[int, Field(ge=-9223372036854775808, le=9223372036854775808)]
PgTypePositiveInt64Annotation = Annotated[int, Field(ge=0, le=9223372036854775808)]


QueryParamsSeparatedListValueType = TypeVar('QueryParamsSeparatedListValueType')


def validate_query_params(value: Union[str, List[str]], type_: type) -> List[QueryParamsSeparatedListValueType]:
    def process_item(item: str) -> QueryParamsSeparatedListValueType:
        return type_(item.strip())

    if isinstance(value, list):
        result: list[QueryParamsSeparatedListValueType] = []
        for item in value:
            if isinstance(item, str):
                reader = csv.reader([item], skipinitialspace=True)
                result.extend(process_item(sub_item) for row in reader for sub_item in row)
            else:
                raise ValueError("List items must be strings")
    elif isinstance(value, str):
        reader = csv.reader([value], skipinitialspace=True)
        result = [process_item(item) for row in reader for item in row]
    else:
        raise ValueError("Value must be a string or a list of strings")

    return result


class QueryParamsSeparatedList(Generic[QueryParamsSeparatedListValueType]):
    def __init__(self, value: Union[str, List[str]]):
        self._values: List[QueryParamsSeparatedListValueType] = validate_query_params(value)

    def to_list(self) -> List[QueryParamsSeparatedListValueType]:
        return list(self._values)

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: type, handler: Any) -> Any:
        inner_type = get_args(source_type)[0]
        return handler(
            Annotated[
                List[inner_type],  # type: ignore
                BeforeValidator(lambda x: validate_query_params(x, inner_type))
            ]
        )
