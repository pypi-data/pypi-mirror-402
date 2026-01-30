from typing import Optional, Any

from wtforms import StringField   # type: ignore
from wtforms.widgets import TextInput   # type: ignore
from markupsafe import Markup


class CustomTextInput(TextInput):
    """
    Render a single-line text input with optional input attributes ("required", "maxlength", "minlength", "pattern").

    examples: TextInputCustom(required=True, min_length=5, max_length=255, pattern=r"^(d+(,d+)*)?$")
              TextInputCustom(max_length=255, pattern=r"^(d+(,d+)*)?$")
              TextInputCustom(required=True, pattern=r"^(d+(,d+)*)?$")
              TextInputCustom(max_length=255)
    In model usage: ... info={"label": "LABEL:", "widget": TextInputCustom(pattern=r"^(d+(,d+)*)?$")}
    """
    validation_attrs = ["required", "maxlength", "minlength", "pattern"]

    def __init__(self, required: Optional[bool] = None, max_length: Optional[int] = None, min_length: Optional[int] = None, pattern: Optional[str] = None):
        super().__init__()
        self.required = required
        self.max_length = max_length
        self.min_length = min_length
        self.pattern = pattern

    def __call__(self, field: StringField, **kwargs: Any) -> Markup:
        kwargs.setdefault("id", field.id)
        kwargs.setdefault("type", self.input_type)
        if self.min_length:
            kwargs.setdefault("minlength", self.min_length)
        if self.max_length:
            kwargs.setdefault("maxlength", self.max_length)
        if self.pattern:
            kwargs.setdefault("pattern", self.pattern)
        if "value" not in kwargs:
            kwargs["value"] = field._value()
        flags = getattr(field, "flags", {})
        for k in dir(flags):
            if k in self.validation_attrs and k not in kwargs:
                kwargs[k] = getattr(flags, k)
        return Markup("<input %s>" % self.html_params(name=field.name, **kwargs))
