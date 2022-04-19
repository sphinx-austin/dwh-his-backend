from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.core.mail import BadHeaderError, send_mail, EmailMessage
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context

from django.conf import settings
from django.http import JsonResponse

from .models import *

from requests.structures import CaseInsensitiveDict
import requests
import json


# get environment variables
import environ
env = environ.Env()
environ.Env.read_env()


def test_email(request):
    demain = request.META['HTTP_HOST']
    print("domain", demain, request.scheme)
    print(request.scheme + request.META[
        'HTTP_HOST'] + '/facilities/update_facility/' + '981893d7-8488-4319-b976-747873551b71')
    context = {
        'news': 'We have good news!',
        'url': request.scheme + "://" + request.META['HTTP_HOST'] + '/facilities/update_facility/',
        'mfl_code': 122345,  # facilitydata.mfl_code,
        'facility_id': '981893d7-8488-4319-b976-747873551b71',  # facilitydata.id
        'username': 123456
    }
    msg_html = render_to_string('facilities/email_template.html', context)
    msg = EmailMessage(subject="Facility Modified", body=msg_html, from_email=settings.DEFAULT_FROM_EMAIL,
                       bcc=['marykilewe@gmail.com'])
    msg.content_subtype = "html"  # Main content is now text/html
    msg.send()
    print('-----------> sending mail ...')
    return 0


@csrf_exempt
def send_email(request):
    # print("see whats sent ---->", request.body)
    data = json.loads(request.body)

    facility_id = data['facility_id']
    username = data['username']
    frontend_url = data['frontend_url']

    # print("request.GET['facility_id']", request.GET['facility_id'], request.GET['username'], request.GET['frontend_url'])

    facility = Facility_Info.objects.get(pk=facility_id)

    context = {
        'news': 'We have good news!',
        'url': frontend_url + '/facilities/approve_changes/',
        'mfl_code': facility.mfl_code,  # facilitydata.mfl_code,
        'facility_id': facility_id,  # facilitydata.id
        'username': username
    }
    his_approver = Organization_HIS_approvers.objects.get(organization=facility.partner.id)
    print('-----------> sending mail ...', his_approver.email)
    msg_html = render_to_string('facilities/email_template.html', context)
    msg = EmailMessage(subject="Facility Modified", body=msg_html, from_email=settings.DEFAULT_FROM_EMAIL,
                       bcc=['marykilewe@gmail.com', his_approver.email])  # , organization.email
    msg.content_subtype = "html"  # Main content is now text/html
    msg.send()
    print('-----------> sending mail ...', his_approver.email)
    return 0



