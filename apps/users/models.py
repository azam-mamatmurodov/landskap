# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os

from django.db import models
from django.contrib.auth.models import AbstractUser, PermissionsMixin, BaseUserManager
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.shortcuts import reverse
from django.db.models.signals import post_save
from mptt.models import MPTTModel, TreeForeignKey
from ckeditor.fields import RichTextField
from geosimple.fields import GeohashField
from autoslug.fields import AutoSlugField
from localflavor.us.models import USStateField

from project import tasks as project_tasks
from project import modules as project_modules

from .managers import (
    CafeManager,
    AlbumManager,
)


GENDERS = (
    ('male', _('Male')),
    ('female', _('Female')),
)

WEEK_DAYS = (
    ('monday', _('Monday'),),
    ('tuesday', _('Tuesday'),),
    ('wednesday', _('Wednesday'),),
    ('thursday', _('Thursday'),),
    ('friday', _('Friday'),),
    ('saturday', _('Saturday'),),
    ('sunday', _('Sunday'),),
)


def get_week_day(day):
    for key, week_day in enumerate(WEEK_DAYS):
        if key == day:
            return week_day[0]
    return None


class Album(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_created=True, auto_now_add=True, auto_now=False, editable=True)
    updated_at = models.DateTimeField(auto_created=True, auto_now_add=False, auto_now=True, editable=True)
    cafe = models.ForeignKey('Cafe', on_delete=models.CASCADE, null=True, blank=True)

    def get_files(self, obj):
        return File.objects.filter(album=self)

    def __str__(self):
        return "Album - {}".format(self.id)

    objects = AlbumManager()


class File(models.Model):
    file = models.FileField(upload_to='album/%y/%m/%d', null=True, blank=True, default='default.png')
    album = models.ForeignKey(Album, on_delete=models.CASCADE)

    def extension(self):
        name, extension = os.path.splitext(self.file.name)
        return extension

    def is_image(self):
        if self.extension().lower() in ['.png', '.jpg', '.jpeg']:
            return True
        return False


