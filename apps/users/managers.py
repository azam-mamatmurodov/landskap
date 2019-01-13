from datetime import datetime, date

from django.contrib.auth.models import BaseUserManager
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Q, Avg
from django.utils.translation import ugettext_lazy as _
from django.apps import apps

from geosimple.managers import GeoManager, GeoQuerySet


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


current_day = date.today().weekday()
current_week_day = get_week_day(current_day)


class CafeQueryset(GeoQuerySet):
    def get_nearby_locations(self, location_lat_long, distance, **kwargs):
        cafe = apps.get_model(app_label='users', model_name='cafe')
        queryset = self.filter(location__distance_lt=(location_lat_long, distance), status=cafe.ACTIVE)
        # distance in kilometres
        if kwargs.get('rate') or kwargs.get('states'):
            week_time_model = apps.get_model(app_label='users', model_name='weektime')
            queryset = queryset
            if kwargs.get('rate'):
                rate = kwargs.get('rate', 0)
                queryset = queryset.annotate(total_rate=Avg('review__rate')).filter(
                    Q(total_rate__lte=rate) | Q(total_rate=None))

            if kwargs.get('states'):
                now = datetime.now().time()
                states = kwargs.get('states').split(',')
                open_cafes = closed_cafes = unknown_cafes = list()

                current_day_available_cafes_queryset = week_time_model.objects.filter(day=current_week_day)

                if states.__contains__('open'):
                    open_cafes = current_day_available_cafes_queryset.filter(opening_time__lte=now,
                                                                             closing_time__gte=now).values_list(
                        'cafe', flat=True)
                if states.__contains__('closed'):
                    open_cafes_queryset = current_day_available_cafes_queryset.filter(opening_time__lte=now,
                                                                                      closing_time__gte=now).values_list(
                        'cafe', flat=True)
                    closed_cafes_queryset = current_day_available_cafes_queryset.values_list('cafe',
                                                                                             flat=True)
                    closed_cafes = list(set(closed_cafes_queryset) - set(open_cafes_queryset))

                if states.__contains__('unknown'):
                    current_day_available_cafes = current_day_available_cafes_queryset.distinct(
                        'cafe').values_list('cafe', flat=True)
                    unknown_cafes = queryset.exclude(pk__in=current_day_available_cafes).values_list('id',
                                                                                                     flat=True)
                all_cafes = list(open_cafes) + list(closed_cafes) + list(unknown_cafes)
                queryset = queryset.filter(pk__in=all_cafes)
        return queryset


class CafeManager(GeoManager):
    def get_queryset(self):
        return CafeQueryset(self.model, using=self._db)  # Important!

    def get_nearby_locations(self, location_lat_long, distance, **kwargs):
        return self.get_queryset().get_nearby_locations(location_lat_long, distance,**kwargs)


class AlbumManager(models.Manager):

    def get_cafe_images(self, cafe_user):
        return self.get_queryset().filter(cafe__user=cafe_user).values_list('files_set')


