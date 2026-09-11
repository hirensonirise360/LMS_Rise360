import django.template.context

# Python 3.14 compatibility patch for Django BaseContext.__copy__
# Python 3.14 changed copy(super()) behavior, causing AttributeError when cloning Django Admin template context.
def _base_context_copy_py314(self):
    duplicate = object.__new__(self.__class__)
    duplicate.__dict__.update(self.__dict__)
    duplicate.dicts = self.dicts[:]
    return duplicate

django.template.context.BaseContext.__copy__ = _base_context_copy_py314
