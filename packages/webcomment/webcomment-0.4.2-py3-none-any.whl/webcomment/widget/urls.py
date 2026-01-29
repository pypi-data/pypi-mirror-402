from django.urls import path

from .endpoints import (
    CommentsEndpoint,
    ReactionsEndpoint,
    ThreadItemEndpoint,
    ThreadResolveEndpoint,
)
from .turnstile import turnstile_view

urlpatterns = [
    path('turnstile', turnstile_view),
    path('resolve', ThreadResolveEndpoint.as_view()),
    path('<thread_id>', ThreadItemEndpoint.as_view()),
    path('<thread_id>/comments', CommentsEndpoint.as_view()),
    path('<thread_id>/reactions', ReactionsEndpoint.as_view()),
]
