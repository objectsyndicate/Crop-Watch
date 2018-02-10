from django import template

register = template.Library()


@register.filter(name='addcss')
def addcss(field, css):
    return field.as_widget(attrs={"class": css})


@register.filter(name='toggle')
def toggle(field, toggle):
    return field.as_widget(attrs={"data-toggle": toggle, 'data-size': "mini", "data-on": "Yes", "data-off": "No",
                                  'data-onstyle': 'success', 'data-offstyle': 'danger'})


@register.filter(name='yearly')
def yearly(field, yearly):
    return field.as_widget(
        attrs={"data-toggle": "toggle", 'data-size': "large", "data-on": "Yearly", "data-off": "Monthly",
               'data-onstyle': 'primary', 'data-offstyle': 'primary'})
