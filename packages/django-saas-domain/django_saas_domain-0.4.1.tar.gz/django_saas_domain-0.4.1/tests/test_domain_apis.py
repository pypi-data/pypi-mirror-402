from saas_base.models import Member
from saas_base.test import SaasTestCase

from saas_domain.models import Domain

TEST_DATA = {
    'hostname': 'example.com',
    'provider': 'null',
}


class TestDomainAPIWithOwner(SaasTestCase):
    def test_list_domains(self):
        self.force_login(self.OWNER_USER_ID)

        resp = self.client.get('/m/domains/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])

        Domain.objects.create(tenant=self.tenant, hostname='example.com')
        resp = self.client.get('/m/domains/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 1)
        self.assertEqual(resp.json()[0]['hostname'], 'example.com')

    def test_create_domain(self):
        self.force_login(self.OWNER_USER_ID)
        resp = self.client.post('/m/domains/', data=TEST_DATA)
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data['hostname'], 'example.com')
        self.assertFalse(data['verified'])
        domain_id = data['id']
        resp = self.client.get(f'/m/domains/{domain_id}/?verify=true')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()['verified'])

    def test_create_domain_with_invalid_provider(self):
        self.force_login(self.OWNER_USER_ID)
        payload = {
            'hostname': 'example.com',
            'provider': 'invalid',
        }
        resp = self.client.post('/m/domains/', data=payload)
        self.assertEqual(resp.status_code, 400)


class TestDomainAPIWithGuestUser(SaasTestCase):
    def test_list_domains_with_read_permission(self):
        user = self.force_login(self.MEMBER_USER_ID)
        Member.objects.create(tenant=self.tenant, user=user, role='MEMBER')

        resp = self.client.get('/m/domains/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])

        Domain.objects.create(tenant=self.tenant, hostname='example.com')
        resp = self.client.get('/m/domains/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 1)
        self.assertEqual(resp.json()[0]['hostname'], 'example.com')

    def test_list_domains_without_permission(self):
        self.force_login(self.GUEST_USER_ID)
        resp = self.client.get('/m/domains/')
        self.assertEqual(resp.status_code, 403)

    def test_create_domain_with_admin_permission(self):
        user = self.force_login(self.ADMIN_USER_ID)
        Member.objects.create(tenant=self.tenant, user=user, role='ADMIN')
        resp = self.client.post('/m/domains/', data=TEST_DATA)
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.json()['hostname'], 'example.com')
        self.assertEqual(resp.json()['verified'], False)

    def test_create_domain_with_read_permission(self):
        user = self.force_login(self.MEMBER_USER_ID)
        Member.objects.create(tenant=self.tenant, user=user, role='MEMBER')
        resp = self.client.post('/m/domains/', data=TEST_DATA)
        self.assertEqual(resp.status_code, 403)

    def test_retrieve_domain_with_read_permission(self):
        self.force_login(self.MEMBER_USER_ID)
        domain = Domain.objects.create(
            tenant=self.tenant,
            hostname='example.com',
            provider='null',
        )
        resp = self.client.get(f'/m/domains/{domain.pk}/')
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get(f'/m/domains/{domain.pk}/?verify=true')
        self.assertEqual(resp.status_code, 403)

    def test_enable_and_refresh_domain(self):
        user = self.force_login(self.ADMIN_USER_ID)
        Member.objects.create(tenant=self.tenant, user=user, role='ADMIN')
        domain = Domain.objects.create(
            tenant=self.tenant,
            hostname='example.com',
            provider='null',
        )

        # enable domain
        resp = self.client.post(f'/m/domains/{domain.pk}/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['instrument']['ownership_status'], 'pending')

    def test_delete_domain_with_admin_permission(self):
        self.force_login(self.ADMIN_USER_ID)

        domain = Domain.objects.create(tenant=self.tenant, hostname='example.com')
        resp = self.client.delete(f'/m/domains/{domain.pk}/')
        self.assertEqual(resp.status_code, 204)
