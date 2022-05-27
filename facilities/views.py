from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.core.mail import BadHeaderError, send_mail, EmailMessage
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context
from django.db import connection
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
    msg = EmailMessage(subject="Facility test email", body=msg_html, from_email=settings.DEFAULT_FROM_EMAIL,
                       bcc=['mary.kilewe@thepalladiumgroup.com'])
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
    mfl_code = data['mfl_code']
    partner = data['partner']
    print(data)
    # print("request.GET['facility_id']", request.GET['facility_id'], request.GET['username'], request.GET['frontend_url'])

    # facility = Facility_Info.objects.get(pk=facility_id)

    context = {
        'news': 'We have good news!',
        'url': frontend_url + '/facilities/approve_changes/',
        'mfl_code': mfl_code,  # facilitydata.mfl_code,
        'facility_id': facility_id,  # facilitydata.id
        'username': username
    }
    his_approver = Organization_HIS_approvers.objects.get(organization=partner)
    print('-----------> sending mail ...', his_approver.email)
    msg_html = render_to_string('facilities/email_template.html', context)
    msg = EmailMessage(subject="Facility Modified", body=msg_html, from_email=settings.DEFAULT_FROM_EMAIL,
                       bcc=['marykilewe@gmail.com', his_approver.email])  # , organization.email
    msg.content_subtype = "html"  # Main content is now text/html
    msg.send()
    print('-----------> sending mail ...', his_approver.email)
    return 0

