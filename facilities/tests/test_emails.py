from django.test import TestCase
from django.urls import reverse
import json
from facilities.models import *


class SendEmailsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.agency_id = SDP_agencies.objects.create(name="CDC").pk
        cls.partner_id = Partners.objects.create(name="CRISSP Plus",
                                                 agency=SDP_agencies.objects.get(pk=cls.agency_id )).pk
        cls.org_appr = Organization_HIS_approvers.objects.create(organization=Partners.objects.get(pk=cls.partner_id),
                                                                 email="maria@gmail.com").pk

    def test_send_email(self):
        # response = self.client.get('/send_email')
        # self.assertEqual(response.status_code, 200)
        email_post = {
            "facility_id": "daaa11d8-e800-4625-8ef7-354382e07272",
            "username": "test username",
            "mfl_code": 99999,
            "partner": self.partner_id,
            "frontend_url": "http://localhost:3000/"
        }

        response = self.client.post('/send_email',
                                    json.dumps(email_post),
                                    content_type="application/json")
        self.assertEqual(response.status_code, 200)

    def test_send_customized_email(self):
        email_post = {
            "facility_id": "daaa11d8-e800-4625-8ef7-354382e07272",
            "username": "test username",
            "mfl_code": 99999,
            "partner": self.partner_id,
            "frontend_url": "http://localhost:3000/"
        }
        response = self.client.post('/new_facility_send_email',
                                    json.dumps(email_post),
                                    content_type="application/json")
        self.assertEqual(response.status_code, 200)

    def test_send_email_view(self):
        email_post = {
            "facility_id": "daaa11d8-e800-4625-8ef7-354382e07272",
            "mfl_code": 99999,
            "choice": 'rejected',
            "reason" :'not a good idea',
            "partner": self.partner_id,
            "user_edited_email": "maria20@yahoo.com"
        }
        response = self.client.post('/send_customized_email',
                                    json.dumps(email_post),
                                    content_type="application/json")
        self.assertEqual(response.status_code, 200)




