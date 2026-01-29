from django.urls import path

from ..endpoints.reactions import ReactionListEndpoint

urlpatterns = [
    path('', ReactionListEndpoint.as_view()),
]