class UserManager(BaseUserManager):

    use_in_migrations = True

    def _create_user(self, phone, password, **extra_fields):
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(phone, password, **extra_fields)

    def create_superuser(self, phone, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(phone, password, **extra_fields)


class CafeOwnerManager(BaseUserManager):

    def get_queryset(self):
        return super().get_queryset().filter(user_type=User.OWNER)


class User(AbstractUser):
    OWNER = 1
    USER = 2
    USER_TYPE_CHOICES = (
        (OWNER, _('Cafe owner')),
        (USER, _('Simple user')),
    )
    username = models.CharField(max_length=12, null=True, blank=True)
    phone = models.CharField(max_length=12, unique=True)
    user_type = models.PositiveSmallIntegerField(choices=USER_TYPE_CHOICES, default=USER)
    first_name = models.CharField(_('First name'), max_length=30, blank=True)
    last_name = models.CharField(_('Last name'), max_length=30, blank=True)
    date_joined = models.DateTimeField(_('Date joined'), auto_now_add=True)
    is_active = models.BooleanField(_('Active'), default=True)
    date_of_birthday = models.DateField(_('date of birthday'), null=True, blank=True, )
    gender = models.CharField(choices=GENDERS, max_length=6, null=True, blank=True, )
    avatar = models.ImageField(null=True, default='default.png')
    referral_code = models.CharField(max_length=60, null=True, blank=True)
    is_can_reject = models.BooleanField(_('Reject'), default=False)
    USERNAME_FIELD = 'phone'
    objects = UserManager()
    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        return self.phone

    def get_avatar(self, request):
        return request.build_absolute_uri(self.avatar.url)

    @property
    def is_cashier(self):
        return Cashier.objects.filter(cashier=self).count()

    def set_referral_code(self):
        self.referral_code = "{:06}".format(self.pk)


class SocialProfile(models.Model):
    FACEBOOK = 'facebook'
    GOOGLE = 'google'
    PROVIDERS = (
        (FACEBOOK, 'Facebook'),
        (GOOGLE, 'Google'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='social_profile')
    provider = models.CharField(choices=PROVIDERS, max_length=60)
    social_user_id = models.CharField(max_length=254)
    token = models.TextField()


class CafeOwner(User):
    objects = CafeOwnerManager()

    class Meta:
        proxy = True


class Category(MPTTModel):
    name = models.CharField(max_length=50, unique=True)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True)
    is_top = models.BooleanField(default=False)
    icon = models.ImageField(upload_to='category/', default='default.png')
    svg_icon = models.FileField(upload_to='category/', default='default.png')

    class MPTTMeta:
        order_insertion_by = ['name']

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

    def __str__(self):
        return "{}".format(self.name)


class WeekTime(models.Model):
    day = models.CharField(choices=WEEK_DAYS, max_length=15,)
    opening_time = models.TimeField(null=True, blank=True)
    closing_time = models.TimeField(null=True, blank=True)
    is_default = models.BooleanField(default=False)
    cafe = models.ForeignKey('Cafe', null=True, related_name='week_time')

    def __str__(self):
        return self.day


class Cafe(models.Model):
    BLOCKED = 0
    ACTIVE = 1
    PENDING = 2
    STATUS = (
        (BLOCKED, _('Blocked')),
        (ACTIVE, _('Active')),
        (PENDING, _('Pending')),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, related_name='cafe_owner',
                             verbose_name=_('Cafe owner'))
    cafe_name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, related_name='cafe_category')
    description = RichTextField()
    call_center = models.CharField(max_length=13, verbose_name='Phone')
    website = models.URLField(null=True, blank=True)
    status = models.IntegerField(choices=STATUS, default=BLOCKED)
    location = GeohashField(default={'latitude': 50.822482, 'longitude': -0.141449}, editable=False)
    address = models.TextField(null=True, blank=True, verbose_name=_('Address 1'))
    second_address = models.TextField(null=True, blank=True, verbose_name=_('Address 2'))
    city = models.CharField(null=True, blank=True, max_length=220)
    state = USStateField(null=True)
    postal_code = models.CharField(null=True, max_length=12)
    tax_rate = models.DecimalField(max_digits=100, decimal_places=2)

    objects = CafeManager()

    def __str__(self):
        return self.cafe_name

    @property
    def get_total_rate(self):
        total_rate = 0
        rates = Review.objects.filter(cafe=self).values('rate')
        if len(rates) > 0:
            for rate in rates:
                total_rate += rate['rate']
            total_rate = total_rate / len(rates)
        return total_rate

    @property
    def get_likes(self):
        likes = Review.objects.filter(cafe=self, rate=1).count()
        return likes

    @property
    def get_dislikes(self):
        dislikes = Review.objects.filter(cafe=self, rate=-1).count()
        return dislikes

    def cafe_changed(self):
        self.status = self.PENDING
        self.save()

    def get_time_graphic(self):
        return self.week_time.values('day', 'opening_time', 'closing_time', )

    def get_absolute_url(self):
        return reverse('users:cafe_detail', args=[self.pk])

    @property
    def logo(self):
        return self.user.settings.logo


# Todo: CafeGeneralSettings must be auto generated on cafe_owner created
class CafeGeneralSettings(models.Model):
    owner = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='settings')
    cafe_name = models.CharField(max_length=120, null=True, blank=True)
    exchangeable_product = models.ForeignKey('products.ProductCategory', null=True, blank=True)
    exchangeable_point = models.IntegerField(default=10)
    expiration_days = models.IntegerField(default=30)
    show_reviews = models.BooleanField(default=True)
    logo = models.ImageField(null=True)

    def __str__(self):
        return self.cafe_name or "--empty--"

    class Meta:
        verbose_name = 'Cafe general setting'
        verbose_name_plural = 'Cafe general settings'


class Cashier(models.Model):
    cafe = models.ForeignKey(Cafe, related_name='cafe_cashiers')
    cashier = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='cashiers')

    def __str__(self):
        return "Cafe - {}, Cashier - {}".format(self.cafe.cafe_name, self.cashier)


