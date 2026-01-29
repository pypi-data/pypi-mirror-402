from django.urls import path

from ..endpoints.settings import SettingEndpoint

urlpatterns = [
    path('', SettingEndpoint.as_view()),
]
