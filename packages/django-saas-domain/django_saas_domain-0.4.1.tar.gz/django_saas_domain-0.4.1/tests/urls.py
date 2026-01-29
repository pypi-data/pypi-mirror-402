from django.urls import include, path
from drf_spectacular.views import SpectacularJSONAPIView

urlpatterns = [
    path('m/domains/', include('saas_domain.api_urls')),
    path('schema/openapi', SpectacularJSONAPIView.as_view(), name='schema'),
]
