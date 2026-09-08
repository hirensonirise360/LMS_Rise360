import logging

from django.db import DatabaseError
from django.http import JsonResponse
from django.shortcuts import render

logger = logging.getLogger(__name__)


class SafeExceptionMiddleware:
    """
    Prevent sensitive backend/database exception details from reaching users.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except DatabaseError:
            logger.exception("Database error while processing path=%s", request.path)
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse(
                    {"success": False, "error": "Request could not be completed."},
                    status=500,
                )
            return render(request, "500.html", status=500)
