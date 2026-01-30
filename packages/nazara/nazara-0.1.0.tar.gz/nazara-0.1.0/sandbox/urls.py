from django.contrib import admin
from django.urls import path

from sandbox.views import health, ready

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health),
    path("ready/", ready),
]
