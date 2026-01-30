from typing import Type, Dict, Any, Optional, List, Set

from pydantic import BaseModel

# CODE FROM https://github.com/godatadriven/pydantic-avro/blob/main/src/pydantic_avro/base.py


def get_avro_schema(model: Type[BaseModel], by_alias: bool = True, namespace: Optional[str] = None) -> Dict[str, Any]:
    schema = model.schema(by_alias=by_alias)
    return {
        "type": "record",
        "namespace": schema["title"] if namespace is None else namespace,
        "name": schema["title"],
        "fields": _get_fields(schema, set()),
    }


def _get_type(schema: Dict[str, Any], value: Dict[str, Any], classes_seen: Set[str]) -> Dict[str, Any]:
    """Returns a type of single field"""
    t = value.get("type")
    f = value.get("format")
    r = value.get("$ref")
    a = value.get("additionalProperties")
    avro_type_dict: Dict[str, Any] = {}
    if "default" in value:
        avro_type_dict["default"] = value.get("default")
    if "description" in value:
        avro_type_dict["doc"] = value.get("description")
    if "allOf" in value and len(value["allOf"]) == 1:
        r = value["allOf"][0]["$ref"]
    if r is not None:
        class_name = r.replace("#/definitions/", "")
        if class_name in classes_seen:
            avro_type_dict["type"] = class_name
        else:
            d = _get_definition(r, schema)
            if "enum" in d:
                avro_type_dict["type"] = {
                    "type": "enum",
                    "symbols": [str(v) for v in d["enum"]],
                    "name": d["title"],
                }
            else:
                avro_type_dict["type"] = {
                    "type": "record",
                    "fields": _get_fields(d, classes_seen),
                    # Name of the struct should be unique true the complete schema
                    # Because of this the path in the schema is tracked and used as name for a nested struct/array
                    "name": class_name,
                }
            classes_seen.add(class_name)
    elif t == "array":
        items: Dict[str, Any] = value.get("items")  # type: ignore
        tn: Dict[str, Any] = _get_type(schema, items, classes_seen)
        # If items in array are a object:
        if "$ref" in items:
            tn = tn["type"]
        # If items in array are a logicalType
        if (
            isinstance(tn, dict)
            and isinstance(tn.get("type", {}), dict)
            and tn.get("type", {}).get("logicalType") is not None
        ):
            tn = tn["type"]
        avro_type_dict["type"] = {"type": "array", "items": tn}
    elif t == "string" and f == "date-time":
        avro_type_dict["type"] = {
            "type": "long",
            "logicalType": "timestamp-micros",
        }
    elif t == "string" and f == "date":
        avro_type_dict["type"] = {
            "type": "int",
            "logicalType": "date",
        }
    elif t == "string" and f == "time":
        avro_type_dict["type"] = {
            "type": "long",
            "logicalType": "time-micros",
        }
    elif t == "string" and f == "uuid":
        avro_type_dict["type"] = {
            "type": "string",
            "logicalType": "uuid",
        }
    elif t == "string":
        avro_type_dict["type"] = "string"
    elif t == "number":
        avro_type_dict["type"] = "double"
    elif t == "integer":
        # integer in python can be a long
        avro_type_dict["type"] = "long"
    elif t == "boolean":
        avro_type_dict["type"] = "boolean"
    elif t == "object":
        if a is None:
            value_type = "string"
        else:
            value_type = _get_type(schema, a, classes_seen)  # type: ignore
        if isinstance(value_type, dict) and len(value_type) == 1:  # type: ignore
            value_type = value_type.get("type")  # type: ignore
        avro_type_dict["type"] = {"type": "map", "values": value_type}
    else:
        raise NotImplementedError(f"Type '{t}' not support yet, please report this at https://github.com/godatadriven/pydantic-avro/issues")
    return avro_type_dict


def _get_definition(ref: str, schema: Dict[str, Any]) -> Dict[str, Any]:
    """Reading definition of base schema for nested structs"""
    id = ref.replace("#/definitions/", "")
    d = schema.get("definitions", {}).get(id)
    if d is None:
        raise RuntimeError(f"Definition {id} does not exist")
    return d


def _get_fields(schema: Dict[str, Any], classes_seen: Set[str]) -> List[Dict[str, Any]]:
    """Return a list of fields of a struct"""
    fields = []
    required = schema.get("required", [])
    for key, value in schema.get("properties", {}).items():
        avro_type_dict = _get_type(schema, value, classes_seen)
        avro_type_dict["name"] = key

        if key not in required:
            if avro_type_dict.get("default") is None:
                avro_type_dict["type"] = ["null", avro_type_dict["type"]]
                avro_type_dict["default"] = None

        fields.append(avro_type_dict)
    return fields
