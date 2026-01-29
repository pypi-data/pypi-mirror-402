from django.contrib import admin
from django.contrib.staticfiles.urls import urlpatterns as static_urlpatterns
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('webcomment.api_urls.all')),
    path('widget/threads/', include('webcomment.widget.urls')),
    path('s/', include('webcomment.webmention.urls')),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('schema/openapi', SpectacularAPIView.as_view(), name='schema'),
    path('schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
] + static_urlpatterns
