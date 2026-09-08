"""
WSGI config for config project.
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# --- Vercel requires 'app'/'application' at module top-level (static parse check) ---
# Define fallback first, then overwrite if Django loads OK.
def application(environ, start_response):
    start_response("500 Internal Server Error", [("Content-Type", "text/plain")])
    return [b"Django failed to start. Check Vercel environment variables."]

app = application  # Vercel looks for this name

try:
    from django.core.wsgi import get_wsgi_application
    _django_app = get_wsgi_application()

    # Overwrite with the real Django app
    application = _django_app
    app = _django_app

except Exception:
    def application(environ, start_response):  # noqa: F811
        start_response("500 Internal Server Error", [("Content-Type", "text/plain; charset=utf-8")])
        return [b"Service temporarily unavailable."]

    app = application
