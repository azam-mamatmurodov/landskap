# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import re

from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import ugettext_lazy as _
from django.conf.urls import url
from django.shortcuts import render, redirect


from mptt.admin import DraggableMPTTAdmin
# from djcelery.models import (
#     TaskState, WorkerState, PeriodicTask,
#     IntervalSchedule, CrontabSchedule
# )
from rest_framework.authtoken import models as rest_auth_models

from apps.users import models as user_models
from .forms import CategoryForm, NotificationsAdminForm


class WeekTimeInline(admin.TabularInline):
    model = user_models.WeekTime
    max_num = min_num = 7

    verbose_name = _('Company weekly work time')
    verbose_name_plural = _('Company weekly work time ')


@admin.register(user_models.User)
class UserAdmin(DjangoUserAdmin, admin.ModelAdmin):
    readonly_fields = ('referral_code', )
    fieldsets = (
        (_('Main'), {'fields': ('phone', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'user_type', 'phone', 'avatar', 'gender',
                                         'date_of_birthday', 'email', 'referral_code', )}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'phone', 'first_name', 'last_name', 'user_type',),
        }),
    )
    list_display = ('get_fullname', 'is_staff', 'user_type', 'date_joined', 'referral_code')
    list_filter = ('user_type',)
    search_fields = ('email', 'first_name', 'last_name', 'phone',)
    ordering = ('email',)

    @staticmethod
    def get_fullname(obj):
        return "{} {}".format(obj.first_name, obj.last_name)


class FileAdmin(admin.StackedInline):
    fields = ['file', ]
    model = user_models.File
    extra = 5


class AlbumAdmin(admin.ModelAdmin):
    inlines = [FileAdmin, ]
    fieldsets = (
        ('Author details', {'fields': ('owner', 'cafe',), }),
    )
    list_display = ('id', 'owner', 'created_at', 'updated_at', 'cafe', )
    list_filter = ['cafe']

    class Meta:
        model = user_models.Album


class ReviewAdmin(admin.ModelAdmin):
    list_display = ['get_author', 'cafe', 'created_at', ]

    @staticmethod
    def get_author(obj):
        return obj.author.first_name


class ReviewLikeDislikeAdmin(admin.ModelAdmin):
    list_display = ['like_dislike_user', 'review', 'rate', ]


class NotificationsAdmin(admin.ModelAdmin):
    empty_value_display = '-empty-'
    list_display = ['title', 'get_receiver', 'get_sender']
    
    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
    
    def get_receiver(self, obj):
        return obj.user.get_full_name()

    get_receiver.short_description = 'Receiver'

    def get_sender(self, obj):
        if obj.notification_sender:
            return obj.notification_sender.get_full_name()
        return None

    get_sender.short_description = 'Sender'

    change_list_template = 'admin/notifications/change_list.html'

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            url('send/', self.send_notifications),
        ]
        return my_urls + urls
    
    def send_notifications(self, request):

        if request.method == 'POST':
            form = NotificationsAdminForm(request.POST)
            if form.is_valid():
                # Creation notifications for business or clients
                count = int(form.data.get('count'))
                text = form.data.get('text')
                user_type = form.data.get('user_type')

                users = user_models.User.objects.filter(user_type=user_type)

                if count <= users.count():
                    receivers = users[:count]
                else:
                    receivers = users
                if int(user_type) == user_models.User.OWNER:
                    for receiver in receivers:
                        user_models.Notifications.objects.create(**{
                            'title': 'Notifications from Administrator',
                            'user': receiver,
                            'notification_sender': request.user,
                            'text': text
                        })
                else:
                    pattern = re.compile(r"^[^.]*")
                    message = re.search(pattern, text).group(0)

                self.message_user(request, "Notifications have been sent to {} users!".format(receivers.count()))
                return redirect('/admin/users/notifications/')
            context = {'form': form}
            return render(request, 'admin/notifications/notifications_send.html', context)
        form = NotificationsAdminForm()
        context = {'form': form}
        return render(request, 'admin/notifications/notifications_send.html', context)


class FileAdminPanel(admin.ModelAdmin):
    list_display = ['get_cafe']
    list_filter = ['album']

    @staticmethod
    def get_cafe(obj):
        return obj.album.cafe


class CashierInline(admin.TabularInline):
    model = user_models.Cashier
    fields = ['cafe', 'cashier']


class CafeAdmin(admin.ModelAdmin):
    inlines = [WeekTimeInline, CashierInline, ]
    ordering = ['-id']
    list_display = ['id', 'cafe_name', 'status', ]
    list_filter = ['status', 'category', ]
    list_editable = ['status']

    class Meta:
        verbose_name = 'Cafe'
        verbose_name_plural = 'Cafes'


class CategoryAdmin(admin.ModelAdmin):
    form = CategoryForm
    
    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'


class UserAvatarsAdmin(admin.ModelAdmin):

    class Meta:
        verbose_name = 'Users avatar'
        verbose_name_plural = 'Users avatar'


class NewsAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_at', ]


class PointAdmin(admin.ModelAdmin):
    list_display = ['owner', 'point_count', 'get_root_cafe', ]

    @staticmethod
    def get_root_cafe(obj):
        if obj.root_cafe:
            return obj.root_cafe.owner
        return None


class FreeItemAdmin(admin.ModelAdmin):
    list_display = ['owner', 'point_count', 'root_cafe',  'product', 'get_root_cafe', 'expire_time', 'status']
    list_filter = ['root_cafe', 'status', ]
    list_per_page = 50

    @staticmethod
    def get_root_cafe(obj):
        if obj.root_cafe:
            return obj.root_cafe.owner
        return None


class CafeGeneralSettingsAdmin(admin.ModelAdmin):
    list_display = ['cafe_name', 'owner']


# admin.site.unregister(TaskState)
# admin.site.unregister(WorkerState)
# admin.site.unregister(IntervalSchedule)
# admin.site.unregister(CrontabSchedule)
# admin.site.unregister(PeriodicTask)
# admin.site.unregister(Group)
# admin.site.register(rest_auth_models.Token)


admin.site.register(user_models.Category, DraggableMPTTAdmin)
admin.site.register(user_models.Cafe, CafeAdmin)
admin.site.register(user_models.News, NewsAdmin)
admin.site.register(user_models.Review, ReviewAdmin)
admin.site.register(user_models.Album, AlbumAdmin)
admin.site.register(user_models.ReviewLikeDislike, ReviewLikeDislikeAdmin)
admin.site.register(user_models.Notifications, NotificationsAdmin)
admin.site.register(user_models.File, FileAdminPanel)
admin.site.register(user_models.Cashier)
admin.site.register(user_models.WeekTime)
admin.site.register(user_models.Point, PointAdmin)
admin.site.register(user_models.FreeItem, FreeItemAdmin)
admin.site.register(user_models.CafeGeneralSettings, CafeGeneralSettingsAdmin)
admin.site.register(user_models.InvitedUser)
admin.site.register(user_models.SocialProfile)
