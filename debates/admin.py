from django.contrib import admin
from .models import Bookmark, Comment, Notification, Profile, Reaction, Report, Tag, Topic, Vote


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'status', 'is_featured', 'created_by', 'views_count', 'created_at')
    list_filter = ('category', 'status', 'is_featured', 'created_at')
    search_fields = ('title', 'description')
    filter_horizontal = ('tags',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('topic', 'user', 'stance', 'parent', 'created_at')
    list_filter = ('stance', 'created_at')
    search_fields = ('text', 'user__username', 'topic__title')


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('topic', 'user', 'choice', 'created_at')
    list_filter = ('choice', 'created_at')
    search_fields = ('topic__title', 'user__username')


@admin.register(Reaction)
class ReactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'comment', 'emoji', 'created_at')
    list_filter = ('emoji', 'created_at')


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ('user', 'topic', 'created_at')
    search_fields = ('user__username', 'topic__title')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_suspended', 'reputation_score')
    list_filter = ('is_suspended',)
    search_fields = ('user__username', 'bio')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('status', 'reported_by', 'topic', 'comment', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('reason', 'admin_note', 'reported_by__username')
