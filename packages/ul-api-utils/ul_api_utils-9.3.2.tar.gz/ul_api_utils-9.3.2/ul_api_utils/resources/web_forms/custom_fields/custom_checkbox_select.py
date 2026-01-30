from wtforms import SelectMultipleField, widgets  # type: ignore


class MultiCheckboxField(SelectMultipleField):
    option_widget = widgets.CheckboxInput()
