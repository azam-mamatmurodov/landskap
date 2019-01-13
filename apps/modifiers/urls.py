from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from apps.modifiers import views as modifier_views

urlpatterns = [
    url(r'^modifiers/$', login_required(modifier_views.ModifierCatListView.as_view()), name='modifier_list'),
    url(r'^modifiers/cat/(?P<cat_id>[\d]+)/$', login_required(modifier_views.ModifierCatListView.as_view()),
        name='modifier_cat_list'),
    url(r'^modifiers/create/$', login_required(modifier_views.ModifierCatCreateView.as_view()),
        name='modifier_cat_create'),
    url(r'^modifiers/(?P<pk>[\d]+)/$',
        login_required(modifier_views.ModifierCatDetailView.as_view()), name='modifier_cat_detail'),
    url(r'^modifiers/(?P<pk>[\d]+)/delete/$',
        login_required(modifier_views.ModifierCatDeleteView.as_view()), name='modifier_cat_delete'),
    url(r'^modifiers/(?P<pk>[\d]+)/edit/$',
        login_required(modifier_views.ModifierCatEditView.as_view()), name='modifier_cat_edit'),

    url(r'^modifiers/modifier/create/$', login_required(modifier_views.ModifierCreateView.as_view()),
        name='modifier_create'),
    url(r'^modifiers/modifier/(?P<pk>[\d]+)/$',
        login_required(modifier_views.ModifierDetailView.as_view()), name='modifier_detail'),
    url(r'^modifiers/modifier/(?P<pk>[\d]+)/delete/$',
        login_required(modifier_views.ModifierDeleteView.as_view()), name='modifier_delete'),
    url(r'^modifiers/modifier/(?P<pk>[\d]+)/edit/$',
        login_required(modifier_views.ModifierEditView.as_view()), name='modifier_edit'),

]
