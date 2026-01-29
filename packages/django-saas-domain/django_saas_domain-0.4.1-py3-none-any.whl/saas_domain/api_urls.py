from django.urls import path

from .endpoints.domain import DomainItemEndpoint, DomainListEndpoint

urlpatterns = [
    path('', DomainListEndpoint.as_view()),
    path('<pk>/', DomainItemEndpoint.as_view()),
]
