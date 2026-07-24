from django.urls import path

from . import views

urlpatterns = [
    path('', views.topic_list, name='topic_list'),
    path('signup/', views.signup, name='signup'),
    path('topic/create/', views.topic_create, name='topic_create'),
    path('topic/<int:pk>/', views.topic_detail, name='topic_detail'),
    path('topic/<int:pk>/vote/', views.topic_vote, name='topic_vote'),
    path('comment/<int:pk>/edit/', views.comment_edit, name='comment_edit'),
    path('comment/<int:pk>/delete/', views.comment_delete, name='comment_delete'),
    path('report/topic/<int:pk>/', views.report_topic, name='report_topic'),
    path('report/comment/<int:pk>/', views.report_comment, name='report_comment'),
    path('profile/<str:username>/', views.user_profile, name='user_profile'),
    path('profile/<str:username>/edit/', views.profile_edit, name='profile_edit'),
    path('notifications/', views.notifications_page, name='notifications_page'),
    path('notifications/<int:pk>/mark-read/', views.mark_notification_read, name='mark_notification_read'),
    path('moderation/reports/', views.moderation_reports, name='moderation_reports'),
    path('moderation/report/<int:pk>/resolve/', views.resolve_report, name='resolve_report'),
    path('moderation/user/<int:pk>/suspend/', views.toggle_user_suspension, name='toggle_user_suspension'),
]
