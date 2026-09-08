from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Template filter to get a value from a dictionary by key."""
    if dictionary is None:
        return None
    # Try the key as is (might be int or str)
    val = dictionary.get(key)
    if val is None:
        # Fallback to string if not found
        val = dictionary.get(str(key))
    return val

@register.filter(name='chr')
def chr_filter(value):
    """Template filter to convert an integer to its character equivalent."""
    try:
        return chr(int(value))
    except (ValueError, TypeError):
        return value


@register.filter
def is_locked_part(part_number):
    """Visual-only: Parts 2 and 3 show locked overlay by default.
    Returns True if the part should appear locked (cosmetic only).
    """
    try:
        return int(part_number) > 1
    except (ValueError, TypeError):
        return False


@register.filter
def subtract(value, arg):
    """Subtract arg from value."""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError, AttributeError):
        return value

@register.filter
def multiply(value, arg):
    """Multiply value by arg."""
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError, AttributeError):
        return value

@register.filter
def divide(value, arg):
    """Divide value by arg."""
    try:
        return int(value) / int(arg) if int(arg) != 0 else 0
    except (ValueError, TypeError, AttributeError):
        return value

@register.filter
def subtract_from(value, arg):
    """Subtract value from arg (arg - value)."""
    try:
        return int(arg) - int(value)
    except (ValueError, TypeError, AttributeError):
        return value
