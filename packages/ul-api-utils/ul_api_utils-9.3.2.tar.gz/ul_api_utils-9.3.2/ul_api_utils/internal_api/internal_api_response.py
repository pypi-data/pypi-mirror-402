import json
import uuid
from enum import IntEnum, unique
from functools import cached_property
from typing import Any, Optional, List, Generic, Type, TypeVar, Union, Dict, NamedTuple

import requests
from pydantic import ValidationError

from ul_api_utils.api_resource.api_response import JsonApiResponsePayload, RootJsonApiResponsePayload
from ul_api_utils.api_resource.signature_check import set_model
from ul_api_utils.const import RESPONSE_PROP_DEBUG_STATS, RESPONSE_PROP_PAYLOAD, RESPONSE_PROP_OK, RESPONSE_PROP_ERRORS, RESPONSE_PROP_TOTAL, RESPONSE_PROP_COUNT, MIME__JSON, \
    RESPONSE_HEADER__CONTENT_TYPE
from ul_api_utils.errors import Server5XXInternalApiError, Client4XXInternalApiError, \
    ResponseStatusAbstractInternalApiError, ResponsePayloadTypeInternalApiError, ResponseJsonSchemaInternalApiError, ResponseJsonInternalApiError
from ul_api_utils.internal_api.internal_api_check_context import internal_api_check_context_rm_response, internal_api_check_context_add_response
from ul_api_utils.utils.api_format import ApiFormat
from ul_api_utils.internal_api.internal_api_error import InternalApiResponseErrorObj
from ul_api_utils.utils.unwrap_typing import UnwrappedOptionalObjOrListOfObj

TPyloadType = TypeVar('TPyloadType', bound=Union[JsonApiResponsePayload, List[JsonApiResponsePayload], RootJsonApiResponsePayload[Any], List[RootJsonApiResponsePayload[Any]], None])
TResp = TypeVar('TResp', bound='InternalApiResponse[Any]')


CHECK_TYPE = {'payload_type', 'json', 'std_schema'}


class InternalApiResponseSchema(NamedTuple):
    response_ok: bool
    response_status_code: int
    response_payload_raw: Any
    response_errors: List[InternalApiResponseErrorObj]
    response_total_count: Optional[int]
    response_count: Optional[int]
    response_many: bool


@unique
class InternalApiResponseCheckLevel(IntEnum):
    STATUS_CODE = 1
    JSON = 2
    STD_SCHEMA = 3
    PAYLOAD_TYPE = 4

    def __repr__(self) -> str:
        return f'{type(self).__name__}.{self.name}'


class InternalApiOverriddenResponse(NamedTuple):
    status_code: int
    text: str
    headers: Dict[str, str]

    @property
    def content(self) -> bytes:
        return self.text.encode('utf-8')

    def json(self) -> Any:
        return json.loads(self.text)


