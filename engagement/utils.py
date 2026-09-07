from .models import Notification


def notify(user, message, link=""):
    Notification.objects.create(user=user, message=message, link=link)
