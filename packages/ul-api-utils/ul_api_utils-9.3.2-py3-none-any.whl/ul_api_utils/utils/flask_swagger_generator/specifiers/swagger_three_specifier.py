import inspect
import io
import json
import re
from datetime import datetime
from typing import Callable, List, Union, Any, Optional

from pydantic import BaseModel
from pydantic.v1.fields import FieldInfo

from ul_api_utils.access import PermissionDefinition
from ul_api_utils.utils.flask_swagger_generator.exceptions import SwaggerGeneratorError
from ul_api_utils.utils.flask_swagger_generator.specifiers.swagger_models import SwaggerModel
from ul_api_utils.utils.flask_swagger_generator.specifiers.swagger_specifier import SwaggerSpecifier
from ul_api_utils.utils.flask_swagger_generator.utils.input_type import InputType
from ul_api_utils.utils.flask_swagger_generator.utils.replace_in_dict import replace_value_in_dict
from ul_api_utils.utils.flask_swagger_generator.utils.request_type import RequestType
from ul_api_utils.utils.flask_swagger_generator.utils.security_type import SecurityType


class SwaggerSecurity(SwaggerModel):

    def __init__(self, function_names: List[str], security_type: SecurityType) -> None:
        super(SwaggerSecurity, self).__init__()
        self.security_type = security_type
        self.function_names = function_names

    def perform_write(self, file) -> None:  # type: ignore
        if self.security_type.equals(SecurityType.BEARER_AUTH):
            security_entry = inspect.cleandoc(
                """
                    security:
                      - bearerAuth: []
                """,
            )

            security_entry = self.indent(security_entry, 3 * self.TAB)
            file.write(security_entry)
            file.write('\n')

    def perform_component_write(self, file) -> None:  # type: ignore
        if SecurityType.BEARER_AUTH.equals(self.security_type):
            security_entry = inspect.cleandoc(
                """
                    bearerAuth:
                      type: http
                      scheme: bearer
                      bearerFormat: JWT
                """,
            )
            security_entry = self.indent(security_entry, 2 * self.TAB)
            file.write(security_entry)
            file.write('\n')


class SwaggerSchema(SwaggerModel):

    def __init__(self, reference_name: str, schema) -> None:  # type: ignore
        super(SwaggerSchema, self).__init__()
        self.reference_name = reference_name
        self.schema = schema
        self.properties = {}
        self.items = {}
        self.type = 'object'

        if isinstance(schema, type) and issubclass(schema, BaseModel):
            json_schema = schema.model_json_schema()
            if '$ref' in json.dumps(json_schema):
                while '$ref' in json.dumps(json_schema):
                    json_schema = replace_value_in_dict(json_schema.copy(), json_schema.copy())
            if '$defs' in json_schema:
                del json_schema['$defs']
            self.type = json_schema['type']
            if json_schema['type'] == 'object':
                self.properties = json_schema.get('properties', dict())
            elif json_schema['type'] == 'array':
                self.items = json_schema['items']

    @staticmethod
    def get_type(value: Union[int, str, float, List[Any]]) -> InputType:
        if isinstance(value, int):
            return InputType.INTEGER
        elif isinstance(value, str):
            return InputType.STRING
        elif isinstance(value, float):
            return InputType.NUMBER
        elif isinstance(value, list):
            return InputType.ARRAY
        else:
            SwaggerGeneratorError("Type {} is not supported".format(type(value)))  # type: ignore

    def perform_write(self, file) -> None:  # type: ignore
        if self.type == 'object':
            schema_entry = inspect.cleandoc(
                """
                    {}:
                      type: object
                      properties: {}
                """.format(self.reference_name, self.properties),
            )

        if self.type == 'array':
            schema_entry = inspect.cleandoc(
                """
                    {}:
                      type: array
                      items: {}
                """.format(self.reference_name, self.items),
            )
        if self.type == 'null':
            schema_entry = inspect.cleandoc(
                """
                    {}:
                      type: object
                      items: {}
                """.format(self.reference_name, self.items),
            )
        if self.type == 'string':
            schema_entry = inspect.cleandoc(
                """
                    {}:
                      type: string
                      items: {}
                """.format(self.reference_name, self.items),
            )
        schema_entry = self.indent(schema_entry, 2 * self.TAB)
        file.write(schema_entry)
        file.write('\n')


