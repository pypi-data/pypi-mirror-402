from functools import wraps

from django.http import Http404
from django.shortcuts import get_object_or_404

from .models import Indicator


def get_indicator_from_url_name(view_func):
    """
    Decorator that retrieves an Indicator from the URL 'name' parameter.

    Replaces the 'name' parameter with the actual 'indicator' object.
    Raises Http404 if the indicator is not found or is not active.
    """

    @wraps(view_func)
    def wrapper(request, name, *args, **kwargs):
        indicator = get_object_or_404(Indicator, name=name)
        if not indicator.is_active:
            raise Http404("Indicator is not active.")
        return view_func(request, indicator=indicator, *args, **kwargs)

    return wrapper
