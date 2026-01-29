from django.urls import include, path

urlpatterns = [
    path('api/', include('webcomment.api_urls.all')),
    path('widget/threads/', include('webcomment.widget.urls')),
    path('s/', include('webcomment.webmention.urls')),
]
