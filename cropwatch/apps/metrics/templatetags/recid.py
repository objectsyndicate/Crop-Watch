from django import template

register = template.Library()


@register.filter(name='recid')
def recid(field, id):
    i = 0

    return field.as_widget(attrs={"id": id})
