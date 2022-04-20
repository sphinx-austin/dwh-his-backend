from django.shortcuts import render, redirect

from django.http import HttpResponse, HttpResponseRedirect, JsonResponse

import random
from requests.structures import CaseInsensitiveDict
import requests
import json

# get environment variables
import environ
env = environ.Env()
environ.Env.read_env()




def signin(request):

    return JsonResponse({'status': 'signin'})


def signin_oidc(request):
    # allows frontend to consume access token and return to backen
    return render(request, 'users/signin_oidc.html')


def redirect_to_frontend(request):
    return JsonResponse({'status': 'success'})


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

    return HttpResponseRedirect('/')