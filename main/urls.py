from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.load, name='load'),
    url(r'^load/', views.load, name='load'),
    url(r'^alt_keys', views.keyword_upload, name='upload'),
    url(r'^sap/', views.sap_integration, name='sap'),
    url(r'^contents/', views.contents, name='contents'),
    # url(r'^tables/', views.table_load, name='table_load'),
    url(r'^report/', views.stored_searches, name='reports'),
    url(r'^stored_search/', views.stored_searches, name='stored_search'),
    url(r'^results', views.results, name='results'),
    url(r'^check_file_selected', views.check_file_selected, name='check_file_selected'),
    url(r'^edit_cmp_description', views.edit_cmp_description, name='edit_cmp_description'),
    url(r'^change_country', views.change_country, name='change_country'),
    url(r'^edit_member_firm_country', views.edit_member_firm_country, name='edit_member_firm_country'),
]
