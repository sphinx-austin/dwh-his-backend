
from django.contrib import admin
from django.urls import include, path
from django.contrib.auth import views as auth_views
from . import views


urlpatterns = [
    path('', views.test, name='test'),
    path('signin/', views.signin, name='signin'),
    # path('connect/authorize/callback/', views.signup_callback, name='signup_callback'),
    path('signin-oidc', views.signin_oidc, name='signin_oidc'),
    path('logout_user/', views.logout_user, name='logout_user'),
    path('store_tokens', views.store_tokens, name='store_tokens'),
    path('log_user_in', views.log_user_in, name='log_user_in'),
]

