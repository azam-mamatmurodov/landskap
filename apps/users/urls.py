from django.conf.urls import url
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required

from apps.users import views as user_views


urlpatterns = [
    url(r'^login/$', user_views.LoginView.as_view(), name='login_page'),
    url(r'^register/$', user_views.RegisterView.as_view(), name='register_page'),
    url(r'^logout/$', auth_views.logout,  {'next_page': '/'}, name='logout',),
    url(r'^settings/$', login_required(user_views.ProfileView.as_view()), name='settings'),

    url(r'^settings/password/$', login_required(user_views.ProfilePasswordView.as_view()),
        name='profile_password_page'),
    url(r'^notifications/$', login_required(user_views.NotificationsView.as_view()), name='company_notifications'),
    url(r'^notifications/(?P<pk>[\d]+)$', login_required(user_views.NotificationDetailView.as_view()),
        name='company_notifications_detail'),


    url(r'^news/$', login_required(user_views.NewsListView.as_view()), name='news_list'),
    url(r'^news/create/$', login_required(user_views.NewsCreateView.as_view()), name='news_create'),
    url(r'^news/(?P<pk>[\d]+)/$', login_required(user_views.NewsDetailView.as_view()), name='news_detail'),
    url(r'^news/(?P<pk>[\d]+)/delete/$', login_required(user_views.NewsDeleteView.as_view()), name='news_delete'),
    url(r'^news/(?P<pk>[\d]+)/edit/$', login_required(user_views.NewsEditView.as_view()), name='news_edit'),

    url(r'^password/reset/$', user_views.PasswordResetView.as_view(), name='password_reset', ),
    url(r'^password/done/$', user_views.PasswordResetDoneView.as_view(), name='password_reset_done', ),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        user_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),

    url(r'^reset/done/$', user_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    url(r'^cafe/$', login_required(user_views.CafeListView.as_view()), name='cafe_list'),
    url(r'^cafe/add/$', login_required(user_views.CafeAddView.as_view()), name='cafe_add'),
    url(r'^cafe/(?P<cafe_id>[\d]+)/$', login_required(user_views.CafeDetailView.as_view()), name='cafe_detail'),
    url(r'^cafe/(?P<cafe_id>[\d]+)/edit/$', login_required(user_views.CafeEditView.as_view()), name='cafe_edit'),
    url(r'^cafe/(?P<cafe_id>[\d]+)/delete/$', login_required(user_views.CafeDeleteView.as_view()), name='cafe_delete'),
    url(r'^cafe/(?P<cafe_id>[\d]+)/work-time/$', login_required(user_views.CafeWeekTimeView.as_view()),
        name='cafe_week_time_page'),
    url(r'^cafe/(?P<cafe_id>[\d]+)/location/$', login_required(user_views.CafeLocationView.as_view()),
        name='cafe_location_page'),
    url(r'^cafe/(?P<cafe_id>[\d]+)/gallery/$', login_required(user_views.GalleryView.as_view()), name='cafe_gallery'),
    url(r'^cafe/(?P<cafe_id>[\d]+)/gallery/add/$', login_required(user_views.GalleryAddView.as_view()),
        name='cafe_gallery_add'),
    url(r'^cafe/(?P<cafe_id>[\d]+)/gallery/(?P<file_id>[\d]+)/delete/$',
        login_required(user_views.GalleryDeleteView.as_view()), name='cafe_gallery_delete'),
    url(r'^cafe/(?P<cafe_id>[\d]+)/reviews/$', login_required(user_views.CafeReviewsView.as_view()),
        name='cafe_review_list'),

    url(r'^employees/$', login_required(user_views.EmployeesView.as_view()), name='employee_list'),
    url(r'^employees/(?P<employee_id>[\d]+)/$', login_required(user_views.EmployeeEditView.as_view()),
        name='employee_edit'),
    url(r'^employees/(?P<employee_id>[\d]+)/password/$', login_required(user_views.EmployeePasswordView.as_view()),
        name='employee_password'),
    url(r'^employees/(?P<employee_id>[\d]+)/delete/$', login_required(user_views.EmployeeDeleteView.as_view()),
        name='employee_delete'),
    url(r'^employees/add/$', login_required(user_views.EmployeeAddView.as_view()), name='employee_add'),
    url(r'^employees/add/existing/$', login_required(user_views.EmployeeAddExistingView.as_view()),
        name='employee_add_existing'),
    url(r'^transactions/$', user_views.TransactionsListView.as_view(), name='transactions_list'),
    url(r'^transactions/(?P<uuid>[0-9A-Za-z\-]+)/$', user_views.TransactionDetailView.as_view(),
        name='transaction_detail'),
]
