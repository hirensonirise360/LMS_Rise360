import time

from django.shortcuts import redirect
from django.urls import resolve, reverse
from django.contrib import messages

# Cache TTL for subscription status (seconds)
# NOTE: we track this via a timestamp stored IN the session, NOT via set_expiry().
# Using set_expiry() would overwrite the session lifetime (e.g. to 5 min) and log
# users out mid-practice when they click "Finish Session".
_SUBSCRIPTION_CACHE_TTL = 300  # 5 minutes


def clear_subscription_cache(request):
    """
    Call this from payment confirmation / activation views to immediately
    invalidate the cached subscription status so the next request re-checks.
    """
    cache_key = f"_sub_active_{request.user.id}"
    request.session.pop(cache_key, None)


class CheckSubscriptionMiddleware:
    """
    Middleware to protect routes.
    Subscription requirement has been removed — all approved users have full access.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)
