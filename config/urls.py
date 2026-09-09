from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views import defaults as default_views
from django.conf.urls.i18n import i18n_patterns
from django.views.i18n import JavaScriptCatalog

from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.views.generic import RedirectView, TemplateView

handler400 = "config.error_views.bad_request"
handler403 = "config.error_views.permission_denied"
handler404 = "config.error_views.page_not_found"
handler500 = "config.error_views.server_error"

def is_authorized_admin(request):
    """Custom permission check for the admin site, permitting active staff and superusers."""
    user = request.user
    return user.is_active and (user.is_staff or user.is_superuser)

# Override admin permission to secure it as requested originally
admin.site.has_permission = is_authorized_admin
admin.site.site_header = "RISE360 Institute Admin"
admin.site.site_title = "RISE360 Institute Admin"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    path("", lambda request: redirect("/en/", permanent=False)),  # Root redirect → /en/
    path("robots.txt", lambda r: HttpResponse(
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /en/ea/portal/\n"
        "Disallow: /en/accounts/\n\n"
        "Sitemap: https://www.rise360institute.com/sitemap.xml\n",
        content_type="text/plain"
    )),
    path("sitemap.xml", lambda r: redirect("/en/ea/sitemap.xml", permanent=True)),
    path("favicon.ico", RedirectView.as_view(url=settings.STATIC_URL + "favicon.ico")),
    path("favicon.png", RedirectView.as_view(url=settings.STATIC_URL + "favicon.png")),
    path("sw.js", TemplateView.as_view(template_name="sw.js", content_type="application/javascript"), name="sw.js"),
    path("offline/", TemplateView.as_view(template_name="offline.html"), name="offline"),
]

urlpatterns += i18n_patterns(
    path("jsi18n/", JavaScriptCatalog.as_view(), name="javascript-catalog"),
    path("", include("core.urls")),
    # path("jet/", include("jet.urls", "jet")),           # Disabled — jet removed
    # path("jet/dashboard/", include("jet.dashboard.urls", "jet-dashboard")),
    path("accounts/", include("accounts.urls")),
    path("programs/", include("course.urls")),
    path("search/", include("search.urls")),
    # EA Exam Prep
    path("ea/", include("ea_exam.urls")),
    path("ea/content/", include("ea_content.urls")),
)


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
