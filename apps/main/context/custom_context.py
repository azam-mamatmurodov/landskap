from apps.users.models import Notifications


def notifications(request):
    if request.user.is_authenticated:
        all_notifications = Notifications.objects.filter(user=request.user)
        latest_notifications = all_notifications[:3]
    return locals()