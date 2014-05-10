from django import template

register = template.Library()

@register.filter(name='get')
def get(tab, i):
    return tab[int(float(i))]

@register.filter(name='addFilter')
def add(filt, f):
	if filt == None:
		return f
	else:
		filt.update(f)
		return (filt)