class InternalApiResponse(Generic[TPyloadType]):

    @property
    def id(self) -> uuid.UUID:
        return self._id

    def __init__(self, info: str, resp: Union[requests.Response, InternalApiOverriddenResponse], std_schema: bool, payload_type: Optional[Type[TPyloadType]]) -> None:
        self._id = uuid.uuid4()
        self._resp = resp
        self._has_std_schema = std_schema
        self._payload_type = None

        self._parsed_schema: Optional[InternalApiResponseSchema] = None
        self._parsed_json: Any = None
        self._parsed_payload: Union[None, JsonApiResponsePayload, List[JsonApiResponsePayload], RootJsonApiResponsePayload[Any], List[RootJsonApiResponsePayload[Any]]] = None

        self._status_checked = False
        self._info = info

        if payload_type is not None:
            self._payload_type = UnwrappedOptionalObjOrListOfObj.parse(payload_type, JsonApiResponsePayload) or UnwrappedOptionalObjOrListOfObj.parse(payload_type, RootJsonApiResponsePayload)
            if self._payload_type is None:
                tn1, tn2 = JsonApiResponsePayload.__name__, RootJsonApiResponsePayload.__name__
                raise ValueError(
                    f'payload_typing is invalid. must be Union[Type[{tn1} | {tn2}], Optional[Type[{tn1} | {tn2}]], List[Type[{tn1} | {tn2}]], Optional[List[Type[{tn1} | {tn2}]]]]. {payload_type} was given',
                )

    def typed(self, payload_type: Type[TPyloadType]) -> 'InternalApiResponse[TPyloadType]':
        assert payload_type is not None
        internal_api_check_context_rm_response(self._id)
        new_one = InternalApiResponse(self._info, self._resp, self._has_std_schema, payload_type)
        internal_api_check_context_add_response(new_one)
        return new_one

    @property
    def has_payload_type(self) -> bool:
        return self._payload_type is not None

    @property
    def many(self) -> bool:
        if self._payload_type is not None:
            return self._payload_type.many
        return self._schema.response_many

    # ERROR HANDLING

    def check(self: TResp, *, level: InternalApiResponseCheckLevel = InternalApiResponseCheckLevel.PAYLOAD_TYPE) -> TResp:
        assert isinstance(level, InternalApiResponseCheckLevel)
        self._raise_for_err(self._status_code_error)

        if level < InternalApiResponseCheckLevel.JSON:
            return self
        self._raise_for_err(self._result_json_error)

        if level < InternalApiResponseCheckLevel.STD_SCHEMA:
            return self
        self._raise_for_err(self._result_json_schema_error)

        if level < InternalApiResponseCheckLevel.PAYLOAD_TYPE:
            return self

        if self._payload_type is None:
            return self

        self._raise_for_err(self._payload_type_error)
        return self

    @cached_property
    def _schema(self) -> InternalApiResponseSchema:
        self._raise_for_err(self._status_code_error, self._status_checked)
        self._raise_for_err(self._result_json_error)
        self._raise_for_err(self._result_json_schema_error)
        assert self._parsed_schema is not None
        return self._parsed_schema

    @cached_property
    def _payload_type_error(self) -> Optional[ResponsePayloadTypeInternalApiError]:
        if self._payload_type is None:
            return ResponsePayloadTypeInternalApiError('payload type is invalid', ValueError('payload_type for response must be specified'))

        try:
            assert self._parsed_schema is not None
            self._parsed_payload = self._payload_type.apply(self._parsed_schema.response_payload_raw, set_model)
        except Exception as e:  # noqa: B902
            return ResponsePayloadTypeInternalApiError('payload schema type is not valid', e)
        return None

    @cached_property
    def _result_json_schema_error(self) -> Optional[ResponseJsonSchemaInternalApiError]:
        ok = self._resp.status_code < 400
        payload_raw = self._parsed_json
        errors = []
        response_many = isinstance(payload_raw, list)
        total_count = len(payload_raw) if response_many else None
        count = len(payload_raw) if response_many else None

        if self._has_std_schema:
            try:
                assert isinstance(self._parsed_json, dict)
                ok = self._parsed_json.get(RESPONSE_PROP_OK, False)
                total_count = self._parsed_json.get(RESPONSE_PROP_TOTAL, None)
                assert count is None or isinstance(total_count, int), f'total_count must be int. "{type(total_count).__name__}" was given'
                count = self._parsed_json.get(RESPONSE_PROP_COUNT, None)
                assert count is None or isinstance(count, int), f'count must be int. "{type(count).__name__}" was given'
                payload_raw = self._parsed_json.get(RESPONSE_PROP_PAYLOAD, None)
                response_many = isinstance(payload_raw, list)

                if response_many:
                    assert count is not None and count >= 0
                    assert total_count is not None and total_count >= 0

                errors = self._mk_std_errors(self._parsed_json)
            except Exception as e:  # noqa: B902
                return ResponseJsonSchemaInternalApiError('invalid schema', e)

        self._parsed_schema = InternalApiResponseSchema(
            response_ok=ok,
            response_status_code=self._resp.status_code,
            response_payload_raw=payload_raw,
            response_errors=errors,
            response_total_count=total_count,
            response_count=count,
            response_many=response_many,
        )
        return None

    @property
    def _internal_use__checked_once(self) -> bool:
        return self._status_checked

    @property
    def _internal_use__info(self) -> str:
        return self._info

    @cached_property
    def _result_json_error(self) -> Optional[ResponseJsonInternalApiError]:
        content_mime: str = self._resp.headers.get(RESPONSE_HEADER__CONTENT_TYPE, MIME__JSON)
        api_format = ApiFormat.from_mime(content_mime)
        if api_format is None:
            return ResponseJsonInternalApiError('content is not parsable as json', ValueError(f'content type "{content_mime}" was given'))

        try:
            self._parsed_json = api_format.parse_bytes(self._resp.content)
        except Exception as e:  # noqa: B902
            return ResponseJsonInternalApiError('content is not parsable as json', e)
        return None

    def _mk_std_errors(self, result_json: Dict[str, Any]) -> List[InternalApiResponseErrorObj]:
        if not isinstance(result_json, dict):
            return []  # type: ignore
        return [set_model(InternalApiResponseErrorObj, error) for error in result_json.get(RESPONSE_PROP_ERRORS, [])]

    @cached_property
    def _status_code_error(self) -> Optional[ResponseStatusAbstractInternalApiError]:
        self._status_checked = True
        code = self._resp.status_code

        if code >= 400:
            errors = []
            if self._has_std_schema and self._result_json_error is None:
                try:
                    errors = self._mk_std_errors(self._parsed_json)
                except ValidationError:
                    pass
            return Server5XXInternalApiError(code, errors) if code >= 500 else Client4XXInternalApiError(code, errors)
        return None

    def _raise_for_err(self, err: Optional[Exception], checked: bool = False) -> None:
        if not checked and err is not None:
            raise err

    # STANDARD PAYLOAD SCHEMA PROPERTIES

    @property
    def ok(self) -> bool:
        return self._schema.response_ok

    @property
    def total_count(self) -> Optional[int]:
        sch = self._schema
        if not sch.response_many:
            raise OverflowError('count it is not permitted for not array payload')
        return sch.response_total_count

    @property
    def count(self) -> Optional[int]:
        sch = self._schema
        if not sch.response_many:
            raise OverflowError('count it is not permitted for not array payload')
        return sch.response_count

    @property
    def errors(self) -> List[InternalApiResponseErrorObj]:
        return self._schema.response_errors

    @property
    def payload_raw(self) -> Union[Optional[Dict[str, Any]], List[Dict[str, Any]]]:  # for backward compatibility
        return self._schema.response_payload_raw

    @property
    def payload(self) -> TPyloadType:
        _sch = self._schema  # noqa: F841
        self._raise_for_err(self._payload_type_error)
        return self._parsed_payload  # type: ignore

    @cached_property
    def internal_use__debug_stats(self) -> List[List[Any]]:
        if not self._has_std_schema:
            return []
        if self._result_json_error is not None or self._parsed_json is None:
            return []
        return self._parsed_json.get(RESPONSE_PROP_DEBUG_STATS, [])

    # STANDARD PAYLOAD PROPS

    @property
    def status_code(self) -> int:
        self._raise_for_err(self._status_code_error, self._status_checked)
        return self._resp.status_code

    @property
    def result_bytes(self) -> bytes:
        self._raise_for_err(self._status_code_error, self._status_checked)
        return self._resp.content

    @property
    def result_text(self) -> str:
        self._raise_for_err(self._status_code_error, self._status_checked)
        return self._resp.text

    @property
    def result_json(self) -> Any:
        self._raise_for_err(self._status_code_error, self._status_checked)
        self._raise_for_err(self._result_json_error)
        return self._parsed_json
