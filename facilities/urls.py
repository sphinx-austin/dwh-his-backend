from django.urls import path

from . import views

urlpatterns = [
    path(r'facilities/add_facility', views.add_facility_data, name='add_facility_data'),
    path(r'facilities/update_facility/<uuid:facility_id>', views.update_facility_data, name='update_facility_data'),
    path(r'facilities/check/facility_edits/<uuid:facility_id>', views.check_for_facility_edits, name='check_for_facility_edits'),
    path(r'facilities/fetch_edits/data/<uuid:facility_id>', views.fetch_edited_data, name='fetch_edited_data'),
    path(r'facilities/approve_changes/<uuid:facility_id>', views.approve_facility_changes, name='approve_facility_changes'),
    path(r'facilities/reject_changes/<uuid:facility_id>', views.reject_facility_changes, name='reject_facility_changes'),
    path(r'facilities/view_facility/data/<uuid:facility_id>', views.view_facility_data, name='view_facility_data'),
    path(r'facilities/partners', views.partners, name='partners'),
    path(r'facilities/edit_partner/<int:partner_id>', views.edit_partner, name='edit_partner'),
    path(r'facilities/sub_counties', views.sub_counties, name='sub_counties'),
    path(r'facilities/get_partners_list', views.get_partners_list, name='get_partners_list'),
    path(r'facilities/get_agencies_list', views.get_agencies_list, name='get_agencies_list'),
    path(r'facilities/data_for_excel', views.data_for_excel, name='data_for_excel'),
    path(r'update_kp_implementation', views.update_kp_implementation, name='update_kp_implementation'),
    path(r'send_email', views.send_email, name='send_email'),
    path(r'send_customized_email', views.send_customized_email, name='send_customized_email'),
    path(r'test_email', views.test_email, name='test_email'),

    path(r'fill_database', views.fill_database, name='fill_database'),
    path(r'facilities', views.facilities, name='facilities'),
    path(r'facilities/emr_types', views.emr_types, name='emr_types'),
    path(r'facilities/org_stewards_and_HISapprovers', views.org_stewards_and_HISapprovers, name='org_stewards_and_HISapprovers'),
    path(r'facilities/hts_deployment_types', views.hts_deployment_types, name='hts_deployment_types'),
    path(r'facilities/hts_uses', views.hts_uses, name='hts_uses'),
    path(r'facilities/owners', views.owners, name='owners'),
    path(r'facilities/agencies', views.agencies, name='agencies'),
    path(r'facilities/partners_list', views.partners_list, name='partners_list'),
    path(r'facilities/fetch_facility_data/<uuid:facility_id>', views.fetch_facility_data, name='fetch_facility_data'),
    path(r'facilities/get_mfl_data', views.get_mfl_data, name='get_mfl_data'),
]