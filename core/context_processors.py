from engagement.models import Notification


def notifications(request):
    count = 0
    if request.user.is_authenticated:
        count = Notification.objects.filter(user=request.user, is_read=False).count()
    return {"unread_notifications_count": count}
