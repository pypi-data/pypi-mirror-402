from typing import Type, Any, Dict, Optional, Tuple

from ul_db_utils.modules.postgres_modules.db import db
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import ARRAY
from wtforms_alchemy import ModelForm, ClassMap, FormGenerator  # type: ignore
from wtforms.fields import SelectField  # type: ignore

from ul_db_utils.model.base_model import BaseModel

from ul_api_utils.resources.web_forms.custom_fields.custom_checkbox_select import MultiCheckboxField


def form_factory(model_obj: Type[BaseModel], edition: bool = False, *, extra_fields: Optional[Dict[str, Any]] = None) -> Type[ModelForm]:
    """
    Returns generated model form.

            Parameters:
                    model_obj (type_of(BaseModel)): model object which will use for form generation
                    edition (bool): flag to indicate creation or edition form will be generated
                    extra_fields (optional(dict(str, any))): additional fields for generated form

            Returns:
                    Form (type_of(ModelForm)): web model form
    """

    class ExtraFieldsFormGenerator(FormGenerator):
        def create_fields(self, form: Any, properties: Dict[str, Any]) -> None:
            """
            Creates fields for given form based on given model attributes.

            :param form: form to attach the generated fields into
            :param properties: model attributes to generate the form fields from
            """
            super(ExtraFieldsFormGenerator, self).create_fields(form, properties)

            if extra_fields:
                for field_name, field in extra_fields.items():
                    setattr(form, field_name, field)

    class Form(ModelForm):
        """
        A class for representing a web form.

        ...

        Attributes
        ----------
        property_columns : dict(str, any)
            Model property columns such as ID, USER_CREATED etc.

        Methods
        -------

        """

        property_columns: Dict[str, Any] = {}

        def __init__(self, *args: Tuple[Any], **kwargs: Dict[str, Any]) -> None:
            super(Form, self).__init__(*args, **kwargs)
            self.property_columns = model_obj.get_property_columns(self._obj) if self._obj else {}

        class Meta:
            model = model_obj
            type_map = ClassMap({postgresql.UUID: SelectField, ARRAY: MultiCheckboxField})
            only = model_obj.get_edit_columns() if edition else model_obj.get_create_columns()
            form_generator = ExtraFieldsFormGenerator

        @classmethod
        def get_session(cls) -> Any:
            return db.session

    Form.__name__ = f"{model_obj.__name__}Form"

    return Form
