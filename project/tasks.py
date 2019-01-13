from celery import shared_task

from django.utils import timezone
from apps.users import models as user_models
from project import modules as project_modules


@shared_task
def test():
    for i in range(0, 100000):
        print('The test task executed with argument "%s" ' % i)

    print('task finished')


@shared_task
def send_free_item_expire_notifications():
    day_after_tomorrow = timezone.datetime.today() + timezone.timedelta(2)
    free_items = user_models.FreeItem.filter_by_day(day=day_after_tomorrow).select_related('owner')

    for free_item in free_items:
        user = free_item.owner
        message = 'You have free item(s) which expires after 2 days'
        result = project_modules.push_service.notify_topic_subscribers(topic_name=user.phone, message_body=message,
                                                                       sound="Default", tag='free_item_expire_tag')
        user_models.Notifications.objects.create(title='Free item expires', text=message, user_id=user.id)

    print('task finished')


@shared_task
def send_news_notifications(news_id):
    news_intance = user_models.News.objects.get(pk=news_id)
    users = user_models.User.objects.all()
    data_message = {
        'id': news_id
    }
    for user in users:
        result = project_modules.push_service.notify_topic_subscribers(topic_name=user.phone, message_body=news_intance.title,
                                                                       sound="Default", tag='news_tag', data_message=data_message)
        print(result)
