from django.contrib import admin

from .models import Comment, Report, Topic, Vote


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'created_by', 'created_at')
    search_fields = ('title', 'description')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('topic', 'user', 'parent', 'created_at')
    search_fields = ('text',)


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('topic', 'user', 'choice', 'created_at')


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('status', 'reported_by', 'topic', 'comment', 'created_at')
    list_filter = ('status',)
    search_fields = ('reason', 'admin_note')
