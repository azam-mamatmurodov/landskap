from django.utils import timezone
from django.conf import settings
from apps.users import models as user_models

from pyfcm import FCMNotification

push_service = FCMNotification(api_key=settings.FCM_API_KEY)


def send_push_for_topic(phone, message, tag='simple_notification', **kwargs):
    receiver = user_models.User.objects.get(phone=phone)
    if kwargs.get('notification_sender'):
        notification_sender = user_models.User.objects.get(id=kwargs.get('notification_sender'))
    else:
        notification_sender = None
    user_models.Notifications.objects.create(**{
        'title': kwargs.get('title', message),
        'user': receiver,
        'notification_sender': notification_sender,
        'text': message,
        })
    return push_service.notify_topic_subscribers(topic_name=phone, message_body=message, sound="Default", tag=tag)


def point_free_item_calculation(cafe, client, count):
    # Here point calculation
    root_cafe, cafes_root_created = user_models.CafeGeneralSettings.objects.get_or_create(owner=cafe.user,
                                                                                          defaults={
                                                                                              'cafe_name': 'Not given'
                                                                                          })

    point, point_created = user_models.Point.objects.get_or_create(root_cafe=root_cafe,
                                                                   owner_id=client.id,
                                                                   defaults={'point_count': count
                                                                             })
    if not point_created:
        # Todo: Calculate total point
        point.point_count += count
        point.save()
    if point.point_count >= root_cafe.exchangeable_point:
        # Todo: Create new free item and subtract point
        expire_datetime = timezone.now() + timezone.timedelta(days=root_cafe.expiration_days)
        user_models.FreeItem.objects.create(
            owner_id=client.id,
            root_cafe_id=root_cafe.id,
            point_count=root_cafe.exchangeable_point,
            expire_time=expire_datetime
        )
        point.point_count -= root_cafe.exchangeable_point
        point.save()
    return point

