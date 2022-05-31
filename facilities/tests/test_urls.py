from django.test import TestCase
from django.urls import reverse
import json
from facilities.models import *


class FacilitiesListViewTest(TestCase):
    def test_homepage_view(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        # self.assertTemplateUsed(response, 'facilities/facilities_list.html')

    def test_sub_counties_lists_all_authors(self):
        # check url is working fine
        response = self.client.get('/facilities/sub_counties')
        self.assertEqual(response.status_code, 200)

    def test_partners_lists_all_authors(self):
        # check url is working fine
        response = self.client.get('/facilities/get_partners_list')
        self.assertEqual(response.status_code, 200)

    def test_agencies_lists_all_authors(self):
        # check url is working fine
        response = self.client.get('/facilities/get_agencies_list')
        self.assertEqual(response.status_code, 200)

