from typing import Dict, List, Any

from ul_api_utils.internal_api.internal_api_error import InternalApiResponseErrorObj


class AbstractApiError(Exception):
    """
    Ошибки которые наследуются от этого класса используются
    - для отделения ошибок НАШЕГО приложения от всех других.
    АБСТРАКТНЫЙ КЛАСС = НАПРЯМУЮ НЕ ИСПОЛЬЗУЕТСЯ для raise
    """
    pass


class AbstractInternalApiError(AbstractApiError):
    """
    Ошибки которые наследуются от этого класса используются
    - ТОЛЬКО для отделения ошибок запроса во внешнее API
    АБСТРАКТНЫЙ КЛАСС = НАПРЯМУЮ НЕ ИСПОЛЬЗУЕТСЯ для raise
    """
    pass


class RequestAbstractInternalApiError(AbstractInternalApiError):
    """
    Ошибки которые наследуются от этого класса используются
    - для отделения ошибок ДО обработки запроса сторонним сервером
    АБСТРАКТНЫЙ КЛАСС = НАПРЯМУЮ НЕ ИСПОЛЬЗУЕТСЯ для raise
    """
    def __init__(self, message: str, error: Exception) -> None:
        assert isinstance(message, str), f'message must be str. "{type(message).__name__}" was given'
        assert isinstance(error, Exception), f'error must be Exception. "{type(error).__name__}" was given'
        super(RequestAbstractInternalApiError, self).__init__(f'{message} :: {error}')
        self.error = error


class NotFinishedRequestInternalApiError(RequestAbstractInternalApiError):
    pass


class ResponseAbstractInternalApiError(AbstractInternalApiError):
    """
    Ошибки которые наследуются от этого класса используются
    - для фильтрации ошибок произошедших После успешного получения информации от стороннеего АПИ
    - но произошедшего по причине некорркетного статуса/формата пэйлоада и пр
    АБСТРАКТНЫЙ КЛАСС = НАПРЯМУЮ НЕ ИСПОЛЬЗУЕТСЯ для raise
    """
    pass


class NotCheckedResponseInternalApiError(ResponseAbstractInternalApiError):
    pass


class ResponseFormatInternalApiError(ResponseAbstractInternalApiError):
    pass


class ResponseDataAbstractInternalApiError(ResponseAbstractInternalApiError):
    """
    Ошибки которые наследуются от этого класса используются
    - для фильтрации ошибок произошедших После успешного получения информации от стороннеего АПИ
    - но произошедшего по причине некорркетного статуса/формата пэйлоада и пр
    АБСТРАКТНЫЙ КЛАСС = НАПРЯМУЮ НЕ ИСПОЛЬЗУЕТСЯ для raise
    """
    def __init__(self, message: str, error: Exception) -> None:
        assert isinstance(message, str), f'message must be str. "{type(message).__name__}" was given'
        assert isinstance(error, Exception), f'error must be Exception. "{type(error).__name__}" was given'
        super(ResponseDataAbstractInternalApiError, self).__init__(f'{message} :: {error}')
        self.error = error


class ResponseJsonInternalApiError(ResponseDataAbstractInternalApiError):
    pass


class ResponseJsonSchemaInternalApiError(ResponseDataAbstractInternalApiError):
    pass


class ResponsePayloadTypeInternalApiError(ResponseDataAbstractInternalApiError):
    pass


class ResponseStatusAbstractInternalApiError(ResponseAbstractInternalApiError):
    """
    Ошибки которые наследуются от этого класса используются
    - если сервер выдал ошибку со статусом (явным или неявным) >= 400
    АБСТРАКТНЫЙ КЛАСС = НАПРЯМУЮ НЕ ИСПОЛЬЗУЕТСЯ для raise
    """

    def __init__(self, status_code: int, errors: List[InternalApiResponseErrorObj]) -> None:
        assert isinstance(status_code, int), f'status_code must be int. "{type(status_code).__name__}" was given'
        assert status_code >= 400
        super(ResponseStatusAbstractInternalApiError, self).__init__(f'status code error :: {status_code} :: {[e.model_dump() for e in errors]}')
        self.status_code = status_code
        self.errors = errors


class Server5XXInternalApiError(ResponseStatusAbstractInternalApiError):
    """
    Ошибки которые наследуются от этого класса используются
    - если сервер выдал ошибку со статусом (явным или неявным) >= 500
    = ЧТОТО ПОШЛО НЕ ТАК на сервере
    """
    def __init__(self, status_code: int, errors: List[InternalApiResponseErrorObj]) -> None:
        assert 500 <= status_code
        super(Server5XXInternalApiError, self).__init__(status_code, errors)


class Client4XXInternalApiError(ResponseStatusAbstractInternalApiError):
    """
    Ошибки которые наследуются от этого класса используются
    - если сервер выдал ошибку со статусом (явным или неявным) >= 400 < 500
    = ЧТО ТО ОТПРАВИЛ НЕ ТО с клиента
    """
    def __init__(self, status_code: int, errors: List[InternalApiResponseErrorObj]) -> None:
        assert 400 <= status_code < 500
        super(Client4XXInternalApiError, self).__init__(status_code, errors)


class UserAbstractApiError(AbstractApiError):
    """
    Ошибки которые наследуются от этого класса используются
    - ТОЛЬКО для остановки обработки запроса с мгновенным выходом
    - используются СТРОГО в обработчиках ресурсов (роутах) API-приложения
    АБСТРАКТНЫЙ КЛАСС = НАПРЯМУЮ НЕ ИСПОЛЬЗУЕТСЯ для raise
    """
    pass


class ValidationListApiError(UserAbstractApiError):
    def __init__(self, errors: List[Dict[str, str]]):
        super().__init__(f'validation errors: {errors}')
        self.errors = errors


class ValidateApiError(UserAbstractApiError):
    def __init__(self, code: str, location: list[Any], msg_template: str, input: Any = None):
        self.code = code
        self.location = location
        self.msg_template = msg_template
        self.input = input

    def __str__(self):  # type: ignore
        return (
            f"{self.msg_template} (code={self.code}, location={self.location}, "
            f"input={self.input})"
        )


class SimpleValidateApiError(UserAbstractApiError):
    pass


class AccessApiError(UserAbstractApiError):
    pass


class PermissionDeniedApiError(UserAbstractApiError):
    pass


class NoResultFoundApiError(UserAbstractApiError):
    pass


class HasAlreadyExistsApiError(UserAbstractApiError):
    pass


class InvalidContentTypeError(UserAbstractApiError):
    pass


class RuntimeAbstractApiError(AbstractApiError):
    """
    Ошибки которые наследуются от этого класса используются
    - ТОЛЬКО для обозначения внештатной ситуации
    - НЕ используется для пользовательского кода.
    - СТРОГО внутрення ошибка сервера (назначенная АПИ-УТИЛС)
    = обозначает то что чтото пошло не так
    АБСТРАКТНЫЙ КЛАСС = НАПРЯМУЮ НЕ ИСПОЛЬЗУЕТСЯ для raise
    """
    pass


class ResourceRuntimeApiError(RuntimeAbstractApiError):
    pass


class ResponseTypeRuntimeApiError(RuntimeAbstractApiError):
    pass


class WrapInternalApiError(Exception):

    def __init__(self, message: str, error: AbstractInternalApiError) -> None:
        super().__init__(message)
        self.error = error
