from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.db import connection
from .forms.users.forms import *
from django.contrib import messages
import random
# get environment variables
import environ
env = environ.Env()
environ.Env.read_env()


from facilities.models import *


def redirect_to_frontend(request):
    return JsonResponse({'status': 'success', 'endpoints':'UP', 'v':2.000, 'date':'28/02/2023'})


def view_unapproved(request):
    facilities_info = Facility_Info.objects.prefetch_related('partner') \
        .select_related('county').select_related('partner').select_related('owner') \
        .select_related('sub_county').filter(approved=False)

    facilitiesdata = []
    for row in facilities_info:

        dataObj = {}
        dataObj["id"] = row.id
        dataObj["mfl_code"] = row.mfl_code
        dataObj["name"] = row.name
        dataObj["county"] = row.county
        dataObj["sub_county"] = row.sub_county
        dataObj["owner"] = row.owner.name
        dataObj["lat"] = row.lat
        dataObj["lon"] = row.lon
        dataObj["partner"] = row.partner.name if row.partner else ""
        dataObj["agency"] = row.partner.agency.name if row.partner and row.partner.agency else ""

        facilitiesdata.append(dataObj)
    return render(request, 'admin_manager/view_unapproved.html', {'facilitiesdata': facilitiesdata})

def view_edits(request):
    facilities_info = Edited_Facility_Info.objects.prefetch_related('partner') \
        .select_related('county').select_related('partner').select_related('owner') \
        .select_related('sub_county')

    editsdata = []
    for row in facilities_info:

        dataObj = {}
        dataObj["id"] = row.id
        dataObj["mfl_code"] = row.mfl_code
        dataObj["name"] = row.name
        dataObj["county"] = row.county
        dataObj["sub_county"] = row.sub_county
        dataObj["owner"] = row.owner.name
        dataObj["lat"] = row.lat
        dataObj["lon"] = row.lon
        dataObj["partner"] = row.partner.name if row.partner else ""
        dataObj["agency"] = row.partner.agency.name if row.partner and row.partner.agency else ""

        editsdata.append(dataObj)
    return render(request, 'admin_manager/view_edits.html', {'editsdata': editsdata})


def view_duplicates(request):
    with connection.cursor() as cursor:
        cursor.execute('SELECT mfl_code, approved, COUNT(mfl_code) '
                        'FROM facilities_facility_info '
                        'GROUP BY mfl_code, approved '
                        'HAVING COUNT(mfl_code) > 1 and approved=true')
        existingduplicates = cursor.fetchall()

    duplicatesdata = []
    if len(existingduplicates) > 0:

        for dup in existingduplicates:
            facilities_info = Facility_Info.objects.prefetch_related('partner') \
                .select_related('county').select_related('partner').select_related('owner') \
                .select_related('sub_county').filter(mfl_code=dup[0])
            for row in facilities_info:
                dataObj = {}
                dataObj["id"] = row.id
                dataObj["mfl_code"] = row.mfl_code
                dataObj["name"] = row.name
                dataObj["county"] = row.county
                dataObj["sub_county"] = row.sub_county
                dataObj["owner"] = row.owner.name
                dataObj["lat"] = row.lat
                dataObj["lon"] = row.lon
                dataObj["partner"] = row.partner.name if row.partner else ""
                dataObj["agency"] = row.partner.agency.name if row.partner and row.partner.agency else ""

                duplicatesdata.append(dataObj)
    return render(request, 'admin_manager/view_duplicates.html', {'duplicatesdata': duplicatesdata})




def delete_facility(request, facility_id):

    # get rid of the edits
    try:
        Facility_Info.objects.get(pk=facility_id, approved=False).delete()
    except Facility_Info.DoesNotExist:
        print('Facility doesnt exist')

    # messages.add_message(request, messages.SUCCESS, "Facility successfully deleted!")
    return HttpResponse('success')

def delete_duplicate(request, facility_id):

    # get rid of the edits
    try:
        Facility_Info.objects.get(pk=facility_id, approved=True).delete()
    except Facility_Info.DoesNotExist:
        print('Facility doesnt exist')

    # messages.add_message(request, messages.SUCCESS, "Facility successfully deleted!")
    return HttpResponse('success')

def delete_edit(request, facility_id):

    # get rid of the edits
    try:
        Edited_Facility_Info.objects.get(pk=facility_id).delete()
    except Edited_Facility_Info.DoesNotExist:
        print('Facility Edits doesnt exist')

    # messages.add_message(request, messages.SUCCESS, "Facility successfully deleted!")
    return HttpResponse('success')


def signin(request):
    return JsonResponse({'status': 'signin'})


def signin_oidc(request):
    # allows frontend to consume access token and return to backen
    return render(request, 'admin_manager/signin_oidc.html')





from django.views.decorators.csrf import csrf_exempt,csrf_protect
@csrf_exempt
def store_tokens(request):

    return JsonResponse({'status': 'success'})

def log_user_in(request):

    return HttpResponseRedirect('/')



def generate_nonce(length=32):
    """Generate pseudorandom number."""
    return ''.join([str(random.randint(0, 9)) for i in range(length)])


def logout_user(request):
    logout(request)
    return HttpResponseRedirect('/')