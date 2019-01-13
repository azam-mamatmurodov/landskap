from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from apps.products import views as product_views

urlpatterns = [
    url(r'^products/$', login_required(product_views.ProductListView.as_view()), name='product_list'),
    url(r'^products/cat/(?P<cat_id>[\d]+)/$', login_required(product_views.ProductCatListView.as_view()),
        name='product_cat_list'),
    url(r'^products/create/$', login_required(product_views.ProductCreateView.as_view()), name='product_create'),
    url(r'^products/(?P<pk>[\d]+)/$',
        login_required(product_views.ProductDetailView.as_view()), name='product_detail'),
    url(r'^products/(?P<pk>[\d]+)/delete/$',
        login_required(product_views.ProductDeleteView.as_view()), name='product_delete'),
    url(r'^products/(?P<pk>[\d]+)/edit/$',
        login_required(product_views.ProductEditView.as_view()), name='product_edit'),
]
