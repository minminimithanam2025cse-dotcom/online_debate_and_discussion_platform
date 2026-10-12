from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    if dictionary is None:
        return 0
    if hasattr(dictionary, 'get'):
        return dictionary.get(key, 0)
    return 0


@register.filter
def user_initials(username):
    if not username:
        return '?'
    clean = str(username).strip()
    parts = clean.replace('_', ' ').replace('-', ' ').split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    return clean[:2].upper()