@csrf_exempt
def new_facility_send_email(request):
    # print("see whats sent ---->", request.body)
    data = json.loads(request.body)

    facility_id = data['facility_id']
    username = data['username']
    frontend_url = data['frontend_url']
    mfl_code = data['mfl_code']
    partner = data['partner']

    # facility = Facility_Info.objects.get(pk=facility_id)

    context = {
        'news': 'We have good news!',
        'url': frontend_url + '/facilities/approve_changes/',
        'mfl_code': mfl_code,  # facilitydata.mfl_code,
        'facility_id': facility_id,  # facilitydata.id
        'username': username
    }
    his_approver = Organization_HIS_approvers.objects.get(organization=partner)
    print('-----------> sending mail ...', his_approver.email)
    msg_html = render_to_string('facilities/new_facility_email_template.html', context)
    msg = EmailMessage(subject="New Facility Added!", body=msg_html, from_email=settings.DEFAULT_FROM_EMAIL,
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
        mfl_code = data['mfl_code']
        user_edited_email = data["user_edited_email"]

        if choice == "approved":
            message_title = "Approved!"
            message = "Changes you made now reflect on the portal!"
            subject = "Facility Changes Approved!"
        else:
            message_title = "Rejected!"
            message = "Reasons provided for the rejection are : "
            subject = "Facility Changes Rejected!"

        # edits = Edited_Facility_Info.objects.get(facility_info=facility_id)
        # user = User.objects.get(pk=edits.user_edited)
        try:
            Facility_Info.objects.get(pk=facility_id)
            url = env("APP_FRONTEND_URL")
        except Facility_Info.DoesNotExist:
            url = env("APP_FRONTEND_URL") + '/facilities/update_facility/'+facility_id
        context = {
            'news': 'We have good news!',
            'url': url,
            'mfl_code': mfl_code,
            'facility_id': facility_id,
            "message_title": message_title,
            "reason_given": reason,
            "choice": choice,
            "message": message,
        }
        msg_html = render_to_string('facilities/customizable_email.html', context)
        msg = EmailMessage(subject=subject, body=msg_html, from_email=settings.DEFAULT_FROM_EMAIL,
                           bcc=[user_edited_email])
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
    # print("what was sent back ----------->", data, data['OrganizationId'])

    with connection.cursor() as cursor:
        cursor.execute('SELECT facilities_facility_info.id, facilities_facility_info.mfl_code, '
                       'facilities_facility_info.name, facilities_counties.name, facilities_sub_counties.name,'
                       'facilities_facility_info.partner_id, facilities_owner.name,  '
                       'facilities_facility_info.lat, facilities_facility_info.lon, '
                       'facilities_implementation_type.ct, facilities_implementation_type.hts, facilities_implementation_type.il, '
                       'facilities_implementation_type.mHealth, facilities_implementation_type.kp '
                       'FROM facilities_facility_info '
                       'JOIN facilities_owner '
                       'ON facilities_owner.id = facilities_facility_info.owner_id '                      
                       'JOIN facilities_counties '
                       'ON facilities_counties.id = facilities_facility_info.county_id '
                       'JOIN facilities_sub_counties '
                       'ON facilities_sub_counties.id = facilities_facility_info.sub_county_id '
                       'JOIN facilities_implementation_type '
                       'ON facilities_implementation_type.facility_info_id = facilities_facility_info.id '
                       'where approved = True;')
        default_all_facilities_data = cursor.fetchall()

    if data['OrganizationId'] != None:
        organization = Organizations.objects.select_related('org_access_right').get(
            organization_id=data['OrganizationId'])

        if organization.org_access_right:
            # if an organization id is sent back, filter according to that org id
            with connection.cursor() as cursor:
                cursor.execute('SELECT facilities_facility_info.id, facilities_facility_info.mfl_code, '
                               'facilities_facility_info.name, facilities_counties.name, facilities_sub_counties.name,'
                               'facilities_facility_info.partner_id, facilities_owner.name,  '
                               'facilities_facility_info.lat, facilities_facility_info.lon, '
                               'facilities_implementation_type.ct, facilities_implementation_type.hts, facilities_implementation_type.il, '
                               'facilities_implementation_type.mHealth, facilities_implementation_type.kp '
                               'FROM facilities_facility_info '
                               'JOIN facilities_owner '
                               'ON facilities_owner.id = facilities_facility_info.owner_id '                      
                               'JOIN facilities_counties '
                               'ON facilities_counties.id = facilities_facility_info.county_id '
                               'JOIN facilities_sub_counties '
                               'ON facilities_sub_counties.id = facilities_facility_info.sub_county_id '
                               'JOIN facilities_implementation_type '
                               'ON facilities_implementation_type.facility_info_id = facilities_facility_info.id '
                               'where facilities_facility_info.partner_id = '+ str(organization.org_access_right.id) +' and facilities_facility_info.approved = True;')
                facilities_info = cursor.fetchall()
        else:
            facilities_info = default_all_facilities_data
    else:
        facilities_info = default_all_facilities_data

    for row in facilities_info:
        # check if partner id in Facility table has a value
        if row[5] != None:
            with connection.cursor() as cursor:
                cursor.execute('SELECT facilities_partners.name, facilities_sdp_agencies.name '
                               'FROM facilities_partners '
                               'JOIN facilities_sdp_agencies '
                               'ON facilities_sdp_agencies.id = facilities_partners.agency_id '
                               'where facilities_partners.id = '+ str(row[5]) +';')
                partner_data = cursor.fetchone()
                sdp = partner_data[0]
                agency = partner_data[1]
        else:
            sdp = ""
            agency = ""

        dataObj = {}
        dataObj["id"] = uuid.UUID(row[0])
        dataObj["mfl_code"] = row[1]
        dataObj["name"] = row[2]
        dataObj["county"] = row[3]
        dataObj["sub_county"] = row[4]
        dataObj["owner"] = row[6] if row[6] else ""
        dataObj["partner"] = sdp
        dataObj["agency"] = agency

        facilitiesdata.append(dataObj)

    return JsonResponse(facilitiesdata,safe=False)


def delete_facility(request, facility_id):

    Facility_Info.objects.get(pk=facility_id).delete()

    return HttpResponseRedirect('/home')


@csrf_exempt
def org_stewards_and_HISapprovers(request):
    data = json.loads(request.body)

    allowed_users = []
    print("Organization_HIS_approvers ---->",data["orgId"])

    organization = Organizations.objects.get(organization_id=data["orgId"])
    print("organization ---->", organization.name)
    if organization.org_access_right != None:
        steward_email = Organization_stewards.objects.get(organization=organization.org_access_right)
        allowed_users.append(steward_email.email.lower() if steward_email else None)

        approver_email = Organization_HIS_approvers.objects.get(organization=organization.org_access_right)
        allowed_users.append(approver_email.email.lower() if approver_email else None)
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

    facilityObj = {}

    if request.method == 'POST':

        try:
            Facility_Info.objects.get(mfl_code=int(data['code']), approved=True)
            facilityObj = {"status": 'data exists'}
        except Facility_Info.DoesNotExist:
            try:
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
                print(request.POST.get('code'), "doesnt exist")

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
    dataObj["date_of_emr_impl"] = emr_info.date_of_emr_impl
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
    unique_facility_id = data['id'] #uuid.uuid4()

    try:
        Facility_Info.objects.get(mfl_code=int(data['mfl_code']), approved=True)
        return JsonResponse({'status_code': 500, 'error': "Facility with "+str(data['mfl_code'])+" already exists in HIS Master List. Please enter another MFL Code"})
    except Facility_Info.DoesNotExist:

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
                                status=data['emr_status'], mode_of_use=data['mode_of_use'], date_of_emr_impl=data['date_of_emr_impl'],
                                ovc=data['ovc_offered'], otz=data['otz_offered'],
                                prep=data['prep_offered'], tb=data['tb_offered'],
                                kp=data['kp_offered'], mnch=data['mnch_offered'],
                                lab_manifest=None,
                                hiv=data['hiv_offered'], tpt=data['tpt_offered'],
                                covid_19=data['covid_19_offered'], evmmc=data['evmmc_offered'],
                                for_version="original",
                                facility_info=Facility_Info.objects.get(pk=unique_facility_id))
        else:
            emr_info = EMR_Info(type=None, status=None, mode_of_use=None, date_of_emr_impl=None,
                                ovc=None, otz=None, prep=None,
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
            return JsonResponse({'status_code': 500, 'error':"Something went wrong. Please refresh and try again"})


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
    print('data ---> ',facility_id, data['id'],data['username'], data['email'])
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
                            status=data['emr_status'], mode_of_use=data['mode_of_use'],date_of_emr_impl=data['date_of_emr_impl'],
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
        emr_info = EMR_Info(type=None, status=None, mode_of_use=None, date_of_emr_impl=None,
                            ovc=None, otz=None, prep=None,
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
        dataObj["user_edited_email"] = facility_info.user_edited_email
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
        dataObj["date_of_emr_impl"] = emr_info.date_of_emr_impl
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
                                                lon=data['lon'] if data['lon'] else None,
                                                approved=True
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
                                status=data['emr_status'], mode_of_use=data['mode_of_use'], date_of_emr_impl=data['date_of_emr_impl'],
                                ovc=data['ovc_offered'], otz=data['otz_offered'],
                                prep=data['prep_offered'], tb=data['tb_offered'],
                                # kp=data['kp_offered'],
                                mnch=data['mnch_offered'],
                                lab_manifest=None,
                                 hiv=data['hiv_offered'], tpt=data['tpt_offered'],
                                 covid_19=data['covid_19_offered'], evmmc=data['evmmc_offered'],
                                for_version="original")
        else:
            EMR_Info.objects.filter(facility_info=facility_id).update(type=None, status=None, mode_of_use=None,
                                date_of_emr_impl=None, ovc=None, otz=None, prep=None,
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
        Facility_Info.objects.get(pk=facility_id, approved=False).delete()

        return JsonResponse({'status_code': 200, 'redirect_url': 'home/'})
    except Facility_Info.DoesNotExist:
        Edited_Facility_Info.objects.select_related('facility_info').get(facility_info=facility_id).delete()
        return JsonResponse({'status_code': 200, 'redirect_url': 'home/'})


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
        "date_of_emr_impl":emr_info.date_of_emr_impl,
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

    with connection.cursor() as cursor:
        cursor.execute('SELECT facilities_facility_info.id, facilities_facility_info.mfl_code, '
                       'facilities_facility_info.name, facilities_counties.name, facilities_sub_counties.name,'
                       'facilities_facility_info.partner_id, facilities_owner.name,  '
                       'facilities_facility_info.lat, facilities_facility_info.lon, '
                       'facilities_implementation_type.ct, facilities_implementation_type.hts, facilities_implementation_type.il, '
                       'facilities_implementation_type.mHealth, facilities_implementation_type.kp '
                       'FROM facilities_facility_info '
                       'JOIN facilities_owner '
                       'ON facilities_owner.id = facilities_facility_info.owner_id '                       
                       'JOIN facilities_counties '
                       'ON facilities_counties.id = facilities_facility_info.county_id '
                       'JOIN facilities_sub_counties '
                       'ON facilities_sub_counties.id = facilities_facility_info.sub_county_id '
                       'JOIN facilities_implementation_type '
                       'ON facilities_implementation_type.facility_info_id = facilities_facility_info.id '
                       'where approved = True;')
        default_all_facilities_data = cursor.fetchall()

    if data['OrganizationId'] != None:
        organization = Organizations.objects.select_related('org_access_right').get(
            organization_id=data['OrganizationId'])

        if organization.org_access_right:
            # if an organization id is sent back, filter according to that org id
            with connection.cursor() as cursor:
                cursor.execute('SELECT facilities_facility_info.id, facilities_facility_info.mfl_code, '
                               'facilities_facility_info.name, facilities_counties.name, facilities_sub_counties.name,'
                               'facilities_facility_info.partner_id, facilities_owner.name,  '
                               'facilities_facility_info.lat, facilities_facility_info.lon, '
                               'facilities_implementation_type.ct, facilities_implementation_type.hts, facilities_implementation_type.il, '
                               'facilities_implementation_type.mHealth, facilities_implementation_type.kp '
                               'FROM facilities_facility_info '
                               'JOIN facilities_owner '
                               'ON facilities_owner.id = facilities_facility_info.owner_id '                       
                               'JOIN facilities_counties '
                               'ON facilities_counties.id = facilities_facility_info.county_id '
                               'JOIN facilities_sub_counties '
                               'ON facilities_sub_counties.id = facilities_facility_info.sub_county_id '
                               'JOIN facilities_implementation_type '
                               'ON facilities_implementation_type.facility_info_id = facilities_facility_info.id '
                               'where facilities_facility_info.partner_id = ' + str(organization.org_access_right.id) +
                               ' and facilities_facility_info.approved = True;')
                facilities_info = cursor.fetchall()
        else:
            facilities_info = default_all_facilities_data
    else:
        facilities_info = default_all_facilities_data

    #append data to a list
    facilitiesdata = []

    for row in facilities_info:
        # check if partner id in Facility table has a value
        if row[5] != None:
            with connection.cursor() as cursor:
                cursor.execute('SELECT facilities_partners.name, facilities_sdp_agencies.name '
                               'FROM facilities_partners '
                               'JOIN facilities_sdp_agencies '
                               'ON facilities_sdp_agencies.id = facilities_partners.agency_id '
                               'where facilities_partners.id = ' + str(row[5]) + ';')
                partner_data = cursor.fetchone()
                sdp = partner_data[0]
                agency = partner_data[1]
        else:
            sdp = ""
            agency = ""

        emr_info = EMR_Info.objects.get(facility_info=row[0])
        hts_info = HTS_Info.objects.get(facility_info=row[0])
        with connection.cursor() as cursor:
            cursor.execute('SELECT facilities_il_info.status, facilities_il_info.webADT_pharmacy, '
                           'facilities_il_info.three_PM, facilities_il_info.air, facilities_il_info.Ushauri, '
                           'facilities_il_info.Mlab, facilities_il_info.lab_manifest, facilities_il_info.nimeconfirm '
                           'FROM facilities_il_info '
                           'where facilities_il_info.facility_info_id = %s;', [row[0]])
            il_info = cursor.fetchone()

        with connection.cursor() as cursor:
            cursor.execute('SELECT facilities_mhealth_info.Ushauri, facilities_mhealth_info.Nishauri, '
                           'facilities_mhealth_info.C4C, facilities_mhealth_info.Mlab, '
                           'facilities_mhealth_info.Psurvey, facilities_mhealth_info.ART_Directory '
                           'FROM facilities_mhealth_info '
                           'where facilities_mhealth_info.facility_info_id = %s;', [row[0]])
            mhealth_info = cursor.fetchone()

        # MHealth_Info.objects.raw('SELECT * FROM facilities_mhealth_info WHERE facility_info_id = %s', [row[0]])

        ct = "CT " if row[9] else ""
        hts = "HTS " if row[10] else ""
        il = "IL " if row[11] else ""
        mhealth = "MHealth " if row[12] else ""
        KP = "KP " if row[13] else ""

        implementation = ct + hts + il + mhealth + KP

        try:
            dataObj = {}
            dataObj["MFL Code"] = row[1]
            dataObj["Name"] = row[2]
            dataObj["County"] = row[3]
            dataObj["SubCounty"] = row[4]
            dataObj["Owner"] = row[6] if row[6] else ""
            dataObj["Partner"] = sdp
            dataObj["Agency"] = agency
            dataObj["Latitude"] = row[7] if row[7] else ""
            dataObj["Longitude"] = row[8] if row[8] else ""
            dataObj["Implementation"] = implementation

            dataObj["EMR Type"] = emr_info.type.type if emr_info.type else ""
            dataObj["EMR Status"] = emr_info.status if emr_info.status else ""
            dataObj["Mode Of Use"] = emr_info.mode_of_use if emr_info.mode_of_use else ""
            dataObj["Date of EMR Implementation"] = emr_info.date_of_emr_impl
            dataObj["HTS Use"] = hts_info.hts_use_name.hts_use_name if hts_info.hts_use_name else ""
            dataObj["HTS Deployment"] = hts_info.deployment.deployment if hts_info.deployment else ""
            dataObj["HTS Status"] = hts_info.status
            dataObj["IL Status"] = il_info[0] if il_info[0] != 'nan' else ''
            # dataObj["webADT_registration"] = il_info[1]
            dataObj["IL WebADT"] = check_true_or_false(il_info[1])
            dataObj["ovc_offered"] = check_true_or_false(emr_info.ovc)
            dataObj["otz_offered"] = check_true_or_false(emr_info.otz)
            dataObj["tb_offered"] = check_true_or_false(emr_info.tb)
            dataObj["prep_offered"] = check_true_or_false(emr_info.prep)
            dataObj["mnch_offered"] = check_true_or_false(emr_info.mnch)
            dataObj["kp_offered"] = check_true_or_false(emr_info.kp)
            dataObj["lab_man_offered"] = check_true_or_false(emr_info.lab_manifest)
            dataObj["hiv_offered"] = check_true_or_false(emr_info.hiv)
            dataObj["tpt_offered"] = check_true_or_false(emr_info.tpt)
            dataObj["covid_19_offered"] = check_true_or_false(emr_info.covid_19)
            dataObj["evmmc_offered"] = check_true_or_false(emr_info.evmmc)

            dataObj["MHealth Ushauri"] = check_true_or_false(mhealth_info[0])
            dataObj["MHealth Nishauri"] = check_true_or_false(mhealth_info[1])
            dataObj["MHealth C4C"] = check_true_or_false(mhealth_info[2])
            dataObj["MHealth Mlab"] = check_true_or_false(mhealth_info[3])
            dataObj["MHealth Psurvey"] = check_true_or_false(mhealth_info[4])
            dataObj["MHealth ART"] = check_true_or_false(mhealth_info[5])

            dataObj["IL 3PM"] = check_true_or_false(il_info[2])
            dataObj["IL Air"] = check_true_or_false(il_info[3])
            dataObj["IL Ushauri"] = check_true_or_false(il_info[4])
            dataObj["IL Mlab"] = check_true_or_false(il_info[5])
            dataObj["IL Lab_manifest"] = check_true_or_false(il_info[6])
            dataObj["IL Nimeconfirm"] = check_true_or_false(il_info[7])

            facilitiesdata.append(dataObj)
        except Exception as e:
            print('error ----->', e)

    return JsonResponse(facilitiesdata, safe=False)
 # ======================= API =====================
#

def check_true_or_false(value):
    if value == 1:
        result = "Yes"
    elif value == 0:
        result = "No"
    else:
        result = ""
    return result



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