class SwaggerResponses(SwaggerModel):
    def perform_write(self, file) -> None:  # type: ignore
        responses_entry = 'responses:'
        responses_entry = self.indent(responses_entry, 3 * self.TAB)
        file.write(responses_entry)
        file.write('\n')


class SwaggerResponse(SwaggerModel):
    def __init__(
        self,
        function_name: str,
        schema_reference: str,
        status_code: int = 200,
        description: Optional[str] = None,
    ) -> None:
        super(SwaggerResponse, self).__init__()
        self.function_name = function_name
        self.description = description
        self.status_code = status_code
        self.schema_reference = schema_reference
        self.response_reference = function_name + '_response'

    def perform_write(self, file) -> None:  # type: ignore
        response_entry = inspect.cleandoc(
            """
                '{}':
                  $ref: '#/components/responses/{}'
            """.format(self.status_code, self.response_reference),
        )
        response_entry = self.indent(response_entry, 4 * self.TAB)
        file.write(response_entry)
        file.write('\n')

    def perform_component_write(self, file) -> None:  # type: ignore
        if self.description:
            component_entry = inspect.cleandoc(
                """
                   {}:
                     description: {}
                     content:
                        application/json:
                          schema:
                            $ref: '#/components/schemas/{}'
                """.format(
                    self.response_reference,
                    self.description,
                    self.schema_reference,
                ),
            )
        else:
            component_entry = inspect.cleandoc(
                """
                   {}:
                     description: {}
                     content:
                        application/json:
                            schema:
                                $ref: '#/components/schemas/{}'
                """.format(
                    self.response_reference,
                    "{} response".format(self.function_name),
                    self.schema_reference,
                ),
            )

        component_entry = self.indent(component_entry, 2 * self.TAB)
        file.write(component_entry)
        file.write('\n')


class SwaggerRequestBody(SwaggerModel):
    def __init__(
        self,
        function_name: str,
        schema_reference: str,
        description: Optional[str] = None,
        required: bool = True,
    ) -> None:
        super(SwaggerRequestBody, self).__init__()
        self.function_name = function_name
        self.description = description
        self.required = required
        self.request_body_reference = \
            self.function_name + '_request_body'
        self.schema_reference = schema_reference

    def perform_write(self, file) -> None:  # type: ignore
        request_body_entry = inspect.cleandoc(
            """
               requestBody:
                 required: {}
                 content:
                    application/json:
                        schema:
                            $ref: '#/components/schemas/{}'
            """.format(
                self.required,
                self.schema_reference,
            ),
        )
        request_body_entry = self.indent(request_body_entry, 3 * self.TAB)
        file.write(request_body_entry)
        file.write('\n')

    def perform_component_write(self, file) -> None:  # type: ignore
        component_entry = inspect.cleandoc(
            """
               {}:
                 description: {}
                 required: {}
                 content:
                    application/json:
                        schema:
                            $ref: '#/components/schemas/{}'
            """.format(
                self.request_body_reference,
                self.description,
                self.required,
                self.schema_reference,
            ),
        )

        component_entry = self.indent(component_entry, 2 * self.TAB)
        file.write(component_entry)
        file.write('\n')


class SwaggerOperationId(SwaggerModel):
    def __init__(self, function_name: str) -> None:
        super(SwaggerOperationId, self).__init__()
        self.operation_id = function_name

    def perform_write(self, file) -> None:  # type: ignore
        operation_id_entry = "operationId: '{}'".format(self.operation_id)
        operation_id_entry = self.indent(operation_id_entry, 3 * self.TAB)
        file.write(operation_id_entry)
        file.write('\n')


class SwaggerParameters(SwaggerModel):
    def perform_write(self, file) -> None:  # type: ignore
        parameters_entry = "parameters:"
        parameters_entry = self.indent(parameters_entry, 3 * self.TAB)
        file.write(parameters_entry)
        file.write('\n')


class SwaggerTag(SwaggerModel):
    def __init__(self, group_name: str) -> None:
        super(SwaggerTag, self).__init__()
        self.group_name = group_name

    def perform_write(self, file) -> None:  # type: ignore
        group_entry = inspect.cleandoc(
            """
                tags:
                - {}
            """.format(self.group_name),
        )

        group_entry = self.indent(group_entry, 3 * self.TAB)
        file.write(group_entry)
        file.write('\n')


