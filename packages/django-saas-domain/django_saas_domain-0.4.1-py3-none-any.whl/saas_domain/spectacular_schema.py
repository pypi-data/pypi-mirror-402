from drf_spectacular.extensions import OpenApiViewExtension
from drf_spectacular.utils import extend_schema


class DomainListEndpoint(OpenApiViewExtension):
    target_class = 'saas_domain.endpoints.domain.DomainListEndpoint'

    def view_replacement(self):
        class Fixed(self.target_class):
            @extend_schema(
                operation_id='domains_list',
                summary='List Domains',
            )
            def get(self, *args, **kwargs):
                pass

            @extend_schema(
                operation_id='domains_add',
                summary='Add Domain',
            )
            def post(self, *args, **kwargs):
                pass

        return Fixed


class DomainItemEndpoint(OpenApiViewExtension):
    target_class = 'saas_domain.endpoints.domain.DomainItemEndpoint'

    def view_replacement(self):
        class Fixed(self.target_class):
            @extend_schema(
                operation_id='domains_retrieve',
                summary='Retrieve Domain',
            )
            def get(self, *args, **kwargs):
                pass

            @extend_schema(
                operation_id='domains_update',
                summary='Re-add Domain',
            )
            def post(self, *args, **kwargs):
                pass

            @extend_schema(
                operation_id='domains_destroy',
                summary='Remove Domain',
            )
            def delete(self, *args, **kwargs):
                pass

        return Fixed
