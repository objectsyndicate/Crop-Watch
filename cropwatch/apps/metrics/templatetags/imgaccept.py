from django import template

register = template.Library()


@register.filter(name='imgaccept')
def imgaccept(field, css):
    return field.as_widget(attrs={"accept": css})
