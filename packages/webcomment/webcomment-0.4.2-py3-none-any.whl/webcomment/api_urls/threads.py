from django.urls import path

from ..endpoints.threads import ThreadListEndpoint, ThreadStatusEndpoint

urlpatterns = [
    path('', ThreadListEndpoint.as_view()),
    path('<pk>/status/', ThreadStatusEndpoint.as_view()),
]
