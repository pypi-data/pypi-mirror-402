from django.urls import path

from .views import receive_webmention

urlpatterns = [
    path('<slug>/webmention', receive_webmention),
]