class Review(MPTTModel):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='review_author')
    parent = TreeForeignKey('self', null=True, blank=True, related_name='review_parent', db_index=True)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_created=True, auto_now_add=True, auto_now=False)
    album = models.ForeignKey(Album, null=True, blank=True, related_name='review_album')
    cafe = models.ForeignKey(Cafe, null=True, related_name='reviews')
    rate = models.FloatField(default=0)

    def get_files(self, obj):
        return File.objects.all()


class Bookmarks(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='bookmark_owner',)
    cafe = models.ForeignKey(Cafe, related_name='bookmarked_cafe', null=True)


class ReviewLikeDislike(models.Model):
    like_dislike_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='review_like_dislike_user')
    rate = models.IntegerField(default=0)
    review = models.ForeignKey(Review, on_delete=models.CASCADE)


class RecentlyViewed(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='user_recently_viewed', on_delete=models.CASCADE)
    cafe = models.ForeignKey(Cafe, on_delete=models.CASCADE, null=True)


class Notifications(models.Model):
    title = models.CharField(max_length=60)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='notification_user', on_delete=models.CASCADE)
    notification_sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='notification_sender', null=True, blank=True,)
    text = models.TextField()
    image = models.ImageField(blank=True, null=True, upload_to='notifications/', default='default.png')
    created_at = models.DateTimeField(auto_created=True, auto_now_add=True, auto_now=False)
    is_read = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'


class News(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL)
    title = models.CharField(max_length=120)
    content = RichTextField()
    image = models.ImageField(default='default.png')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.BooleanField(default=True)
    slug = AutoSlugField(populate_from='title', unique=True, null=True)

    class Meta:
        verbose_name = 'News'
        verbose_name_plural = 'News'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('users:news_detail', args=[self.pk])


class CafeLikeDislike(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='like_dislike_cafe')
    rate = models.IntegerField(default=0)
    cafe = models.ForeignKey(Cafe, on_delete=models.CASCADE)


class Employee(models.Model):
    employer = models.ForeignKey(settings.AUTH_USER_MODEL)
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='employees')


class Point(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='points')
    created_at = models.DateTimeField(auto_now_add=True)
    point_count = models.PositiveIntegerField(default=1)
    root_cafe = models.ForeignKey(CafeGeneralSettings, null=True)
    # Todo: removed cafe_owner, everywhere must be replaced cafe_owner to root_cafe,


class FreeItem(models.Model):
    VALID = 'valid'
    EXPIRED = 'expired'
    REDEEMED = 'redeemed'
    STATUS_CHOICES = (
        (VALID, 'Valid'),
        (EXPIRED, 'Expired'),
        (REDEEMED, 'Redeemed'),
    )
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='product_exchanger')
    created_at = models.DateTimeField(auto_now_add=True)
    point_count = models.PositiveIntegerField(default=1)
    root_cafe = models.ForeignKey(CafeGeneralSettings, null=True, blank=True, related_name='exchanged_product')
    product = models.ForeignKey('products.Product', null=True, blank=True)
    expire_time = models.DateTimeField(null=True)
    status = models.CharField(choices=STATUS_CHOICES, default=VALID, max_length=60)

    def get_status(self):
        return self.status

    @classmethod
    def filter_by_day(self, day):
        return FreeItem.objects.filter(expire_time__day=day.day, expire_time__month=day.month,
                                       expire_time__year=day.year)


class InvitedUser(models.Model):
    user = models.OneToOneField(User, related_name='inviter')
    inviter = models.ForeignKey(User, related_name='invitee')
    given_free_item = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


def news_create_handler(sender, instance, **kwargs):
    if kwargs['created']:
        project_tasks.send_news_notifications.delay(news_id=instance.id)


post_save.connect(receiver=news_create_handler, sender=News)


def point_create_handler(sender, instance, **kwargs):
    if kwargs['created']:
        phone = instance.owner.phone
        sent = project_modules.send_push_for_topic(phone=phone, message='You have new point', tag='points')
        import os
        from django.conf import settings
        file = open('/mnt/python/projects/landskap/sent_data.txt', 'a+')
        file.write(f"{sent}\n")
        file.close()
        print(f"{sent}")

post_save.connect(receiver=point_create_handler, sender=Point)