class SwaggerRequestType(SwaggerModel):

    def __init__(self, function_name: str, request_type: RequestType, summary: Optional[str] = None, description: Optional[str] = None) -> None:
        super(SwaggerRequestType, self).__init__()
        self.request_type = request_type
        self.function_name = function_name
        self.summary = summary
        self.description = description

    def perform_write(self, file) -> None:  # type: ignore
        request_type_entry = "{}:".format(self.request_type.value)
        if self.summary is not None:
            request_type_entry += f"\n  summary: {self.summary}"
        if self.description is not None:
            request_type_entry += f"\n  description: |\n{self.TAB}{self.TAB}{self.description}"
        request_type_entry = self.indent(request_type_entry, 2 * self.TAB)

        file.write(request_type_entry)
        file.write('\n')


class SwaggerPathParameter(SwaggerModel):
    def __init__(
        self,
        input_type: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        required: bool = True,
    ) -> None:
        super(SwaggerPathParameter, self).__init__()
        self.input_type = InputType.from_string(input_type)  # type: ignore
        self.name = name
        self.description = f'description: {description}' if description else ''
        self.required = required

    def perform_write(self, file):  # type: ignore
        if self.input_type == InputType.UUID:
            parameter_entry = inspect.cleandoc(
                """
                    - in: path
                      name: {name}
                      schema:
                        type: string
                        format: uuid
                      {description}
                      required: {required}
                """.format(
                    name=self.name,
                    required=self.required,
                    description=self.description,
                ),
            )
        else:
            parameter_entry = inspect.cleandoc(
                """
                    - in: path
                      name: {name}
                      schema:
                        type: {input_type}
                      {description}
                      required: {required}
                """.format(
                    name=self.name,
                    required=self.required,
                    description=self.description,
                    input_type=self.input_type.value,
                ),
            )

        param = self.indent(parameter_entry, 3 * self.TAB)
        file.write(param)
        file.write("\n")


class SwaggerQueryParameter(SwaggerModel):
    def __init__(
        self,
        input_type: Optional[str] = None,
        input_format: Optional[str] = None,
        default_value: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        required: bool = True,
        enum: Optional[list] = None,  # type: ignore
    ) -> None:
        super(SwaggerQueryParameter, self).__init__()
        self.input_type = InputType.from_string(input_type)  # type: ignore
        self.input_format = f'format: {input_format}' if input_format else ''
        self.default_value = f'default: {default_value}' if default_value else ''
        self.name = name
        self.description = f'description: {description}' if description else ''
        self.required = required
        self.enum = enum

    def perform_write(self, file) -> None:  # type: ignore
        if self.input_type.value == InputType.UUID:
            parameter_entry = inspect.cleandoc(
                """
                    - in: query
                      name: {name}
                      schema:
                        type: string
                        format: uuid
                      {default_value}
                      {description}
                      required: {required}
                """.format(
                    name=self.name,
                    required=self.required,
                    description=self.description,
                    default_value=self.default_value,
                ),
            )
        else:
            if self.enum is not None:
                parameter_entry = inspect.cleandoc(
                    """
                        - in: query
                          name: {name}
                          schema:
                            type: {input_type}
                            {input_format}
                            enum: {enum}
                          {default_value}
                          {description}
                          required: {required}
                    """.format(
                        name=self.name,
                        required=self.required,
                        description=self.description,
                        input_type=self.input_type.value,
                        input_format=self.input_format,
                        default_value=self.default_value,
                        enum=self.enum,
                    ),
                )
            else:
                parameter_entry = inspect.cleandoc(
                    """
                        - in: query
                          name: {name}
                          schema:
                            type: {input_type}
                            {input_format}
                          {default_value}
                          {description}
                          required: {required}
                    """.format(
                        name=self.name,
                        required=self.required,
                        description=self.description,
                        input_type=self.input_type.value,
                        input_format=self.input_format,
                        default_value=self.default_value,
                    ),
                )

        param = self.indent(parameter_entry, 3 * self.TAB)
        file.write(param)
        file.write("\n")

    def __hash__(self) -> int:
        return hash(f'{self.input_type}{self.input_format}{self.default_value}{self.name}{self.description}{self.required}')

    def __eq__(self, other: object) -> bool:
        return hash(self) == hash(other)


