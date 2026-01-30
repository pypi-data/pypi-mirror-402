import inspect
from typing import NamedTuple, Any, Callable, Optional, List, Dict, Type, Tuple, TYPE_CHECKING, Union, get_origin, get_args

from flask import request
from pydantic import BaseModel, ValidationError, validate_call, TypeAdapter, RootModel
from pydantic.v1.utils import deep_update
from pydantic_core import ErrorDetails

from ul_api_utils.api_resource.api_request import ApiRequestQuery
from ul_api_utils.api_resource.api_resource_type import ApiResourceType
from ul_api_utils.api_resource.api_response import HtmlApiResponse, JsonApiResponse, FileApiResponse, \
    RedirectApiResponse, ApiResponse, \
    JsonApiResponsePayload, RootJsonApiResponsePayload, ProxyJsonApiResponse, AnyJsonApiResponse, \
    EmptyJsonApiResponse, TPayloadTotalUnion, RootJsonApiResponse
from ul_api_utils.api_resource.signature_check import get_typing, set_model_dictable, set_model
from ul_api_utils.errors import ValidationListApiError, ResourceRuntimeApiError, InvalidContentTypeError
from ul_api_utils.utils.api_format import ApiFormat
from ul_api_utils.utils.api_method import ApiMethod
from ul_api_utils.utils.json_encoder import to_dict
from ul_api_utils.utils.unwrap_typing import UnwrappedOptionalObjOrListOfObj

if TYPE_CHECKING:
    from ul_api_utils.api_resource.api_resource import ApiResource

FN_SYSTEM_PROPS = {"api_resource", "query", "body", "return", "body_validation_error", "query_validation_error"}


def _is_complex_type(annotation: Any) -> bool:
    origin = get_origin(annotation)

    # Optional[type_] is typing.Union
    if origin is Union:
        return any(_is_complex_type(arg) for arg in get_args(annotation))

    return origin in (list, dict, tuple, set)

def _patch_errors(dest_errors: List[Dict[str, str]], errors: List[ErrorDetails], kind: str) -> List[Dict[str, str]]:
    for error in errors:
        dest_errors.append({
            "error_type": kind,
            "error_message": error['msg'],
            "error_location": error["loc"],  # type: ignore
            "error_kind": error["type"],
            "error_input": error["input"],
        })
    return dest_errors


@validate_call()
def _body_list(root: List[Dict[str, Any]]) -> List[Any]:  # only for pydantic validation
    return root


