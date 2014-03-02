from django import template

register = template.Library()

@register.filter(name='get')
def get(tab, i):
    return tab[int(float(i))]