@csrf_exempt
def send_customized_email(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        facility_id = data['facility_id']
        choice = data['choice']
        reason = data['reason']
        print("--------", facility_id)

        facilitydata = Facility_Info.objects.prefetch_related('partner') \
            .select_related('owner').select_related('county') \
            .select_related('sub_county').get(pk=facility_id)

        if choice == "approved":
            message_title = "Approved!"
            message = "Changes you made now reflect on the portal!"
            subject = "Facility Changes Approved!"
        else:
            message_title = "Rejected!"
            message = "Reasons provided for the rejection are : "
            subject = "Facility Changes Rejected!"

        edits = Edited_Facility_Info.objects.get(facility_info=facility_id)
        # user = User.objects.get(pk=edits.user_edited)
        print("the user is", edits.user_edited_name, edits.user_edited_email)

        context = {
            'news': 'We have good news!',
            'url': env("APP_FRONTEND_URL") + '/facilities/update_facility/',
            'mfl_code': facilitydata.mfl_code,
            'facility_id': facilitydata.id,
            "message_title": message_title,
            "reason_given": reason,
            "choice": choice,
            "message": message,
            "user_name": edits.user_edited_name
        }
        msg_html = render_to_string('facilities/customizable_email.html', context)
        msg = EmailMessage(subject=subject, body=msg_html, from_email=settings.DEFAULT_FROM_EMAIL,
                           bcc=[edits.user_edited_email])
        msg.content_subtype = "html"  # Main content is now text/html
        msg.send()
        print('-----------> sending customized mail ...', choice)
    return HttpResponse(0)


def update_kp_implementation(request):
    emr_info = EMR_Info.objects.all()
    for ct_data in emr_info:
        Implementation_type.objects.filter(facility=facility_to_edit).update(KP=ct_data.kp)

    return 0

def fill_database(request):
    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"
    headers["Authorization"] = "Bearer nCDms5vo6dueklfIL3OitjjCkWUtMb"
    url = 'http://api.kmhfltest.health.go.ke/api/facilities/facilities/?format=json'
    response = requests.get(url, headers=headers)

    data = json.loads(response.content)

    for i in range(0, len(data['results'])):
        print("sub county",data['results'][i]['sub_county_name'])
        lat_long = data['results'][i]["lat_long"] if data['results'][i]["lat_long"] else [None, None]
        unique_facility_id = uuid.uuid4()
        facility = Facility_Info.objects.create(id=unique_facility_id, mfl_code=data['results'][i]['code'],
                                                name=data['results'][i]['name'],
                                                county=Counties.objects.get(name=data['results'][i]['county_name']),
                                                sub_county=Sub_counties.objects.get(
                                                    name=data['results'][i]['sub_county_name']),
                                                owner=Owner.objects.get(name=data['results'][i]['owner_type_name']),
                                                # partner=Partners.objects.get(pk=int(form.cleaned_data['partner'])),
                                                lat=lat_long[0],
                                                lon=lat_long[1],
                                                kmhfltest_id=data['results'][i]["id"]
                                                ).save()

        # save Implementation info
        implementation_info = Implementation_type(ct=None, hts=None, il=None,
                                                  for_version="original",
                                                  facility_info=Facility_Info.objects.get(pk=unique_facility_id)).save()

        # save HTS info
        hts_info = HTS_Info(hts_use_name=None, status=None, deployment=None,
                            for_version="original",
                            facility_info=Facility_Info.objects.get(pk=unique_facility_id)).save()

        # save EMR info
        emr_info = EMR_Info(type=None, status=None, ovc=None, otz=None, prep=None,
                            tb=None, kp=None, mnch=None, lab_manifest=None,
                            for_version="original",
                            facility_info=Facility_Info.objects.get(pk=unique_facility_id)).save()

        # save IL info
        il_info = IL_Info(webADT_registration=None, webADT_pharmacy=None, status=None, three_PM=None,
                          for_version="original",
                          facility_info=Facility_Info.objects.get(pk=unique_facility_id)).save()

        # save MHealth info
        mhealth_info = MHealth_Info(Ushauri=None, C4C=None,
                                    Nishauri=None, ART_Directory=None,
                                    Psurvey=None, Mlab=None,
                                    for_version="original",
                                    facility_info=Facility_Info.objects.get(pk=unique_facility_id)).save()

    return HttpResponseRedirect('/home')


@csrf_exempt
def facilities(request):
    facilitiesdata = []

    data = json.loads(request.body)
    print("what was sent back ----------->", data, data['OrganizationId'])

    if data['OrganizationId']:
        organization = Organizations.objects.select_related('org_access_right').get(
            organization_id=data['OrganizationId'])

        if organization.org_access_right:
            facilities_info = Facility_Info.objects.select_related('partner') \
                .select_related('county') \
                .select_related('sub_county').filter(partner__id=organization.org_access_right.id)
        else:
            facilities_info = Facility_Info.objects.prefetch_related('partner') \
                .select_related('county') \
                .select_related('sub_county')
    else:
        facilities_info = Facility_Info.objects.prefetch_related('partner') \
            .select_related('county') \
            .select_related('sub_county')

    for row in facilities_info:
        implementation_info = Implementation_type.objects.get(facility_info=row.id)
        emr_info = EMR_Info.objects.get(facility_info=row.id)
        hts_info = HTS_Info.objects.get(facility_info=row.id)
        il_info = IL_Info.objects.get(facility_info=row.id)
        mhealth_info = MHealth_Info.objects.get(facility_info=row.id)

        ct = "CT" if implementation_info.ct else ""
        hts = "HTS" if implementation_info.hts else ""
        il = "IL" if implementation_info.il else ""

        implementation = [ct, hts, il]

        dataObj = {}
        dataObj["id"] = row.id
        dataObj["mfl_code"] = row.mfl_code
        dataObj["name"] = row.name
        dataObj["county"] = row.county.name
        dataObj["sub_county"] = row.sub_county.name
        dataObj["owner"] = row.owner.name if row.owner else ""
        dataObj["lat"] = row.lat if row.lat else ""
        dataObj["lon"] = row.lon if row.lon else ""
        dataObj["partner"] = row.partner.name if row.partner else ""
        dataObj["agency"] = row.partner.agency.name if row.partner and row.partner.agency else ""
        dataObj["implementation"] = implementation
        dataObj["emr_type"] = emr_info.type.type if emr_info.type else ""
        dataObj["emr_status"] = emr_info.status if emr_info.status else ""
        dataObj["mode_of_use"] = emr_info.mode_of_use if emr_info.mode_of_use else ""
        dataObj["hts_use"] = hts_info.hts_use_name.hts_use_name if hts_info.hts_use_name else ""
        dataObj["hts_deployment"] = hts_info.deployment.deployment if hts_info.deployment else ""
        dataObj["hts_status"] = hts_info.status
        dataObj["il_status"] = il_info.status
        dataObj["il_registration_ie"] = il_info.webADT_registration
        dataObj["il_pharmacy_ie"] = il_info.webADT_pharmacy
        dataObj["mhealth_ovc"] = mhealth_info.Nishauri

        facilitiesdata.append(dataObj)

    return JsonResponse(facilitiesdata,safe=False)


def org_stewards_and_HISapprovers(request):
    allowed_users = [i.email for i in Organization_stewards.objects.all()] + [i.email for i in Organization_HIS_approvers.objects.all()]
    return JsonResponse(allowed_users, safe=False)


def emr_types(request):
    emr_types = [["", ""]] + [(i.id, i.type) for i in EMR_type.objects.all()]
    return JsonResponse(emr_types, safe=False)


def hts_deployment_types(request):
    types = [["", ""]] + [(i.id, i.deployment) for i in HTS_deployment_type.objects.all()]
    return JsonResponse(types, safe=False)


def hts_uses(request):
    uses = [["", ""]] + [[i.id, i.hts_use_name] for i in HTS_use_type.objects.all()]
    return JsonResponse(uses, safe=False)


def owners(request):
    owners = [["", ""]] + [[i.id, i.name] for i in Owner.objects.all()]
    return JsonResponse(owners, safe=False)


def get_agencies_list(request):
    agencies = SDP_agencies.objects.all()

    agencies_list =[]
    for row in agencies:
        agencyObj = {}
        agencyObj['id'] = row.id
        agencyObj['name'] = row.name

        agencies_list.append(agencyObj)

    return JsonResponse(agencies_list, safe=False)


def partners_list(request):
    partners = Partners.objects.select_related('agency').all().order_by('name')
    partners_list = []
    for row in partners:
        subObj = {}
        subObj['id'] = row.id
        subObj['partner'] = row.name
        subObj['agency'] = row.agency.name if row.agency else ""
        subObj['agency_id'] = row.agency.id if row.agency else None

        partners_list.append(subObj)

    return JsonResponse(partners_list, safe=False)


def agencies(request):
    partners = Partners.objects.select_related('agency').all()

    partners_list = []
    for row in partners:
        partnerObj = {}
        partnerObj['partner'] = row.id
        partnerObj['agency'] = {'id': row.agency.id, 'name': row.agency.name} if row.agency else {}

        partners_list.append(partnerObj)

    return JsonResponse(partners_list, safe=False)


@csrf_exempt
def get_mfl_data(request):
    data = json.loads(request.body)
    print(data['code'], type(data['code']))

    facilityObj = {}

    if request.method == 'POST':
        try:

            try:
                Facility_Info.objects.get(mfl_code=int(data['code']))
                facilityObj = {"status": 'data exists'}
            except Facility_Info.DoesNotExist:
                mfl_data = Master_Facility_List.objects.select_related('county').select_related('sub_county')\
                    .select_related('partner').select_related('owner').get(mfl_code=int(data['code']))

                facilityObj['mfl_code'] = mfl_data.mfl_code
                facilityObj['name'] = mfl_data.name
                facilityObj['county'] = mfl_data.county.id
                facilityObj['sub_county'] = mfl_data.sub_county.id
                facilityObj['lat'] = float(mfl_data.lat) if mfl_data.lat else ""
                facilityObj['lon'] = float(mfl_data.lon) if mfl_data.lon else ""
                facilityObj['partner'] = mfl_data.partner.id if mfl_data.partner else ""
                facilityObj['owner'] = mfl_data.owner.id
                facilityObj['agency'] = mfl_data.partner.agency.name if mfl_data.partner else ""
        except Master_Facility_List.DoesNotExist:
            print(request.POST.get('code'), ' doesn\'t exist')

    return JsonResponse(facilityObj, safe=False)


def fetch_facility_data(request, facility_id):
    facility_info = Facility_Info.objects.prefetch_related('partner') \
            .select_related('owner').select_related('county')\
            .select_related('sub_county').get(pk=facility_id)

    facility_data = []
    # try:
    implementation_info = Implementation_type.objects.get(facility_info=facility_info.id)
    emr_info = EMR_Info.objects.get(facility_info=facility_info.id)
    hts_info = HTS_Info.objects.get(facility_info=facility_info.id)
    il_info = IL_Info.objects.get(facility_info=facility_info.id)
    mhealth_info = MHealth_Info.objects.get(facility_info=facility_info.id)

    ct = "CT" if implementation_info.ct else ""
    hts = "HTS" if implementation_info.hts else ""
    il = "IL" if implementation_info.il else ""

    implementation = [ct, hts, il]

    dataObj = {}
    dataObj["id"] = facility_info.id
    dataObj["mfl_code"] = facility_info.mfl_code
    dataObj["name"] = facility_info.name
    dataObj["county"] = facility_info.county.id
    dataObj["sub_county"] = facility_info.sub_county.id
    dataObj["owner"] = facility_info.owner.id if facility_info.owner else ""
    dataObj["lat"] = facility_info.lat if facility_info.lat else ""
    dataObj["lon"] = facility_info.lon if facility_info.lon else ""
    dataObj["partner"] = facility_info.partner.id if facility_info.partner else ""
    dataObj["agency"] = facility_info.partner.agency.name if facility_info.partner and facility_info.partner.agency else ""
    dataObj["CT"]= implementation_info.ct
    dataObj["HTS"]= implementation_info.hts
    dataObj["IL"]= implementation_info.il
    dataObj["mHealth"] = implementation_info.mhealth
    dataObj["KP"] = implementation_info.KP
    dataObj["ovc_offered"]= emr_info.ovc
    dataObj["otz_offered"]= emr_info.otz
    dataObj["tb_offered"]= emr_info.tb
    dataObj["prep_offered"]= emr_info.prep
    dataObj["mnch_offered"]= emr_info.mnch
    dataObj["kp_offered"]= emr_info.kp
    dataObj["lab_man_offered"]= emr_info.lab_manifest
    dataObj["hiv_offered"] = emr_info.hiv
    dataObj["tpt_offered"] = emr_info.tpt
    dataObj["covid_19_offered"] = emr_info.covid_19
    dataObj["evmmc_offered"] = emr_info.evmmc
    dataObj["mhealth_ushauri"]= mhealth_info.Ushauri
    dataObj["mhealth_nishauri"]= mhealth_info.Nishauri
    dataObj["mhealth_c4c"]= mhealth_info.C4C
    dataObj["mhealth_mlab"]= mhealth_info.Mlab
    dataObj["mhealth_psurvey"]= mhealth_info.Psurvey
    dataObj["mhealth_art"]= mhealth_info.ART_Directory
    dataObj["il_status"]= il_info.status
    dataObj["webADT_registration"]= il_info.webADT_registration
    dataObj["webADT_pharmacy"]= il_info.webADT_pharmacy
    dataObj["il_three_PM"]= il_info.three_PM
    dataObj["il_air"] = il_info.air
    dataObj["il_ushauri"] = il_info.Ushauri
    dataObj["il_mlab"] = il_info.Mlab
    dataObj["il_lab_manifest"] = il_info.lab_manifest
    dataObj["il_nimeconfirm"] = il_info.nimeconfirm
    dataObj["emr_type"]= emr_info.type.id if emr_info.type else ""
    dataObj["emr_status"]= emr_info.status
    dataObj["mode_of_use"] = emr_info.mode_of_use
    dataObj["hts_use"]= hts_info.hts_use_name.id if hts_info.hts_use_name else ""
    dataObj["hts_deployment"]= hts_info.deployment.id if hts_info.deployment else ""
    dataObj["hts_status"]= hts_info.status
    facility_data.append(dataObj)
    # except Exception as e:
    #     print(e)

    return JsonResponse(facility_data,safe=False)


@csrf_exempt
def add_facility_data(request):
    data = json.loads(request.body)

    # try:
    unique_facility_id = uuid.uuid4()
    # Save the new category to the database.
    facility = Facility_Info.objects.create(id=unique_facility_id, mfl_code=int(data['mfl_code']),
                                            name=data['name'],
                                            county=Counties.objects.get(
                                                pk=int(data['county'])) if data['county'] != None else None,
                                            sub_county=Sub_counties.objects.get(
                                                pk=int(data['sub_county'])) if data['sub_county'] != None else None,
                                            owner=Owner.objects.get(pk=int(data['owner'])) if data['owner'] != "" else None,
                                            partner=Partners.objects.get(
                                                pk=int(data['partner'])) if data['partner'] != "" else None,
                                            # facilitydata.agency = facilitydata.partner.agency.name
                                            lat=data['lat'] if data['lat'] else None,
                                            lon=data['lon'] if data['lon'] else None,
                                            date_added=datetime.datetime.today(),
                                            )

    # save Implementation info
    implementation_info = Implementation_type(ct=data['CT'], KP=data['KP'],
                                              hts=data['HTS'], il=data['IL'],
                                              mhealth=data['mHealth'],
                                              for_version="original",
                                              facility_info=Facility_Info.objects.get(
                                                  pk=unique_facility_id))

    if data['HTS'] == True:
        # save HTS info
        hts_info = HTS_Info(hts_use_name=HTS_use_type.objects.get(pk=int(data['hts_use'])),
                            status=data['hts_status'],
                            deployment=HTS_deployment_type.objects.get(
                                pk=int(data['hts_deployment'])),
                            for_version="original",
                            facility_info=Facility_Info.objects.get(pk=unique_facility_id))
    else:
        # save HTS info
        hts_info = HTS_Info(hts_use_name=None, status=None, deployment=None,
                            for_version="original",
                            facility_info=Facility_Info.objects.get(pk=unique_facility_id))

    # save EMR info
    if data['CT'] == True:
        emr_info = EMR_Info(type=EMR_type.objects.get(pk=int(data['emr_type'])),
                            status=data['emr_status'], mode_of_use=data['mode_of_use'],
                            ovc=data['ovc_offered'], otz=data['otz_offered'],
                            prep=data['prep_offered'], tb=data['tb_offered'],
                            kp=data['kp_offered'], mnch=data['mnch_offered'],
                            lab_manifest=None,
                            hiv=data['hiv_offered'], tpt=data['tpt_offered'],
                            covid_19=data['covid_19_offered'], evmmc=data['evmmc_offered'],
                            for_version="original",
                            facility_info=Facility_Info.objects.get(pk=unique_facility_id))
    else:
        emr_info = EMR_Info(type=None, status=None, mode_of_use=None, ovc=None, otz=None, prep=None,
                            tb=None, kp=None, mnch=None, lab_manifest=None,
                            hiv=None, tpt=None,covid_19=None, evmmc=None,
                            for_version="original",
                            facility_info=Facility_Info.objects.get(pk=unique_facility_id))

    # save IL info
    if data['IL'] == True:
        il_info = IL_Info(webADT_registration=data['webADT_registration'],
                          webADT_pharmacy=data['webADT_pharmacy'],
                          status=None, three_PM=data['il_three_PM'],
                          air=data['il_air'], Ushauri=data['il_ushauri'],
                          Mlab=data['il_mlab'],
                          lab_manifest=data['il_lab_manifest'], nimeconfirm =data['il_nimeconfirm'],
                          for_version="original",
                          facility_info=Facility_Info.objects.get(pk=unique_facility_id))
    else:
        il_info = IL_Info(webADT_registration=None, webADT_pharmacy=None, status=None, three_PM=None,
                          air=None, Ushauri=None, Mlab=None,lab_manifest=None, nimeconfirm =None,
                          for_version="original",
                          facility_info=Facility_Info.objects.get(pk=unique_facility_id))

    # save MHealth info
    mhealth_info = MHealth_Info(Ushauri=data['mhealth_ushauri'], C4C=data['mhealth_c4c'],
                                Nishauri=data['mhealth_nishauri'],
                                ART_Directory=data['mhealth_art'],
                                Psurvey=data['mhealth_psurvey'], Mlab=data['mhealth_mlab'],
                                for_version="original",
                                facility_info=Facility_Info.objects.get(pk=unique_facility_id))

    try:
        # save to the DB
        facility.save()
        implementation_info.save()
        hts_info.save()
        emr_info.save()
        il_info.save()
        mhealth_info.save()
        return JsonResponse({'status_code': 200, 'redirect_url': 'home/'})
    except Exception as e:
        print(e)
        return JsonResponse({'status_code': 500, 'error':e})


def check_for_facility_edits(request, facility_id):
    # check for edits
    try:
        facility_edits = Edited_Facility_Info.objects.get(facility_info=facility_id)
        return JsonResponse({'status_code': 200, 'facility_edits':True})
    except Edited_Facility_Info.DoesNotExist:
        facility_edits = None
        return JsonResponse({'status_code': 404, 'facility_edits':False})



@csrf_exempt
def update_facility_data(request, facility_id):
    data = json.loads(request.body)
    #print('data ---> ', data)
    print('data ---> ',data['username'], data['email'])
    # try:
    unique_id_for_edit = uuid.uuid4()
    # Save the new category to the database.
    facility = Edited_Facility_Info.objects.create(id=unique_id_for_edit, mfl_code=int(data['mfl_code']),
                                            name=data['name'],
                                            county=Counties.objects.get(
                                                pk=int(data['county'])),
                                            sub_county=Sub_counties.objects.get(
                                                pk=int(data['sub_county'])),
                                            owner=Owner.objects.get(pk=int(data['owner'])),
                                            partner=Partners.objects.get(
                                                pk=int(data['partner'])) if data['partner'] != "" else None,
                                            # facilitydata.agency = facilitydata.partner.agency.name
                                            lat=data['lat'] if data['lat'] else None,
                                            lon=data['lon'] if data['lon'] else None,
                                            facility_info=Facility_Info.objects.get(pk=facility_id),
                                            date_edited=datetime.datetime.today(),
                                            user_edited_name=data['username'],
                                            user_edited_email=data['email']
                                            )

    # save Implementation info
    implementation_info = Implementation_type(ct=data['CT'], KP=data["KP"],
                                              hts=data['HTS'], il=data['IL'],
                                              mhealth=data['mHealth'],
                                              for_version="edited",
                                              facility_edits=Edited_Facility_Info.objects.get(
                                                  pk=unique_id_for_edit))

    if data['HTS'] == True:
        # save HTS info
        hts_info = HTS_Info(hts_use_name=HTS_use_type.objects.get(pk=int(data['hts_use'])),
                            status=data['hts_status'],
                            deployment=HTS_deployment_type.objects.get(
                                pk=int(data['hts_deployment'])),
                            for_version="edited",
                            facility_edits=Edited_Facility_Info.objects.get(pk=unique_id_for_edit))
    else:
        # save HTS info
        hts_info = HTS_Info(hts_use_name=None, status=None, deployment=None,
                            for_version="edited",
                            facility_edits=Edited_Facility_Info.objects.get(pk=unique_id_for_edit))

    # save EMR info
    if data['CT'] == True:
        emr_info = EMR_Info(type=EMR_type.objects.get(pk=int(data['emr_type'])),
                            status=data['emr_status'], mode_of_use=data['mode_of_use'],
                            ovc=data['ovc_offered'], otz=data['otz_offered'],
                            prep=data['prep_offered'], tb=data['tb_offered'],
                            # kp=data['kp_offered'],
                            mnch=data['mnch_offered'],
                            lab_manifest=None,
                            hiv=data['hiv_offered'], tpt=data['tpt_offered'],
                            covid_19=data['covid_19_offered'], evmmc=data['evmmc_offered'],
                            for_version="edited",
                            facility_edits=Edited_Facility_Info.objects.get(pk=unique_id_for_edit))
    else:
        emr_info = EMR_Info(type=None, status=None, mode_of_use=None, ovc=None, otz=None, prep=None,
                            tb=None, kp=None, mnch=None, lab_manifest=None,
                            hiv=None, tpt=None, covid_19=None, evmmc=None,
                            for_version="edited",
                            facility_edits=Edited_Facility_Info.objects.get(pk=unique_id_for_edit))

    # save IL info
    if data['IL'] == True:
        il_info = IL_Info(webADT_registration=data['webADT_registration'],
                          webADT_pharmacy=data['webADT_pharmacy'],
                          status=None, three_PM=data['il_three_PM'],
                          air=data['il_air'], Ushauri=data['il_ushauri'],
                          Mlab=data['il_mlab'],
                          lab_manifest=data['il_lab_manifest'], nimeconfirm=data['il_nimeconfirm'],
                          for_version="edited",
                          facility_edits=Edited_Facility_Info.objects.get(pk=unique_id_for_edit))
    else:
        il_info = IL_Info(webADT_registration=None, webADT_pharmacy=None, status=None, three_PM=None,
                          air=None, Ushauri=None, Mlab=None,
                          lab_manifest=None, nimeconfirm=None,
                          for_version="edited",
                          facility_edits=Edited_Facility_Info.objects.get(pk=unique_id_for_edit))

    # save MHealth info
    mhealth_info = MHealth_Info(Ushauri=data['mhealth_ushauri'], C4C=data['mhealth_c4c'],
                                Nishauri=data['mhealth_nishauri'],
                                ART_Directory=data['mhealth_art'],
                                Psurvey=data['mhealth_psurvey'], Mlab=data['mhealth_mlab'],
                                for_version="edited",
                                facility_edits=Edited_Facility_Info.objects.get(pk=unique_id_for_edit))

    try:
        # save to the DB
        facility.save()
        implementation_info.save()
        hts_info.save()
        emr_info.save()
        il_info.save()
        mhealth_info.save()

        return JsonResponse({'status_code': 200, 'redirect_url': 'home/'})
    except Exception as e:
        print(e)
        return JsonResponse({'status_code': 500, 'error':e})


def fetch_edited_data(request, facility_id):
    edited_data = []

    try:
        facility_info = Edited_Facility_Info.objects.prefetch_related('partner') \
                .select_related('owner').select_related('county')\
                .select_related('sub_county').get(facility_info=facility_id)

        # try:
        implementation_info = Implementation_type.objects.get(facility_edits=facility_info.id)
        emr_info = EMR_Info.objects.get(facility_edits=facility_info.id)
        hts_info = HTS_Info.objects.get(facility_edits=facility_info.id)
        il_info = IL_Info.objects.get(facility_edits=facility_info.id)
        mhealth_info = MHealth_Info.objects.get(facility_edits=facility_info.id)

        org_his_approver = Organization_HIS_approvers.objects.get(organization=facility_info.partner.id)

        ct = "CT" if implementation_info.ct else ""
        hts = "HTS" if implementation_info.hts else ""
        il = "IL" if implementation_info.il else ""

        implementation = [ct, hts, il]

        dataObj = {}
        dataObj["org_his_approver_email"] = org_his_approver.email if org_his_approver else None
        dataObj["id"] = facility_info.id
        dataObj["mfl_code"] = facility_info.mfl_code
        dataObj["name"] = facility_info.name
        dataObj["county"] = facility_info.county.id
        dataObj["sub_county"] = facility_info.sub_county.id
        dataObj["owner"] = facility_info.owner.id if facility_info.owner else ""
        dataObj["lat"] = facility_info.lat if facility_info.lat else ""
        dataObj["lon"] = facility_info.lon if facility_info.lon else ""
        dataObj["partner"] = facility_info.partner.id if facility_info.partner else ""
        dataObj["agency"] = facility_info.partner.agency.name if facility_info.partner and facility_info.partner.agency else ""
        dataObj["CT"]= implementation_info.ct
        dataObj["HTS"]= implementation_info.hts
        dataObj["IL"]= implementation_info.il
        dataObj["mHealth"] = implementation_info.mhealth
        dataObj["KP"] = implementation_info.KP
        dataObj["ovc_offered"]= emr_info.ovc
        dataObj["otz_offered"]= emr_info.otz
        dataObj["tb_offered"]= emr_info.tb
        dataObj["prep_offered"]= emr_info.prep
        dataObj["mnch_offered"]= emr_info.mnch
        dataObj["kp_offered"]= emr_info.kp
        dataObj["lab_man_offered"]= emr_info.lab_manifest
        dataObj["hiv_offered"] = emr_info.hiv
        dataObj["tpt_offered"] = emr_info.tpt
        dataObj["covid_19_offered"] = emr_info.covid_19
        dataObj["evmmc_offered"] = emr_info.evmmc
        dataObj["mhealth_ushauri"]= mhealth_info.Ushauri
        dataObj["mhealth_nishauri"]= mhealth_info.Nishauri
        dataObj["mhealth_c4c"]= mhealth_info.C4C
        dataObj["mhealth_mlab"]= mhealth_info.Mlab
        dataObj["mhealth_psurvey"]= mhealth_info.Psurvey
        dataObj["mhealth_art"]= mhealth_info.ART_Directory
        dataObj["il_status"]= il_info.status
        dataObj["webADT_registration"]= il_info.webADT_registration
        dataObj["webADT_pharmacy"]= il_info.webADT_pharmacy
        dataObj["il_three_PM"]= il_info.three_PM
        dataObj["il_air"] = il_info.air
        dataObj["il_ushauri"] = il_info.Ushauri
        dataObj["il_mlab"] = il_info.Mlab
        dataObj["il_lab_manifest"] = il_info.lab_manifest
        dataObj["il_nimeconfirm"] = il_info.nimeconfirm
        dataObj["emr_type"]= emr_info.type.id if emr_info.type else ""
        dataObj["emr_status"]= emr_info.status
        dataObj["mode_of_use"] = emr_info.mode_of_use
        dataObj["hts_use"]= hts_info.hts_use_name.id if hts_info.hts_use_name else ""
        dataObj["hts_deployment"]= hts_info.deployment.id if hts_info.deployment else ""
        dataObj["hts_status"]= hts_info.status

        dataObj["Edit_Exists"] =True
        edited_data.append(dataObj)
    except Edited_Facility_Info.DoesNotExist:
        edited_data = [{"Edit_Exists": False}]

    return JsonResponse(edited_data,safe=False)


@csrf_exempt
def approve_facility_changes(request, facility_id):
    data = json.loads(request.body)
    print(data)
    # edited_facilitydata = Edited_Facility_Info.objects.prefetch_related('partner') \
    #     .select_related('owner').select_related('county') \
    #     .select_related('sub_county').select_related('facility_info').get(facility_info=facility_id)

    # Save the new category to the database.
    try:
        print('------------------> approved')
        #facility_to_edit = edited_facilitydata.facility_info.id
        Facility_Info.objects.filter(pk=facility_id).update(mfl_code=int(data['mfl_code']),
                                                name=data['name'],
                                                county=Counties.objects.get(
                                                    pk=int(data['county'])),
                                                sub_county=Sub_counties.objects.get(
                                                    pk=int(data['sub_county'])),
                                                owner=Owner.objects.get(pk=int(data['owner'])),
                                                partner=Partners.objects.get(
                                                    pk=int(data['partner'])) if data['partner'] != "" else None,
                                                # facilitydata.agency = facilitydata.partner.agency.name
                                                lat=data['lat'] if data['lat'] else None,
                                                lon=data['lon'] if data['lon'] else None
                                                )

        # save Implementation info
        Implementation_type.objects.filter(facility_info=facility_id).update(ct=data['CT'],
                                                  hts=data['HTS'], il=data['IL'], mhealth=data['mHealth'],
                                                  KP = data["KP"], for_version="original")

        if data['HTS'] == True:
            # save HTS info
            HTS_Info.objects.filter(facility_info=facility_id).update(hts_use_name=HTS_use_type.objects.get(pk=int(data['hts_use'])),
                                status=data['hts_status'],
                                deployment=HTS_deployment_type.objects.get(
                                    pk=int(data['hts_deployment'])),
                                for_version="original")
        else:
            # save HTS info
            HTS_Info.objects.filter(facility_info=facility_id).update(hts_use_name=None, status=None, deployment=None,
                                for_version="original")

        # save EMR info
        if data['CT'] == True:
           EMR_Info.objects.filter(facility_info=facility_id).update(type=EMR_type.objects.get(pk=int(data['emr_type'])),
                                status=data['emr_status'], mode_of_use=data['mode_of_use'],
                                ovc=data['ovc_offered'], otz=data['otz_offered'],
                                prep=data['prep_offered'], tb=data['tb_offered'],
                                # kp=data['kp_offered'],
                                mnch=data['mnch_offered'],
                                lab_manifest=None,
                                 hiv=data['hiv_offered'], tpt=data['tpt_offered'],
                                 covid_19=data['covid_19_offered'], evmmc=data['evmmc_offered'],
                                for_version="original")
        else:
            EMR_Info.objects.filter(facility_info=facility_id).update(type=None, status=None, mode_of_use=None, ovc=None, otz=None, prep=None,
                                tb=None, kp=None, mnch=None, lab_manifest=None,
                                hiv=None, tpt=None, covid_19=None, evmmc=None,
                                for_version="original")

        # save IL info
        if data['IL'] == True:
            IL_Info.objects.filter(facility_info=facility_id).update(webADT_registration=data['webADT_registration'],
                              webADT_pharmacy=data['webADT_pharmacy'],
                              status=None, three_PM=data['il_three_PM'],
                              air=data['il_air'], Ushauri=data['il_ushauri'],
                              Mlab=data['il_mlab'],
                             lab_manifest=data['il_lab_manifest'],nimeconfirm=data['il_nimeconfirm'],
                              for_version="original")
        else:
            IL_Info.objects.filter(facility_info=facility_id).update(webADT_registration=None, webADT_pharmacy=None, status=None,
                              three_PM=None, air=None, Ushauri=None, Mlab=None,lab_manifest=None, nimeconfirm=None,
                              for_version="original")

        # save MHealth info
        MHealth_Info.objects.filter(facility_info=facility_id).update(Ushauri=data['mhealth_ushauri'], C4C=data['mhealth_c4c'],
                                    Nishauri=data['mhealth_nishauri'],
                                    ART_Directory=data['mhealth_art'],
                                    Psurvey=data['mhealth_psurvey'], Mlab=data['mhealth_mlab'],
                                    for_version="original")

        Edited_Facility_Info.objects.select_related('facility_info').get(facility_info=facility_id).delete()
        return JsonResponse({'status_code': 200, 'redirect_url': 'home/'})
    except Exception as e:
        print('------------------> error', e)
        return JsonResponse({'status_code': 500})


@csrf_exempt
def reject_facility_changes(request, facility_id):
    # data = json.loads(request.body)
    print('------------------> rejected')
    try:
        Edited_Facility_Info.objects.select_related('facility_info').get(facility_info=facility_id).delete()
        return JsonResponse({'status_code': 200, 'redirect_url': 'home/'})
    except Exception as e:
        print('------------------> rejected', e)
        return JsonResponse({'status_code': 500})


def view_facility_data(request, facility_id):

    facilitydata = Facility_Info.objects.prefetch_related('partner') \
        .select_related('owner').select_related('county') \
        .select_related('sub_county').get(pk=facility_id)

    implementation_info = Implementation_type.objects.get(facility_info=facility_id)
    emr_info = EMR_Info.objects.select_related('type').get(facility_info=facility_id)
    hts_info = HTS_Info.objects.get(facility_info=facility_id)
    il_info = IL_Info.objects.get(facility_info=facility_id)
    mhealth_info = MHealth_Info.objects.get(facility_info=facility_id)

    facility_data = {  # 1st Method
        'mfl_code': facilitydata.mfl_code,
        'name': facilitydata.name,
        'county': facilitydata.county.name,
        'sub_county': facilitydata.sub_county.name,
        'owner': facilitydata.owner.name if facilitydata.owner else "",
        'partner': facilitydata.partner.name if facilitydata.partner else "None",
        'agency': facilitydata.partner.agency.name if facilitydata.partner and facilitydata.partner.agency else "None",
        'lat': facilitydata.lat,
        'lon': facilitydata.lon,
        'CT': implementation_info.ct,
        'HTS': implementation_info.hts,
        'IL':  implementation_info.il,
        'mHealth': implementation_info.mhealth,
        "KP" : implementation_info.KP,
        'ovc_offered': emr_info.ovc,
        'otz_offered': emr_info.otz,
        'tb_offered': emr_info.tb,
        'prep_offered': emr_info.prep,
        'mnch_offered': emr_info.mnch,
        'kp_offered': emr_info.kp,
        'lab_man_offered': emr_info.lab_manifest,
        "hiv_offered" : emr_info.hiv,
        "tpt_offered" : emr_info.tpt,
        "covid_19_offered" : emr_info.covid_19,
        "evmmc_offered" : emr_info.evmmc,
        'mhealth_ushauri': mhealth_info.Ushauri,
        'mhealth_nishauri': mhealth_info.Nishauri,
        'mhealth_c4c': mhealth_info.C4C,
        'mhealth_mlab': mhealth_info.Mlab,
        'mhealth_psurvey': mhealth_info.Psurvey,
        'mhealth_art': mhealth_info.ART_Directory,
        'il_status': il_info.status,
        'webADT_registration': il_info.webADT_registration,
        'webADT_pharmacy': il_info.webADT_pharmacy,
        'il_three_PM': il_info.three_PM,
        'il_air': il_info.air,
        'il_ushauri': il_info.Ushauri,
        'il_mlab': il_info.Mlab,
        'il_lab_manifest': il_info.lab_manifest,
        'il_nimeconfirm': il_info.nimeconfirm,
        'emr_type': emr_info.type.type if emr_info.type else "",
        'emr_status': emr_info.status,
        'mode_of_use': emr_info.mode_of_use,
        'hts_use': hts_info.hts_use_name.hts_use_name if hts_info.hts_use_name else "",
        'hts_deployment': hts_info.deployment.deployment if hts_info.deployment else "",
        'hts_status': hts_info.status,
    }

    return JsonResponse(facility_data,safe=False)


def partners(request):

    partners_query = Partners.objects.prefetch_related('agency').all()

    partners_data = []
    for part in partners_query:
        partObj = {}

        partObj['id'] = part.id
        partObj['name'] = part.name
        partObj['agency'] = part.agency.name if part.agency else ""
        partObj['agency_id'] = part.agency.id if part.agency else ""

        partners_data.append(partObj)

    return JsonResponse(partners_data,safe=False)


@csrf_exempt
def edit_partner(request, partner_id):

    partner_query = Partners.objects.prefetch_related('agency').get(pk=partner_id)
    org_steward = Organization_stewards.objects.select_related('organization').get(organization__id=partner_id)
    partObj = {}

    partObj['id'] = partner_query.id
    partObj['partner'] = partner_query.name
    partObj['org_steward_email'] = (org_steward.email).strip()
    partObj['agency'] = partner_query.agency.name if partner_query.agency else ""
    partObj['agency_id'] = partner_query.agency.id if partner_query.agency else ""

    if request.method == 'POST':
        data = json.loads(request.body)
        print(data)
        try:
            Partners.objects.filter(pk=int(data['id'])) \
                .update(name=data['partner'],
                        agency=SDP_agencies.objects.get(pk=int(data['agency_id'])))
            return JsonResponse({'status_code':200, 'redirect_url':'partners/'},safe=False)
        except Exception as e:
            print(e)
            return JsonResponse({'status_code':500},safe=False)

    return JsonResponse(partObj,safe=False)


@csrf_exempt
def data_for_excel(request):
    data = json.loads(request.body)

    if data['OrganizationId']:
        organization = Organizations.objects.select_related('org_access_right').get(
            organization_id=data['OrganizationId'])

        if organization.org_access_right:
            facilities_info = Facility_Info.objects.select_related('partner') \
                .select_related('county') \
                .select_related('sub_county').filter(partner__id=organization.org_access_right.id)
        else:
            facilities_info = Facility_Info.objects.prefetch_related('partner') \
                .select_related('county') \
                .select_related('sub_county').all()
    else:
        facilities_info = Facility_Info.objects.prefetch_related('partner') \
            .select_related('county') \
            .select_related('sub_county').all()

    #append data to a list
    facilitiesdata = []

    for row in facilities_info:
        implementation_info = Implementation_type.objects.get(facility_info=row.id)
        emr_info = EMR_Info.objects.get(facility_info=row.id)
        hts_info = HTS_Info.objects.get(facility_info=row.id)
        il_info = IL_Info.objects.get(facility_info=row.id)
        mhealth_info = MHealth_Info.objects.get(facility_info=row.id)

        ct = "CT " if implementation_info.ct else ""
        hts = "HTS " if implementation_info.hts else ""
        il = "IL " if implementation_info.il else ""
        mhealth = "MHealth " if implementation_info.mhealth else ""
        KP = "KP " if implementation_info.KP else ""

        implementation = ct + hts + il + mhealth + KP

        try:
            dataObj = {}
            dataObj["mfl_code"] = row.mfl_code
            dataObj["name"] = row.name
            dataObj["county"] = row.county.name
            dataObj["sub_county"] = row.sub_county.name
            dataObj["owner"] = row.owner.name if row.owner else ""
            dataObj["lat"] = row.lat if row.lat else ""
            dataObj["lon"] = row.lon if row.lon else ""
            dataObj["partner"] = row.partner.name if row.partner else ""
            dataObj["agency"] = row.partner.agency.name if row.partner and row.partner.agency else ""
            dataObj["implementation"] = implementation
            dataObj["emr_type"] = emr_info.type.type if emr_info.type else ""
            dataObj["emr_status"] = emr_info.status if emr_info.status else ""
            dataObj["mode_of_use"] = emr_info.mode_of_use if emr_info.mode_of_use else ""
            dataObj["hts_use"] = hts_info.hts_use_name.hts_use_name if hts_info.hts_use_name else ""
            dataObj["hts_deployment"] = hts_info.deployment.deployment if hts_info.deployment else ""
            dataObj["hts_status"] = hts_info.status
            dataObj["il_status"] = il_info.status
            dataObj["il_registration_ie"] = il_info.webADT_registration
            dataObj["il_pharmacy_ie"] = il_info.webADT_pharmacy
            dataObj["ovc_offered"] = emr_info.ovc
            dataObj["otz_offered"] = emr_info.otz
            dataObj["tb_offered"] = emr_info.tb
            dataObj["prep_offered"] = emr_info.prep
            dataObj["mnch_offered"] = emr_info.mnch
            dataObj["kp_offered"] = emr_info.kp
            dataObj["lab_man_offered"] = emr_info.lab_manifest
            dataObj["hiv_offered"] = emr_info.hiv
            dataObj["tpt_offered"] = emr_info.tpt
            dataObj["covid_19_offered"] = emr_info.covid_19
            dataObj["evmmc_offered"] = emr_info.evmmc
            dataObj["mhealth_ushauri"] = mhealth_info.Ushauri
            dataObj["mhealth_nishauri"] = mhealth_info.Nishauri
            dataObj["mhealth_c4c"] = mhealth_info.C4C
            dataObj["mhealth_mlab"] = mhealth_info.Mlab
            dataObj["mhealth_psurvey"] = mhealth_info.Psurvey
            dataObj["mhealth_art"] = mhealth_info.ART_Directory
            dataObj["il_status"] = il_info.status
            dataObj["webADT_registration"] = il_info.webADT_registration
            dataObj["webADT_pharmacy"] = il_info.webADT_pharmacy
            dataObj["il_three_PM"] = il_info.three_PM
            dataObj["il_air"] = il_info.air
            dataObj["il_ushauri"] = il_info.Ushauri
            dataObj["il_mlab"] = il_info.Mlab
            dataObj["il_lab_manifest"] = il_info.lab_manifest
            dataObj["il_nimeconfirm"] = il_info.nimeconfirm
            dataObj["emr_type"] = emr_info.type.type if emr_info.type else ""
            dataObj["emr_status"] = emr_info.status
            dataObj["mode_of_use"] = emr_info.mode_of_use
            dataObj["hts_use"] = hts_info.hts_use_name.hts_use_name if hts_info.hts_use_name else ""
            dataObj["hts_deployment"] = hts_info.deployment.deployment if hts_info.deployment else ""
            dataObj["hts_status"] = hts_info.status

            facilitiesdata.append(dataObj)
        except Exception as e:
            print('error ----->', e)

    return JsonResponse(facilitiesdata, safe=False)
 # ======================= API =====================
#


def sub_counties(request):
    #sub_counties = Sub_counties.objects.filter(county=county_id)
    #data = serialize("json", sub_counties)
    #return HttpResponse(data, content_type="application/json")
    counties = Counties.objects.all().order_by('name')

    sub_counties_list =[]
    for row in counties:
        sub_counties = Sub_counties.objects.filter(county=row.id).order_by('name')

        subObj = {}
        subObj['county'] = row.id
        subObj['county_name'] = row.name
        subObj['sub_county'] = [{'id': sub.id, 'name': sub.name} for sub in sub_counties]

        sub_counties_list.append(subObj)

    return JsonResponse(sub_counties_list, safe=False)


def get_partners_list(request):
    partners = Partners.objects.select_related('agency').all()

    partners_list =[]
    for row in partners:

        partnerObj = {}
        partnerObj['partner'] = row.id
        partnerObj['agency'] = {'id': row.agency.id, 'name': row.agency.name}

        partners_list.append(partnerObj)

    return JsonResponse(partners_list, safe=False)


