from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from django.conf import settings
from django.views.generic import RedirectView

from rest_framework.authtoken import views
from rest_framework_swagger.views import get_swagger_view

from apps.restapp.urls import urlpatterns as rest_urlpatterns

api_title = 'Landskap API documentation'
schema_view = get_swagger_view(title=api_title, patterns=rest_urlpatterns, url='/api/v1/')

urlpatterns = [
    url(r'^api-token-auth/', views.obtain_auth_token),
    url(r'^api/v1/', include('apps.restapp.urls', namespace='rest_api_urls')),
    url(r'^api/v1/', schema_view),
]

urlpatterns += [
    url('^$', RedirectView.as_view(url='/cafe/',)),
    url(r'^admin/', admin.site.urls),
    url(r'', include('apps.main.urls', namespace='main')),
    url(r'', include('apps.users.urls', namespace='users')),
    url(r'', include('apps.products.urls', namespace='products')),
    url(r'', include('apps.modifiers.urls', namespace='modifiers')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # import debug_toolbar
    # urlpatterns += [
    #     url(r'^__debug__/', include(debug_toolbar.urls)),
    # ]
