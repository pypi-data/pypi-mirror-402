import pytest

from pydantic import BaseModel
from typing import Union, List
from ul_api_utils.validators.custom_fields import QueryParamsSeparatedList


class ModelStr(BaseModel):
    param: QueryParamsSeparatedList[str]


class ModelInt(BaseModel):
    param: QueryParamsSeparatedList[int]


@pytest.mark.parametrize(
    "model, input_data, expected_output",
    [
        pytest.param(ModelStr, "first_array_element,second,third,this", ["first_array_element", "second", "third", "this"]),
        pytest.param(ModelStr, ["first_array_element,second,third,this"], ["first_array_element", "second", "third", "this"]),
        pytest.param(ModelInt, ["1,2,3,4,5"], [1, 2, 3, 4, 5]),
        pytest.param(ModelStr, 'first_array_element,"second,third",this', ["first_array_element", "second,third", "this"]),
        pytest.param(ModelStr, ['first_array_element,"second,third",this'], ["first_array_element", "second,third", "this"]),
        pytest.param(ModelStr, '"first_array_element,second,third",this, "1,2"', ["first_array_element,second,third", "this", "1,2"]),
    ],
)
def test__query_params_separated_list(
    model: Union[ModelStr, ModelInt], input_data: Union[List[str], str], expected_output: List[Union[str, int]],
) -> None:
    instance = model(param=input_data)  # type: ignore
    assert isinstance(instance.param, list)
    assert instance.param == expected_output
