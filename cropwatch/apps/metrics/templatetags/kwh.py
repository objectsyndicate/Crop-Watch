from django import template

register = template.Library()


@register.filter(name='kwh')
def kwh(kwhm, kwh_cost):
    return format(int(kwhm) * kwh_cost, '.2f')