class SwaggerPath(SwaggerModel):
    def __init__(self, func_name: str, func_object: Callable[..., Any], group: str, path: str, request_types: List[str]) -> None:
        super(SwaggerPath, self).__init__()
        self.func_name = func_name
        self.func_obj = func_object
        self.path = path
        self.group = group
        self.add_request_types(func_name, func_object, request_types)

    def add_request_types(self, function_name, function_object, request_types: List[str]) -> None:  # type: ignore
        for request_type in request_types:
            if request_type not in {'OPTIONS', 'HEAD'}:
                access: PermissionDefinition = function_object.__closure__[0].cell_contents
                swagger_request_type = SwaggerRequestType(
                    function_name,
                    RequestType.from_string(request_type),
                    f'permission={access.category + "/" if access.category else ""}{access.key}({access.id})',
                    function_object.__doc__,
                )
                swagger_request_type.add_swagger_model(SwaggerTag(self.group))
                swagger_request_type.add_swagger_model(SwaggerOperationId(function_name))
                self.add_swagger_model(swagger_request_type)

    def perform_write(self, file) -> None:  # type: ignore
        self.index_path_parameters()
        self.index_query_parameters()
        self.format_path()

        path_entry = "'{path}':".format(path=self.path)
        path = self.indent(path_entry, self.TAB)
        file.write(path)
        file.write("\n")

    def index_query_parameters(self) -> None:
        parameter_models = set()
        query_model = self.func_obj.__annotations__.get('query')
        if query_model is not None and issubclass(query_model, BaseModel):
            swagger_request_types = self.get_swagger_child_models_of_type(SwaggerRequestType)
            for swagger_request_type in swagger_request_types:
                parameters: List[SwaggerModel] = swagger_request_type.get_swagger_child_models_of_type(SwaggerParameters)

                if not parameters:
                    parameters = SwaggerParameters()  # type: ignore
                    swagger_request_type.add_swagger_model(parameters)
                query_schema = query_model.model_json_schema()
                query_required_fields = set(query_schema.get('required')) if query_schema.get('required') is not None else set()
                query_definitions = query_schema.get('$defs')
                for parameter_name, parameter_spec in query_schema.get('properties').items():
                    if 'anyOf' in parameter_spec.keys():
                        if parameter_spec.get('anyOf')[0].get('$ref') is not None:
                            definition = query_definitions.get(parameter_spec.get('$ref', '').split('/')[-1], {})
                            parameter_models.add(SwaggerQueryParameter(
                                input_type=definition.get('type', 'string'),
                                input_format=definition.get('format'),
                                default_value=definition.get('default'),
                                name=parameter_name,
                                description=definition.get('description'),
                                enum=definition.get('enum'),
                                required=parameter_name in query_required_fields,
                            ))
                        if parameter_spec.get('anyOf')[0].get('type') is not None:
                            parameter_models.add(SwaggerQueryParameter(
                                input_type=parameter_spec.get('anyOf')[0].get('type'),
                                input_format=parameter_spec.get('format'),
                                default_value=parameter_spec.get('default'),
                                name=parameter_name,
                                description=parameter_spec.get('description'),
                                required=parameter_name in query_required_fields,
                            ))
                    elif parameter_spec.get('$ref') is not None:
                        definition = query_definitions.get(parameter_spec.get('$ref', '').split('/')[-1], {})
                        parameter_models.add(SwaggerQueryParameter(
                            input_type=definition.get('type', 'string'),
                            input_format=definition.get('format'),
                            default_value=definition.get('default'),
                            name=parameter_name,
                            description=definition.get('description'),
                            enum=definition.get('enum'),
                            required=parameter_name in query_required_fields,
                        ))
                    elif parameter_spec.get('type') is not None:
                        parameter_models.add(SwaggerQueryParameter(
                            input_type=parameter_spec.get('type') or parameter_spec.get('anyOf')[0].get('type'),
                            input_format=parameter_spec.get('format'),
                            default_value=parameter_spec.get('default'),
                            name=parameter_name,
                            description=parameter_spec.get('description'),
                            required=parameter_name in query_required_fields,
                        ))
                if isinstance(parameters, SwaggerModel):
                    parameters.add_swagger_models(parameter_models)
                elif isinstance(parameters, list):
                    for parameter in parameters:
                        parameter.add_swagger_models(parameter_models)

    def index_path_parameters(self) -> None:
        parameters = re.findall("<(.*?)>", self.path)
        swagger_request_types = self.get_swagger_child_models_of_type(SwaggerRequestType)
        parameter_models = []

        if parameters:
            for parameter in parameters:
                if len(parameter.split(':')) > 1:
                    input_type, name = parameter.split(':')
                else:
                    input_type = 'str'
                    name = parameter
                fn_signature = inspect.signature(self.func_obj)
                fn_param_default = fn_signature.parameters.get(name).default  # type: ignore
                description = None
                if isinstance(fn_param_default, FieldInfo):
                    description = fn_param_default.description
                parameter_models.append(SwaggerPathParameter(input_type, name, description, True))

            for swagger_request_type in swagger_request_types:
                parameters: List[SwaggerModel] = swagger_request_type.get_swagger_child_models_of_type(SwaggerParameters)  # type: ignore
                if not parameters:
                    parameters = SwaggerParameters()  # type: ignore
                    swagger_request_type.add_swagger_model(parameters)
                if isinstance(parameters, SwaggerModel):
                    parameters.add_swagger_models(parameter_models)
                elif isinstance(parameters, list):
                    for parameter in parameters:
                        parameter.add_swagger_models(parameter_models)

    def format_path(self) -> None:
        if len(re.findall("<(.*?)>", self.path)) > 0:
            swagger_request_types = self.get_swagger_child_models_of_type(SwaggerRequestType)
            parameters = swagger_request_types[-1].get_swagger_child_models_of_type(SwaggerParameters)
            path_parameters = parameters[-1].get_swagger_child_models_of_type(SwaggerPathParameter)
            query_parameters = parameters[-1].get_swagger_child_models_of_type(SwaggerQueryParameter)
            for path_parameter in path_parameters:
                self.path = self.path.replace(
                    "<{}:{}>".format(path_parameter.input_type.get_flask_input_type_value(), path_parameter.name),
                    "{" + path_parameter.name + "}",
                )
            for query_parameter in query_parameters:
                self.path = self.path.replace(
                    "<{}:{}>".format(query_parameter.input_type.get_flask_input_type_value(), query_parameter.name),
                    "{" + query_parameter.name + "}",
                )


