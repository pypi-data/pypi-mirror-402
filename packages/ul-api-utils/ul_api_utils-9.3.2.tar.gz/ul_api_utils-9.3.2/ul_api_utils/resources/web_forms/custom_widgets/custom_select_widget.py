from typing import Any

from markupsafe import Markup
from wtforms import SelectField  # type: ignore
from wtforms.widgets.core import html_params, Select  # type: ignore


class CustomLiveSearchPlaceholderSelect(Select):
    """
    Renders a CUSTOM select field.

    If `multiple` is True, then the `size` property should be specified on
    rendering to make the field useful.

    The field must provide an `iter_choices()` method which the widget will
    call on rendering; this method must yield tuples of
    `(value, label, selected)`.
    It also must provide a `has_groups()` method which tells whether choices
    are divided into groups, and if they do, the field must have an
    `iter_groups()` method that yields tuples of `(label, choices)`, where
    `choices` is an iterable of `(value, label, selected)` tuples.
    Otherwise, `selected` is False for any option field in select item group.
    """
    def __call__(self, field: SelectField, **kwargs: Any) -> Markup:
        kwargs.setdefault("id", field.id)
        if self.multiple:
            kwargs["multiple"] = True
        flags = getattr(field, "flags", {})
        for k in dir(flags):
            if k in self.validation_attrs and k not in kwargs:
                kwargs[k] = getattr(flags, k)

        html = ["<select data-live-search='true' data-show-subtext='true' %s>" % html_params(name=field.name, **kwargs),
                "<option value='' disabled selected>Select something...</option>"]

        if field.has_groups():
            for group, choices in field.iter_groups():
                html.append("<optgroup %s>" % html_params(label=group))
                for val, label, selected in choices:
                    html.append(self.render_option(val, label, selected))
                html.append("</optgroup>")
        else:
            for val, label, _ in field.iter_choices():
                html.append(self.render_option(val, label, False))
        html.append("</select>")
        return Markup("".join(html))


class CustomLiveSearchSelect(Select):
    """
    Renders a CUSTOM select field.

    If `multiple` is True, then the `size` property should be specified on
    rendering to make the field useful.

    The field must provide an `iter_choices()` method which the widget will
    call on rendering; this method must yield tuples of
    `(value, label, selected)`.
    It also must provide a `has_groups()` method which tells whether choices
    are divided into groups, and if they do, the field must have an
    `iter_groups()` method that yields tuples of `(label, choices)`, where
    `choices` is an iterable of `(value, label, selected)` tuples.
    Otherwise, `selected` is False for any option field in select item group.
    """
    def __call__(self, field: SelectField, **kwargs: Any) -> Markup:
        kwargs.setdefault("id", field.id)
        if self.multiple:
            kwargs["multiple"] = True
        flags = getattr(field, "flags", {})
        for k in dir(flags):
            if k in self.validation_attrs and k not in kwargs:
                kwargs[k] = getattr(flags, k)

        html = ["<select data-live-search='true' data-show-subtext='true' %s>" % html_params(name=field.name, **kwargs)]

        if field.has_groups():
            for group, choices in field.iter_groups():
                html.append("<optgroup %s>" % html_params(label=group))
                for val, label, selected in choices:
                    html.append(self.render_option(val, label, selected))
                html.append("</optgroup>")
        else:
            for val, label, selected in field.iter_choices():
                html.append(self.render_option(val, label, selected))
        html.append("</select>")
        return Markup("".join(html))
