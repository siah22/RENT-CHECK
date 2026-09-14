from django.db.models import Q

from engagement.models import Message, Notification, Report
from properties.models import Property


def notifications(request):
    data = {
        "unread_notifications_count": 0,
        "unread_message_count": 0,
        "admin_pending_properties_count": 0,
        "admin_pending_reports_count": 0,
    }
    if request.user.is_authenticated:
        data["unread_notifications_count"] = Notification.objects.filter(
            user=request.user, is_read=False
        ).count()
        data["unread_message_count"] = Message.objects.filter(is_read=False).exclude(
            sender=request.user
        ).filter(
            Q(conversation__tenant=request.user) | Q(conversation__owner=request.user)
        ).count()
        if request.user.is_admin_role:
            data["admin_pending_properties_count"] = Property.objects.filter(
                verification_status=Property.VerificationStatus.PENDING
            ).count()
            data["admin_pending_reports_count"] = Report.objects.filter(
                status=Report.Status.PENDING
            ).count()
    return data
