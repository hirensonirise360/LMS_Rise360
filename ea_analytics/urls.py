from django.urls import path
from . import views

urlpatterns = [
    path("", views.analytics_dashboard, name="ea_analytics_dashboard"),
]