class SwaggerThreeSpecifier(SwaggerModel, SwaggerSpecifier):
    __slots__ = tuple([
        'request_bodies',
        'schemas',
        'responses',
        'securities',
        'swagger_models',
        'application_name',
        'application_version',
    ])

    def __init__(self) -> None:
        super().__init__()
        self.request_bodies = []  # type: ignore
        self.schemas = []  # type: ignore
        self.responses = []  # type: ignore
        self.securities = []  # type: ignore

    def perform_write(self, file) -> None:  # type: ignore
        # Add all request bodies to request_types with same function name
        self._add_request_bodies_to_paths()
        self._add_responses_to_paths()
        self._add_securities_to_paths()

        meta = inspect.cleandoc("""
            openapi: 3.0.1
            info:
              title: {name}
              description: Generated at {time}. This is the swagger
                ui based on the open api 3.0 specification of the {name}
              version: {version}
            externalDocs:
              description: Find out more about Swagger
              url: 'http://swagger.io'
            servers:
              - url: /
            """.format(name=self.application_name, version=self.application_version, time=datetime.now().strftime("%d/%m/%Y %H:%M:%S")),
        )

        file.write(meta)
        file.write("\n")
        file.write("paths:")
        file.write("\n")

    def write(self, file: io.TextIOBase) -> None:
        """
        Overwrite the write method to add some additional functionality.
        After the perform write action the swagger specifier
        wil add the models to the bottom of the swagger definition
        """
        super().write(file)

        file.write('components:')
        file.write('\n')
        if len(self.securities) > 0:
            securities_entry = 'securitySchemes:'
            securities_entry = self.indent(securities_entry, self.TAB)
            file.write(securities_entry)
            file.write('\n')
            for security in self.securities:
                security.perform_component_write(file)

        if len(self.request_bodies) > 0:
            request_bodies_entries = 'requestBodies:'
            request_bodies_entries = self.indent(request_bodies_entries, self.TAB)
            file.write(request_bodies_entries)
            file.write('\n')

            for request_body in self.request_bodies:
                request_body.perform_component_write(file)

        if len(self.responses) > 0:
            response_entries = 'responses:'
            response_entries = self.indent(response_entries, self.TAB)
            file.write(response_entries)
            file.write('\n')

            for response in self.responses:
                response.perform_component_write(file)

        if len(self.schemas) > 0:
            schemas_entries = 'schemas:'
            schemas_entries = self.indent(schemas_entries, self.TAB)
            file.write(schemas_entries)
            file.write('\n')

            for schema in self.schemas:
                schema.perform_write(file)

    def _add_request_bodies_to_paths(self) -> None:
        swagger_paths = self.get_swagger_child_models_of_type(SwaggerPath)
        for swagger_path in swagger_paths:
            # Get the request types
            swagger_request_types = swagger_path.get_swagger_child_models_of_type(SwaggerRequestType)
            for swagger_request_type in swagger_request_types:
                for request_body in self.request_bodies:
                    if swagger_request_type.function_name == request_body.function_name:
                        swagger_request_type.add_swagger_model(request_body)

    def _add_responses_to_paths(self) -> None:
        swagger_paths = self.get_swagger_child_models_of_type(SwaggerPath)

        for swagger_path in swagger_paths:
            # Get the request types
            swagger_request_types = swagger_path.get_swagger_child_models_of_type(SwaggerRequestType)
            for swagger_request_type in swagger_request_types:
                for response in self.responses:
                    if swagger_request_type.function_name == response.function_name:
                        responses_model = swagger_request_type.get_swagger_child_models_of_type(SwaggerResponses)
                        if not responses_model:
                            responses_model = SwaggerResponses()
                            swagger_request_type.add_swagger_model(responses_model)
                        responses_model.add_swagger_model(response)

    def _add_securities_to_paths(self) -> None:
        swagger_paths = self.get_swagger_child_models_of_type(SwaggerPath)
        for swagger_path in swagger_paths:
            swagger_request_types = swagger_path.get_swagger_child_models_of_type(SwaggerRequestType)
            for swagger_request_type in swagger_request_types:
                for security in self.securities:
                    if swagger_request_type.function_name in security.function_names:
                        swagger_request_type.add_swagger_model(security)

    def add_endpoint(self, function_name: str, function_object: Callable[..., Any], path: str, request_types: List[str], group: Optional[str] = None) -> None:  # type: ignore
        if path == '/static/<path:filename>':
            return
        swagger_paths = self.get_swagger_child_models_of_type(SwaggerPath)
        for swagger_path in swagger_paths:
            if swagger_path.path == path:
                swagger_path.add_request_types(function_name, function_object, request_types)
                return
        new_swagger_path = SwaggerPath(function_name, function_object, group, path, request_types)  # type: ignore
        self.add_swagger_model(new_swagger_path)

    def add_response(
        self,
        function_name: str,
        status_code: int,
        schema: Union[SwaggerSchema, type[BaseModel]],
        description: str = "",
    ) -> None:
        if not isinstance(schema, SwaggerSchema):
            schema = SwaggerSchema(function_name + "_response_schema", schema)
            self.schemas.append(schema)
        swagger_response = SwaggerResponse(function_name, schema.reference_name, status_code, description.strip())
        self.responses.append(swagger_response)

    def add_query_parameters(self) -> None:
        pass

    def add_request_body(self, function_name: str, schema) -> None:  # type: ignore
        if not isinstance(schema, SwaggerSchema):
            schema = SwaggerSchema(function_name + "_request_body_schema", schema)
            self.schemas.append(schema)
        swagger_request_body = SwaggerRequestBody(function_name, schema.reference_name)
        self.request_bodies.append(swagger_request_body)

    def add_security(self, function_name: str, security_type: SecurityType) -> None:
        for security in self.securities:
            if security.security_type.equals(security_type):
                security.function_names.append(function_name)
                return
        security_model = SwaggerSecurity([function_name], security_type)
        self.securities.append(security_model)

    def clean(self) -> None:
        self.schemas = []
        self.securities = []
        self.responses = []
        self.swagger_models = []
