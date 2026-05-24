from django.urls import path

from apps.common.views import HealthView, ReadyView


urlpatterns = [
    path("", HealthView.as_view(), name="health"),
    path("ready/", ReadyView.as_view(), name="ready"),
]
