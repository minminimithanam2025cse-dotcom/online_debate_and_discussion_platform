from .models import Notification


def unread_notifications_count(request):
    if request.user.is_authenticated:
        unread_qs = Notification.objects.filter(user=request.user, is_read=False)
        count = unread_qs.count()
        recent_notifications = unread_qs.order_by('-created_at')[:5]
    else:
        count = 0
        recent_notifications = []
    return {
        'unread_notifications_count': count,
        'navbar_notifications': recent_notifications,
    }
