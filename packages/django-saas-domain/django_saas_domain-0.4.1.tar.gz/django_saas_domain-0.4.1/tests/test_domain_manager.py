from unittest.mock import patch

from saas_base.test import SaasTestCase

from saas_domain.models import Domain, DomainManager


class TestDomainManager(SaasTestCase):
    def test_not_found(self):
        with patch.object(DomainManager, 'get', side_effect=Domain.DoesNotExist()) as mock_get:
            value = Domain.objects.get_tenant_id('google.com')
            self.assertIsNone(value)

            # trigger get from cache
            value = Domain.objects.get_tenant_id('google.com')
            self.assertIsNone(value)
            self.assertEqual(mock_get.call_count, 1)

    def test_found(self):
        tenant = self.get_tenant()
        Domain.objects.create(tenant=tenant, hostname='example.com')

        with patch.object(DomainManager, 'get', side_effect=Domain.DoesNotExist()) as mock_get:
            value = Domain.objects.get_tenant_id('example.com')
            self.assertEqual(value, tenant.pk)

            value = Domain.objects.get_tenant_id('example.com')
            self.assertEqual(value, tenant.pk)
            mock_get.assert_not_called()

    def test_purge_tenant_events(self):
        from saas_domain.providers import NullProvider

        tenant = self.get_tenant()
        Domain.objects.create(tenant=tenant, hostname='example.com', provider='null')

        with patch.object(NullProvider, 'remove_domain') as remove_domain:
            tenant.delete()
            remove_domain.assert_called_once()

    def test_disable_domain(self):
        tenant = self.get_tenant()
        domain = Domain.objects.create(tenant=tenant, hostname='example.com')
        domain.disable()
        self.assertFalse(domain.verified)