class ApiResourceFnTyping(NamedTuple):
    fn: Callable[..., ApiResponse]

    request_body_many: bool
    request_body_optional: bool
    response_payload_many: bool

    api_resource_type: ApiResourceType
    signatures_typing: List[Tuple[str, Type[Any]]]

    body_typing: Optional[Type[BaseModel]]  # none if it is not specified
    has_body_validation_error: bool
    query_typing: Optional[Type[ApiRequestQuery]]  # none if it is not specified
    has_query_validation_error: bool
    return_typing: Optional[Type[ApiResponse]]  # NOT NONE for api
    return_payload_typing: Optional[Type[JsonApiResponsePayload] | Type[RootJsonApiResponsePayload[Any]]]  # NOT NONE for api

    def get_return_schema(self) -> Type[BaseModel]:
        inner_type = self.return_payload_typing
        if self.response_payload_many:
            inner_type = List[inner_type]  # type: ignore
        return self.return_typing._internal_use__mk_schema(inner_type)  # type: ignore

    def get_body_schema(self) -> Optional[Type[BaseModel]]:
        if self.body_typing is None:
            return None

        body_typing = self.body_typing

        if self.request_body_optional:
            if self.request_body_many:
                class BodyTypingOptList(RootModel[List[body_typing] | None]):  # type: ignore
                    pass

                return BodyTypingOptList

            class BodyTypingOpt(RootModel[Optional[body_typing]]):  # type: ignore
                pass
            return BodyTypingOpt

        if self.request_body_many:
            class BodyTypingList(RootModel[List[body_typing]]):  # type: ignore
                pass

            return BodyTypingList
        return body_typing

    def runtime_validate_api_proxy_payload(self, response: Dict[str, Any], *, quick: bool) -> None:
        assert isinstance(response, dict)

    def runtime_validate_api_response_payload(self, payload: Any, total_count: Optional[int], *, quick: bool) -> TPayloadTotalUnion:  # type: ignore
        quick = quick or self.return_payload_typing is None

        if self.return_typing == AnyJsonApiResponse:
            return payload, total_count  # type: ignore

        if self.response_payload_many:
            if not (isinstance(total_count, int) and total_count >= 0):
                raise ResourceRuntimeApiError(f'total_count must be int >= 0. {type(total_count).__name__} was given. Error value: {total_count}')
            new_payload = []
            for o in payload:
                r = to_dict(o) if quick else set_model_dictable(self.return_payload_typing, o)  # type: ignore
                if r is None:
                    raise ResourceRuntimeApiError(f'invalid type of object. {type(o).__name__} was given')
                new_payload.append(r)
            return new_payload, total_count

        if payload is None:  # only for case when payload must be single object
            return None, None

        new_payload = to_dict(payload) if quick else set_model_dictable(self.return_payload_typing, payload)  # type: ignore
        if new_payload is None:
            raise ResourceRuntimeApiError(f'invalid type of object. {type(payload).__name__} was given')
        return new_payload, None

    def _get_body(self) -> Optional[Any]:
        if self.api_resource_type == ApiResourceType.WEB:
            res_dict: Dict[str, Any] = {}
            for key, value in request.form.to_dict(flat=False).items():
                if '[]' in key:
                    key = key.replace('[]', '')
                    res_dict[key] = value
                elif '[' in key:
                    key, *dict_keys = key.split('[')
                    dict_keys = [dict_key[:-1] for dict_key in dict_keys]
                    tree_dict: Dict[str, Any] = {}
                    for iter, dict_key in enumerate(reversed(dict_keys)):
                        if iter == 0:
                            tree_dict = {dict_key: value[0]}
                        else:
                            tree_dict = {dict_key: tree_dict}
                    res_dict.setdefault(key, dict())
                    res_dict[key] = deep_update(res_dict[key], tree_dict)
                else:
                    res_dict[key] = value[0]
            return res_dict
        if self.api_resource_type not in (ApiResourceType.API, ApiResourceType.FILE):
            return None
        if not request.is_json:
            body_data: Optional[bytes] = request.get_data()
            api_format = ApiFormat.from_mime(request.mimetype)
            if api_format is None:
                raise InvalidContentTypeError(f"Failed to decode JSON object: invalid content type '{request.mimetype}'")
            return api_format.parse_bytes(body_data) if body_data else None
        else:
            return request.json  # TODO: make this from ApiFormat

    def _runtime_validate_body(self, method: ApiMethod, kwargs: Dict[str, Any], errors: List[Dict[str, str]]) -> Tuple[Dict[str, Any], List[Dict[str, str]]]:
        if self.request_body_optional:
            kwargs['body'] = None
        if method in {ApiMethod.GET, ApiMethod.OPTIONS} or self.body_typing is None:
            return kwargs, errors
        body = self._get_body()
        try:
            expected_typing: Type[BaseModel | List[BaseModel]] = List[self.body_typing] if self.request_body_many else self.body_typing  # type: ignore
            kwargs['body'] = TypeAdapter(expected_typing).validate_python(body)
        except ValidationError as ve:
            if self.has_body_validation_error:
                kwargs['body_validation_error'] = ve
            else:
                _patch_errors(errors, ve.errors(), "body-validation-error")
        return kwargs, errors

    def _runtime_validate_query(self, kwargs: Dict[str, Any], errors: List[Dict[str, str]]) -> Tuple[Dict[str, Any], List[Dict[str, str]]]:
        if self.query_typing is None:
            return kwargs, errors
        try:
            kwargs["query"] = set_model(self.query_typing, {
                **request.args.to_dict(),
                **{
                    key: value for key, value in request.args.to_dict(flat=False).items()
                    if key in self.query_typing.model_fields
                       and _is_complex_type(self.query_typing.model_fields[key].annotation)
                },
            })
        except ValidationError as ve:
            if self.has_query_validation_error:
                kwargs['query_validation_error'] = ve
            else:
                _patch_errors(errors, ve.errors(), "query-validation-error")
        return kwargs, errors

    def _runtime_validate_signature(self, kwargs: Dict[str, Any], errors: List[Dict[str, str]]) -> Tuple[Dict[str, Any], List[Dict[str, str]]]:
        loc_err = []
        for name, type_ in self.signatures_typing:
            try:
                kwargs[name] = TypeAdapter(type_).validate_python(kwargs.get(name))
            except ValidationError as e:
                err = e.errors()[0]
                err["loc"] = [name]  # type: ignore
                loc_err.append(err)
        _patch_errors(errors, loc_err, "path-params-validation-error")
        return kwargs, errors

    def runtime_validate_request_input(self, method: ApiMethod, fn_kwargs: Dict[str, Any]) -> Dict[str, Any]:
        errors: List[Dict[str, str]] = []
        fn_kwargs, errors = self._runtime_validate_signature(fn_kwargs, errors)
        fn_kwargs, errors = self._runtime_validate_query(fn_kwargs, errors)
        fn_kwargs, errors = self._runtime_validate_body(method, fn_kwargs, errors)
        if len(errors) > 0:
            raise ValidationListApiError(errors)
        return fn_kwargs

    @classmethod
    def _parse_body_typing(cls, fn: Callable[['ApiResource'], ApiResponse]) -> Tuple[bool, bool, bool, Optional[Type[BaseModel]]]:
        request_many = False
        body_typing = fn.__annotations__.get('body', None)
        body_validation_error_typing = fn.__annotations__.get('body_validation_error', None)
        body_is_optional = False

        if body_typing is not None:
            body_typing_parsed = UnwrappedOptionalObjOrListOfObj.parse(body_typing, BaseModel)
            tn = BaseModel.__name__
            assert body_typing_parsed is not None, \
                f'body_typing is invalid. must be Union[Type[{tn}], Optional[Type[{tn}]], List[Type[{tn}]], Optional[List[Type[{tn}]]]], {body_typing} was given'
            body_is_optional = body_typing_parsed.optional
            request_many = body_typing_parsed.many
            body_typing = body_typing_parsed.value_type

        if body_validation_error_typing:
            assert body_typing is not None
            assert body_is_optional, 'query typing must be optional'
            body_validation_error_typing_parsed = UnwrappedOptionalObjOrListOfObj.parse(body_validation_error_typing, ValidationError)
            assert body_validation_error_typing_parsed is not None and body_validation_error_typing_parsed.optional and not body_validation_error_typing_parsed.many, \
                f'query_typing is invalid. must be Optional[ValidationError], {body_validation_error_typing} was given'
        return request_many, body_is_optional, body_validation_error_typing is not None, body_typing

    @classmethod
    def _parse_return_typing(
        cls,
        api_resource_type: 'ApiResourceType',
        fn: Callable[['ApiResource'], ApiResponse],
    ) -> Tuple[bool, Optional[Type[JsonApiResponsePayload] | Type[RootJsonApiResponsePayload[Any]]], Optional[Type[ApiResponse]]]:
        response_many = False
        return_typing = fn.__annotations__.get('return', None)
        ret = get_typing(return_typing)
        if len(ret) > 1:
            assert len(ret) == 2, f'invalid generic arguments. must be 1. {len(ret) - 1} was given'
            return_typing, return_payload_typing = ret
        else:
            return_typing, return_payload_typing = ret[0], None

        assert inspect.isclass(return_typing), f'{fn.__name__} :: invalid response typing. {return_typing} was given'

        if return_typing != RedirectApiResponse:
            if api_resource_type == ApiResourceType.API:
                if return_payload_typing is not None:
                    ret_payload_res = get_typing(return_payload_typing)
                    if len(ret_payload_res) > 1:
                        return_payload_typing = ret_payload_res[1]
                        if ret_payload_res[0] != list:  # noqa: E721
                            raise TypeError(f'{fn.__name__} :: invalid response payload type wrapper. only List is supported')
                        response_many = True

                assert return_typing is not None, \
                    f'{fn.__name__} :: invalid response typing. it must be not None. {return_typing}[{return_payload_typing}] was given'

                if return_typing is EmptyJsonApiResponse:
                    assert return_payload_typing is None, f'{fn.__name__} :: invalid response payload typing. payload must be None. {return_payload_typing.__name__} was given'

                elif return_typing is RootJsonApiResponse:
                    assert return_payload_typing is not None and issubclass(return_payload_typing, (JsonApiResponsePayload, RootJsonApiResponsePayload)), \
                        f'{fn.__name__} :: invalid response payload typing. payload must be subclass of (JsonApiResponsePayload, RootJsonApiResponsePayload). ' \
                        f'{return_payload_typing.__name__ if return_payload_typing is not None else "None"} was given'

                elif return_typing is AnyJsonApiResponse:
                    assert return_payload_typing is None, f'{fn.__name__} :: invalid response payload typing. payload must be None. {return_payload_typing.__name__} was given'

                elif issubclass(return_typing, JsonApiResponse):
                    assert return_payload_typing is not None and issubclass(return_payload_typing, (JsonApiResponsePayload, RootJsonApiResponsePayload)), \
                        f'{fn.__name__} :: invalid response payload typing. payload must be subclass of (JsonApiResponsePayload, RootJsonApiResponsePayload). ' \
                        f'{return_payload_typing.__name__ if return_payload_typing is not None else "None"} was given'

                elif issubclass(return_typing, ProxyJsonApiResponse):
                    assert return_payload_typing is not None and issubclass(return_payload_typing, (JsonApiResponsePayload, RootJsonApiResponsePayload)), \
                        f'{fn.__name__} :: invalid response payload typing. payload must be subclass of (JsonApiResponsePayload, RootJsonApiResponsePayload). ' \
                        f'{return_payload_typing.__name__ if return_payload_typing is not None else "None"} was given'

                else:
                    raise TypeError(f'{fn.__name__} :: invalid response typing. {return_typing.__name__} was given')

            elif api_resource_type is ApiResourceType.FILE:
                assert return_typing is not None and issubclass(return_typing, FileApiResponse), \
                    f'{fn.__name__} :: invalid response typing. it must be subclass of HtmlApiResponse. {return_typing.__name__} was given'

            elif api_resource_type is ApiResourceType.WEB:
                assert return_typing is not None and issubclass(return_typing, HtmlApiResponse), \
                    f'{fn.__name__} :: invalid response typing. it must be subclass of HtmlApiResponse. {return_typing.__name__} was given'

        return response_many, return_payload_typing, return_typing

    @classmethod
    def _parse_query_typing(cls, fn: Callable[['ApiResource'], ApiResponse]) -> Tuple[bool, Optional[Type[ApiRequestQuery]]]:
        query_typing = fn.__annotations__.get('query', None)
        query_validation_error_typing = fn.__annotations__.get('query_validation_error', None)
        query_is_optional = False
        if query_typing is not None:
            query_typing_parsed = UnwrappedOptionalObjOrListOfObj.parse(query_typing, ApiRequestQuery)
            tn = ApiRequestQuery.__name__
            assert query_typing_parsed is not None and not query_typing_parsed.many, \
                f'query_typing is invalid. must be Union[Type[{tn}], Optional[Type[{tn}]]], {query_typing} was given'
            query_is_optional = query_typing_parsed.optional

        if query_validation_error_typing:
            assert query_typing is not None
            assert query_is_optional, 'query typing must be optional'
            query_err_typing_parsed = UnwrappedOptionalObjOrListOfObj.parse(query_validation_error_typing, ValidationError)
            assert query_err_typing_parsed is not None and query_err_typing_parsed.optional and not query_err_typing_parsed.many, \
                f'query_typing is invalid. must be Optional[ValidationError], {query_validation_error_typing} was given'
        return query_validation_error_typing is not None, query_typing

    @classmethod
    def parse_fn(cls, api_resource_type: 'ApiResourceType', methods: List[ApiMethod], fn: Callable[['ApiResource'], ApiResponse]) -> 'ApiResourceFnTyping':
        api_resource_typing = fn.__annotations__.get('api_resource', None)
        if api_resource_typing is None or api_resource_typing.__name__ != 'ApiResource':
            raise TypeError(f'{fn.__name__} :: invalid api_resource typing. must be ApiResource. {api_resource_typing} was given')

        request_many, body_is_optional, has_body_validation_error, body_typing = cls._parse_body_typing(fn)
        has_query_validation_error, query_typing = cls._parse_query_typing(fn)
        response_many, return_payload_typing, return_typing = cls._parse_return_typing(api_resource_type, fn)

        for method in methods:
            if method in {ApiMethod.GET, ApiMethod.OPTIONS} and not body_is_optional:
                assert body_typing is None, f'body must be empty for method {method.value}. "{body_typing.__name__}" was given'

        return ApiResourceFnTyping(
            fn=fn,
            api_resource_type=api_resource_type,

            signatures_typing=[(k, v) for k, v in fn.__annotations__.items() if k not in FN_SYSTEM_PROPS],

            body_typing=body_typing,
            has_body_validation_error=has_body_validation_error,
            request_body_many=request_many,
            request_body_optional=body_is_optional,

            query_typing=query_typing,
            has_query_validation_error=has_query_validation_error,

            return_typing=return_typing,
            return_payload_typing=return_payload_typing,
            response_payload_many=response_many,
        )
