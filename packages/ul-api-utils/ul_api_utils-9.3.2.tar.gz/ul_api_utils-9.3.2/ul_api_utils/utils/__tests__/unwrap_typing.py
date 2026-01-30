from typing import Optional, List

from pydantic import BaseModel

from ul_api_utils.api_resource.signature_check import set_model
from ul_api_utils.utils.unwrap_typing import UnwrappedOptionalObjOrListOfObj


def test_unwrap_list_obj_apply() -> None:
    class Some(BaseModel):
        value: int

    parsed1: UnwrappedOptionalObjOrListOfObj[Some] = UnwrappedOptionalObjOrListOfObj.parse(Some, None)  # type: ignore
    parsed1_v = parsed1.apply({"value": 1}, set_model)
    assert parsed1_v is not None
    assert parsed1_v.value == 1

    parsed2: UnwrappedOptionalObjOrListOfObj[List[Some]] = UnwrappedOptionalObjOrListOfObj.parse(List[Some], None)  # type: ignore
    parsed2_v = parsed2.apply([{"value": 1}], set_model)
    assert parsed2_v is not None
    assert len(parsed2_v) == 1
    assert parsed2_v[0].value == 1

    parsed3: UnwrappedOptionalObjOrListOfObj[Optional[List[Some]]] = UnwrappedOptionalObjOrListOfObj.parse(Optional[List[Some]], None)  # type: ignore
    parsed3_v = parsed3.apply([{"value": 1}], set_model)
    assert parsed3_v is not None
    assert len(parsed3_v) == 1
    assert parsed3_v[0].value == 1
    assert parsed3.apply(None, set_model) is None

    parsed4: UnwrappedOptionalObjOrListOfObj[Optional[Some]] = UnwrappedOptionalObjOrListOfObj.parse(Optional[Some], None)  # type: ignore
    assert parsed4.apply(None, set_model) is None
    parsed4_v = parsed4.apply({"value": 1}, set_model)
    assert parsed4_v is not None
    assert parsed4_v.value == 1


def test_unwrap_list_obj() -> None:
    class Some:
        pass

    parsed = UnwrappedOptionalObjOrListOfObj.parse(Some, None)  # type: ignore
    assert parsed is not None
    assert parsed.value_type == Some
    assert not parsed.optional
    assert not parsed.many

    parsed = UnwrappedOptionalObjOrListOfObj.parse(List[Some], None)
    assert parsed is not None
    assert parsed.value_type == Some
    assert not parsed.optional
    assert parsed.many

    parsed = UnwrappedOptionalObjOrListOfObj.parse(Optional[Some], None)  # type: ignore
    assert parsed is not None
    assert parsed.value_type == Some
    assert parsed.optional
    assert not parsed.many

    parsed = UnwrappedOptionalObjOrListOfObj.parse(Optional[List[Some]], None)  # type: ignore
    assert parsed is not None
    assert parsed.value_type == Some
    assert parsed.optional
    assert parsed.many

    parsed = UnwrappedOptionalObjOrListOfObj.parse(List[Optional[Some]], None)
    assert parsed is None
