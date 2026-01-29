from rest_framework.mixins import ListModelMixin
from rest_framework.request import Request
from rest_framework.response import Response
from saas_base.drf.decorators import resource_permission
from saas_base.drf.views import TenantEndpoint

from ..models import Domain
from ..providers import get_domain_provider
from ..serializers import DomainSerializer


class DomainListEndpoint(ListModelMixin, TenantEndpoint):
    serializer_class = DomainSerializer
    pagination_class = None
    queryset = Domain.objects.all()

    @resource_permission('security.domain.view')
    def get(self, request: Request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    @resource_permission('security.domain.create')
    def post(self, request: Request, *args, **kwargs):
        tenant_id = self.get_tenant_id()
        serializer: DomainSerializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        domain = serializer.save(tenant_id=tenant_id)
        provider = get_domain_provider(domain.provider)
        if provider:
            provider.add_domain(domain)
            serializer = self.get_serializer(domain)
        return Response(serializer.data, status=201)


class DomainItemEndpoint(TenantEndpoint):
    serializer_class = DomainSerializer
    queryset = Domain.objects.all()

    def get_required_permission(self):
        if self.request.query_params.get('verify'):
            return 'security.domain.verify'
        return 'security.domain.view'

    def get(self, request: Request, *args, **kwargs):
        domain = self.get_object()
        if request.query_params.get('verify'):
            provider = get_domain_provider(domain.provider)
            if provider:
                provider.verify_domain(domain)
        serializer: DomainSerializer = self.get_serializer(domain)
        return Response(serializer.data)

    @resource_permission('security.domain.manage')
    def post(self, request: Request, *args, **kwargs):
        domain = self.get_object()
        provider = get_domain_provider(domain.provider)
        if provider:
            provider.add_domain(domain)
        serializer: DomainSerializer = self.get_serializer(domain)
        return Response(serializer.data)

    @resource_permission('security.domain.manage')
    def delete(self, request: Request, *args, **kwargs):
        domain = self.get_object()
        provider = get_domain_provider(domain.provider)
        if provider:
            provider.remove_domain(domain)
        domain.delete()
        return Response(status=204)
