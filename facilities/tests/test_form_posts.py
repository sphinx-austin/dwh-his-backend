from django.test import TestCase
from django.urls import reverse

from ..models import *


class FacilityPostTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.county_id = Counties.objects.create(name="Kisumu").pk
        cls.sub_county_id = Sub_counties.objects.create(name="Kisumu West",county=Counties.objects.get(pk=cls.county_id)).pk
        cls.partner_id = Partners.objects.create(name="HJF-Nairobi").pk
        cls.owner_id = Owner.objects.create(name="Armed Forces").pk
        cls.deployment_id = HTS_deployment_type.objects.create(deployment="Desktop Only").pk
        cls.htsuse_id = HTS_use_type.objects.create(hts_use_name="Desktop Only").pk
        cls.emrtype_id = EMR_type.objects.create(type="KenyaEMR").pk
        cls.facility_id = Facility_Info.objects.create(id=uuid.uuid4(), mfl_code=99998, name="test facility",
                                                county=Counties.objects.get(pk=cls.county_id), sub_county=Sub_counties.objects.get(
                                                    pk=cls.sub_county_id), lat=2.45, lon=3.67, partner=Partners.objects.get(pk=cls.partner_id),
                                                owner=Owner.objects.get(pk=cls.owner_id),
                                                date_added="2019-04-03", year=2022, month=10, kmhfltest_id="daaa11d8-e800-4625-8ef7-354382e07272",
                                                approved=True)

    def test_facilityinfo_post(self):
        self.assertEqual(Facility_Info.objects.count(), 1)
        facility = Facility_Info.objects.create(id=uuid.uuid4(), mfl_code=99999, name="my_new facility",
                                                county=Counties.objects.get(pk=self.county_id), sub_county=Sub_counties.objects.get(
                                                    pk=self.sub_county_id), lat=2.45, lon=3.67, partner=Partners.objects.get(pk=self.partner_id),
                                                owner=Owner.objects.get(pk=self.owner_id),
                                                date_added="2020-10-23", year=2022, month=10, kmhfltest_id="d97d11d8-e800-4625-8ef7-354382e07272",
                                                approved=True)
        facility.save()
        self.assertEqual(Facility_Info.objects.count(), 2)

    def test_editedfacilityinfo_post(self):
        facility = Edited_Facility_Info.objects.create(id=uuid.uuid4(), mfl_code=99999, name="edited test facility",
                                                county=Counties.objects.get(pk=self.county_id), sub_county=Sub_counties.objects.get(
                                                    pk=self.sub_county_id), lat=2.45, lon=3.67, partner=Partners.objects.get(pk=self.partner_id),
                                                owner=Owner.objects.get(pk=self.owner_id),
                                                date_edited="2020-10-23", facility_info=Facility_Info.objects.get(pk=self.facility_id.pk),
                                                user_edited_name="", user_edited_email="")
        facility.save()
        self.assertEqual(Edited_Facility_Info.objects.count(), 1)

    def test_EMR_Info_post(self):
        EMR_Info.objects.create(type=EMR_type.objects.get(pk=self.emrtype_id), status='Active', mode_of_use="",
                                date_of_emr_impl="2022-01-10",
                                ovc=True, otz=True, prep=False,
                                tb=True, kp=True, mnch=False, lab_manifest=False,
                                hiv=True, tpt=True,covid_19=False, evmmc=False,
                            for_version="original",
                            facility_info=Facility_Info.objects.get(pk=self.facility_id.pk)).save()

        self.assertEqual(EMR_Info.objects.count(), 1)

    def test_HTS_Info_post(self):
        HTS_Info.objects.create(hts_use_name=HTS_use_type.objects.get(pk=self.htsuse_id), status='Active',
                                deployment=HTS_deployment_type.objects.get(pk=self.deployment_id),
                            for_version="original",
                            facility_info=Facility_Info.objects.get(pk=self.facility_id.pk)).save()

        self.assertEqual(HTS_Info.objects.count(), 1)

    def test_Implementation_type_post(self):
        Implementation_type.objects.create(ct=True, hts=True, il=True, KP=True, mhealth=True, for_version="original",
                            facility_info=Facility_Info.objects.get(pk=self.facility_id.pk)).save()

        self.assertEqual(Implementation_type.objects.count(), 1)

    def test_IL_Info_post(self):
        IL_Info.objects.create(webADT_registration=True, webADT_pharmacy=True, status=True, three_PM=True,
                              air=True, Ushauri=True, Mlab=True, lab_manifest=True, nimeconfirm =True,
                          for_version="original",
                            facility_info=Facility_Info.objects.get(pk=self.facility_id.pk)).save()

        self.assertEqual(IL_Info.objects.count(), 1)

    def test_MHealth_Info_post(self):
        MHealth_Info.objects.create(Ushauri=True, C4C=True,Nishauri=True, ART_Directory=True,
                                    Psurvey=True, Mlab=True,for_version="original",
                            facility_info=Facility_Info.objects.get(pk=self.facility_id.pk)).save()

        self.assertEqual(MHealth_Info.objects.count(), 1)

