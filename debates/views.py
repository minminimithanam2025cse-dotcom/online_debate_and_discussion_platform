from datetime import timedelta

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Count, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import CommentForm, CustomSignUpForm, ProfileForm, ReportForm, TopicForm
from .models import Bookmark, Comment, Notification, Profile, Reaction, Report, Tag, Topic, Vote


def custom_404(request, exception):
    return render(request, '404.html', status=404)


def custom_500(request):
    return render(request, '500.html', status=500)


def get_user_profile(user):
    return Profile.objects.get_or_create(user=user)[0]


def user_suspended(user):
    profile = get_user_profile(user)
    return profile.is_suspended


def create_notification(user, message, link=''):
    Notification.objects.create(user=user, message=message, link=link)


def topic_list(request):
    queryset = Topic.objects.select_related('created_by', 'created_by__profile').prefetch_related('tags', 'comments', 'votes')
    q = request.GET.get('q', '').strip()
    category = request.GET.get('category', '').strip()
    tag = request.GET.get('tag', '').strip()
    status = request.GET.get('status', '').strip()
    sort = request.GET.get('sort', 'newest')

    if q:
        queryset = queryset.filter(
            Q(title__icontains=q)
            | Q(description__icontains=q)
            | Q(category__icontains=q)
            | Q(tags__name__icontains=q)
        ).distinct()

    if category and category != 'all':
        queryset = queryset.filter(category=category)

    if tag:
        queryset = queryset.filter(tags__name__iexact=tag)

    if status in ('active', 'concluded'):
        queryset = queryset.filter(status=status)

    queryset = queryset.annotate(
        vote_count=Count('votes', distinct=True),
        discussion_count=Count('comments', distinct=True),
    )

    if sort == 'most_voted':
        queryset = queryset.order_by('-vote_count', '-created_at')
    elif sort == 'most_discussed':
        queryset = queryset.order_by('-discussion_count', '-created_at')
    elif sort == 'trending':
        seven_days_ago = timezone.now() - timedelta(days=7)
        queryset = queryset.annotate(
            trend_score=Count('votes', distinct=True) + Count('comments', distinct=True)
        ).order_by('-trend_score', '-created_at')
    else:
        queryset = queryset.order_by('-created_at')

    # Trending topics for sidebar widget
    seven_days_ago = timezone.now() - timedelta(days=7)
    trending_topics = Topic.objects.filter(created_at__gte=seven_days_ago).annotate(
        vote_count=Count('votes', distinct=True),
        discussion_count=Count('comments', distinct=True),
        activity_score=Count('votes', distinct=True) + Count('comments', distinct=True)
    ).order_by('-activity_score', '-created_at')[:5]

    # Category pills with count
    category_counts = {cat[0]: 0 for cat in Topic.CATEGORY_CHOICES}
    for item in Topic.objects.values('category').annotate(count=Count('id')):
        if item['category'] in category_counts:
            category_counts[item['category']] = item['count']

    categories_data = [
        {'slug': 'all', 'name': 'All Categories', 'icon': 'fa-globe', 'count': Topic.objects.count()},
        {'slug': 'technology', 'name': 'Technology', 'icon': 'fa-microchip', 'count': category_counts.get('technology', 0)},
        {'slug': 'politics', 'name': 'Politics', 'icon': 'fa-landmark', 'count': category_counts.get('politics', 0)},
        {'slug': 'science', 'name': 'Science', 'icon': 'fa-flask', 'count': category_counts.get('science', 0)},
        {'slug': 'culture', 'name': 'Culture', 'icon': 'fa-masks-theater', 'count': category_counts.get('culture', 0)},
        {'slug': 'sports', 'name': 'Sports', 'icon': 'fa-futbol', 'count': category_counts.get('sports', 0)},
        {'slug': 'general', 'name': 'General', 'icon': 'fa-comments', 'count': category_counts.get('general', 0)},
    ]

    # Featured topic
    featured_topic = Topic.objects.filter(is_featured=True).first()
    if not featured_topic and queryset.exists():
        featured_topic = queryset.first()

    # User bookmarks list for quick indicator
    user_bookmarked_ids = set()
    if request.user.is_authenticated:
        user_bookmarked_ids = set(request.user.bookmarks.values_list('topic_id', flat=True))

    paginator = Paginator(queryset, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    platform_stats = {
        'total_topics': Topic.objects.count(),
        'total_votes': Vote.objects.count(),
        'total_comments': Comment.objects.count(),
        'total_debaters': User.objects.count(),
    }

    context = {
        'page_obj': page_obj,
        'q': q,
        'selected_category': category,
        'selected_tag': tag,
        'selected_status': status,
        'sort': sort,
        'trending_topics': trending_topics,
        'categories_data': categories_data,
        'featured_topic': featured_topic,
        'platform_stats': platform_stats,
        'user_bookmarked_ids': user_bookmarked_ids,
        'popular_tags': Tag.objects.annotate(t_count=Count('topics')).order_by('-t_count')[:10],
        'sort_options': [
            ('newest', 'Newest Discussions'),
            ('trending', 'Trending Now 🔥'),
            ('most_voted', 'Most Voted'),
            ('most_discussed', 'Most Debated'),
        ],
    }
    return render(request, 'debates/topic_list.html', context)


@login_required(login_url='login')
def topic_create(request):
    if user_suspended(request.user):
        messages.error(request, 'Your account is suspended and cannot create topics.')
        return redirect('topic_list')

    if request.method == 'POST':
        form = TopicForm(request.POST)
        if form.is_valid():
            topic = form.save(commit=False)
            topic.created_by = request.user
            topic.save()
            tag_names = form.cleaned_data.get('tags_input', [])
            if tag_names:
                tags = []
                for tag_name in tag_names:
                    tag, _ = Tag.objects.get_or_create(name=tag_name)
                    tags.append(tag)
                topic.tags.set(tags)
            messages.success(request, 'Your debate topic was published successfully! Let the discourse begin.')
            return redirect('topic_detail', pk=topic.pk)
    else:
        form = TopicForm()
    return render(request, 'debates/topic_form.html', {'form': form, 'title': 'Create a New Debate Topic'})


def topic_detail(request, pk):
    topic = get_object_or_404(Topic.objects.select_related('created_by', 'created_by__profile'), pk=pk)

    # Increment view counter smoothly
    Topic.objects.filter(pk=pk).update(views_count=models.F('views_count') + 1)
    topic.refresh_from_db(fields=['views_count'])

    stance_filter = request.GET.get('stance', 'all')
    comments_qs = topic.comments.select_related('user', 'user__profile', 'parent').prefetch_related(
        'replies__user', 'replies__user__profile', 'reactions', 'reactions__user'
    ).filter(parent__isnull=True)

    if stance_filter in ('for', 'against', 'neutral'):
        comments_qs = comments_qs.filter(stance=stance_filter)

    vote_history = topic.votes.select_related('user', 'user__profile').order_by('-created_at')
    total_votes = topic.total_votes
    for_count = topic.for_votes
    against_count = topic.against_votes

    for_percent = round((for_count / total_votes) * 100, 1) if total_votes else 50.0
    against_percent = round((against_count / total_votes) * 100, 1) if total_votes else 50.0

    user_vote = None
    is_bookmarked = False
    if request.user.is_authenticated:
        user_vote = topic.votes.filter(user=request.user).first()
        is_bookmarked = topic.bookmarks.filter(user=request.user).exists()

    # Stance counts for arguments breakdown
    all_root_comments = topic.comments.filter(parent__isnull=True)
    counts_by_stance = {
        'all': all_root_comments.count(),
        'for': all_root_comments.filter(stance='for').count(),
        'against': all_root_comments.filter(stance='against').count(),
        'neutral': all_root_comments.filter(stance='neutral').count(),
    }

    comment_form = CommentForm()
    if request.method == 'POST' and request.user.is_authenticated:
        if user_suspended(request.user):
            messages.error(request, 'Your account is suspended and cannot perform actions right now.')
            return redirect('topic_detail', pk=topic.pk)

        # Legacy fallback if reaction posted directly to topic_detail
        if request.POST.get('reaction'):
            comment = get_object_or_404(Comment, pk=request.POST.get('comment_id'))
            emoji = request.POST.get('reaction')
            reaction = Reaction.objects.filter(user=request.user, comment=comment).first()
            if reaction:
                if reaction.emoji == emoji:
                    reaction.delete()
                    messages.success(request, 'Reaction removed.')
                else:
                    reaction.emoji = emoji
                    reaction.save(update_fields=['emoji'])
                    messages.success(request, 'Reaction updated.')
            else:
                Reaction.objects.create(user=request.user, comment=comment, emoji=emoji)
                messages.success(request, 'Reaction recorded.')
            return redirect('topic_detail', pk=topic.pk)

        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            parent_id = request.POST.get('parent_id')
            parent = None
            if parent_id:
                parent = get_object_or_404(Comment, pk=parent_id, topic=topic)
            comment = comment_form.save(commit=False)
            comment.topic = topic
            comment.user = request.user
            comment.parent = parent
            # If stance wasn't picked in reply form, inherit or neutral
            if not comment.stance:
                comment.stance = 'neutral'
            comment.save()

            if parent:
                create_notification(parent.user, f'{request.user.username} replied to your argument.', f'/topic/{topic.pk}/#comment-{comment.pk}')
            elif topic.created_by != request.user:
                create_notification(topic.created_by, f'{request.user.username} posted an argument on your debate.', f'/topic/{topic.pk}/#comment-{comment.pk}')
            messages.success(request, 'Your argument was posted to the debate.')
            return redirect(f'/topic/{topic.pk}/#comment-{comment.pk}')
        else:
            messages.error(request, 'Please check your argument input.')

    related_topics = Topic.objects.filter(category=topic.category).exclude(pk=topic.pk)[:4]

    context = {
        'topic': topic,
        'comments': comments_qs,
        'vote_history': vote_history,
        'comment_form': comment_form,
        'user_vote': user_vote,
        'is_bookmarked': is_bookmarked,
        'for_percent': for_percent,
        'against_percent': against_percent,
        'for_count': for_count,
        'against_count': against_count,
        'total_votes': total_votes,
        'stance_filter': stance_filter,
        'counts_by_stance': counts_by_stance,
        'reaction_choices': Reaction.EMOJI_CHOICES,
        'related_topics': related_topics,
    }
    return render(request, 'debates/topic_detail.html', context)


@login_required(login_url='login')
def topic_vote(request, pk):
    topic = get_object_or_404(Topic, pk=pk)
    if user_suspended(request.user):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
            return JsonResponse({'status': 'error', 'message': 'Your account is suspended and cannot vote.'}, status=403)
        messages.error(request, 'Your account is suspended and cannot vote.')
        return redirect('topic_detail', pk=topic.pk)

    if request.method != 'POST':
        return redirect('topic_detail', pk=topic.pk)

    choice = request.POST.get('choice')
    if choice not in ('for', 'against'):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
            return JsonResponse({'status': 'error', 'message': 'Invalid vote choice.'}, status=400)
        messages.error(request, 'Please choose a valid vote option.')
        return redirect('topic_detail', pk=topic.pk)

    vote = topic.votes.filter(user=request.user).first()
    action = 'recorded'
    if vote:
        if vote.choice == choice:
            action = 'retained'
        else:
            vote.choice = choice
            vote.save(update_fields=['choice'])
            action = 'changed'
    else:
        Vote.objects.create(topic=topic, user=request.user, choice=choice)
        action = 'recorded'
        if topic.created_by != request.user:
            create_notification(topic.created_by, f'{request.user.username} voted on your debate: "{topic.title[:40]}"', f'/topic/{topic.pk}/')

    total = topic.total_votes
    for_count = topic.for_votes
    against_count = topic.against_votes
    for_pct = round((for_count / total) * 100, 1) if total else 50.0
    against_pct = round((against_count / total) * 100, 1) if total else 50.0

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
        return JsonResponse({
            'status': 'ok',
            'action': action,
            'choice': choice,
            'for_votes': for_count,
            'against_votes': against_count,
            'total_votes': total,
            'for_percent': for_pct,
            'against_percent': against_pct,
            'message': f'Your vote ({choice.upper()}) was successfully {action}!'
        })

    messages.success(request, f'Your vote has been {action} successfully.')
    return redirect('topic_detail', pk=topic.pk)


@login_required(login_url='login')
def topic_bookmark(request, pk):
    topic = get_object_or_404(Topic, pk=pk)
    bookmark = Bookmark.objects.filter(user=request.user, topic=topic).first()
    if bookmark:
        bookmark.delete()
        bookmarked = False
        msg = 'Debate removed from your bookmarks.'
    else:
        Bookmark.objects.create(user=request.user, topic=topic)
        bookmarked = True
        msg = 'Debate saved to your bookmarks!'

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
        return JsonResponse({
            'status': 'ok',
            'bookmarked': bookmarked,
            'message': msg,
            'bookmark_count': topic.bookmarks.count()
        })

    messages.success(request, msg)
    return redirect('topic_detail', pk=topic.pk)


@login_required(login_url='login')
def comment_react(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    if user_suspended(request.user):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
            return JsonResponse({'status': 'error', 'message': 'Account is suspended.'}, status=403)
        messages.error(request, 'Your account is suspended.')
        return redirect('topic_detail', pk=comment.topic.pk)

    if request.method != 'POST':
        return redirect('topic_detail', pk=comment.topic.pk)

    emoji = request.POST.get('reaction', '').strip()
    valid_emojis = [e[0] for e in Reaction.EMOJI_CHOICES]
    if emoji not in valid_emojis:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Invalid reaction.'}, status=400)
        return redirect('topic_detail', pk=comment.topic.pk)

    reaction = Reaction.objects.filter(user=request.user, comment=comment).first()
    active_emoji = None
    if reaction:
        if reaction.emoji == emoji:
            reaction.delete()
            active_emoji = None
            msg = 'Reaction removed'
        else:
            reaction.emoji = emoji
            reaction.save(update_fields=['emoji'])
            active_emoji = emoji
            msg = 'Reaction updated'
    else:
        Reaction.objects.create(user=request.user, comment=comment, emoji=emoji)
        active_emoji = emoji
        msg = 'Reaction added'
        if comment.user != request.user:
            create_notification(comment.user, f'{request.user.username} reacted to your comment.', f'/topic/{comment.topic.pk}/#comment-{comment.pk}')

    counts = comment.reaction_counts

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
        return JsonResponse({
            'status': 'ok',
            'counts': counts,
            'active_emoji': active_emoji,
            'message': msg,
        })

    messages.success(request, msg)
    return redirect('topic_detail', pk=comment.topic.pk)


@login_required(login_url='login')
def comment_edit(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    if user_suspended(request.user):
        messages.error(request, 'Your account is suspended and cannot edit comments.')
        return redirect('topic_detail', pk=comment.topic.pk)
    if comment.user != request.user:
        messages.error(request, 'You can only edit your own comments.')
        return redirect('topic_detail', pk=comment.topic.pk)

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your argument has been updated.')
            return redirect(f'/topic/{comment.topic.pk}/#comment-{comment.pk}')
    else:
        form = CommentForm(instance=comment)
    return render(request, 'debates/comment_form.html', {'form': form, 'comment': comment})


@login_required(login_url='login')
def comment_delete(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    if user_suspended(request.user):
        messages.error(request, 'Your account is suspended and cannot delete comments.')
        return redirect('topic_detail', pk=comment.topic.pk)
    if comment.user != request.user:
        messages.error(request, 'You can only delete your own comments.')
        return redirect('topic_detail', pk=comment.topic.pk)

    topic_pk = comment.topic.pk
    comment.delete()
    messages.success(request, 'Argument removed successfully.')
    return redirect('topic_detail', pk=topic_pk)


@login_required(login_url='login')
def report_topic(request, pk):
    topic = get_object_or_404(Topic, pk=pk)
    if request.method == 'POST':
        form = ReportForm(request.POST, instance=Report(topic=topic, reported_by=request.user))
        if form.is_valid():
            form.save()
            messages.success(request, 'Your report has been submitted to moderators.')
            return redirect('topic_detail', pk=topic.pk)
    else:
        form = ReportForm()
    return render(request, 'debates/report_form.html', {'form': form, 'item_type': 'topic', 'item': topic})


@login_required(login_url='login')
def report_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    if request.method == 'POST':
        form = ReportForm(request.POST, instance=Report(comment=comment, reported_by=request.user))
        if form.is_valid():
            form.save()
            messages.success(request, 'Your report has been submitted to moderators.')
            return redirect('topic_detail', pk=comment.topic.pk)
    else:
        form = ReportForm()
    return render(request, 'debates/report_form.html', {'form': form, 'item_type': 'comment', 'item': comment})


def user_profile(request, username):
    user = get_object_or_404(User.objects.select_related('profile'), username=username)
    profile = get_user_profile(user)
    topics = Topic.objects.filter(created_by=user).order_by('-created_at')
    comments = Comment.objects.filter(user=user).select_related('topic').order_by('-created_at')
    votes = Vote.objects.filter(user=user).select_related('topic').order_by('-created_at')
    bookmarked_topics = Topic.objects.filter(bookmarks__user=user).select_related('created_by')

    context = {
        'profile_user': user,
        'profile': profile,
        'topics': topics,
        'comments': comments,
        'votes': votes,
        'bookmarked_topics': bookmarked_topics,
        'reputation': profile.reputation_score,
        'rank_badge': profile.rank_badge,
    }
    return render(request, 'debates/profile.html', context)


@login_required(login_url='login')
def profile_edit(request, username):
    if request.user.username != username:
        messages.error(request, 'You can only edit your own profile.')
        return redirect('user_profile', username=request.user.username)

    profile = get_user_profile(request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile was updated successfully.')
            return redirect('user_profile', username=request.user.username)
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'debates/profile_edit.html', {'form': form, 'profile': profile})


@login_required(login_url='login')
def notifications_page(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'debates/notifications.html', {'notifications': notifications})


@login_required(login_url='login')
def mark_notification_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save(update_fields=['is_read'])
    return redirect(notification.link or 'notifications_page')


@login_required(login_url='login')
def mark_all_notifications_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
        return JsonResponse({'status': 'ok'})
    messages.success(request, 'All notifications marked as read.')
    return redirect('notifications_page')


def leaderboard(request):
    # Fetch active users and rank by reputation score
    users = User.objects.filter(is_active=True).select_related('profile').prefetch_related('topics', 'comments', 'votes')
    leaderboard_data = []
    for u in users:
        p = get_user_profile(u)
        leaderboard_data.append({
            'user': u,
            'profile': p,
            'score': p.reputation_score,
            'badge': p.rank_badge,
            'topic_count': u.topics.count(),
            'comment_count': u.comments.count(),
            'vote_count': u.votes.count(),
        })

    leaderboard_data.sort(key=lambda x: x['score'], reverse=True)
    top_debaters = leaderboard_data[:20]

    return render(request, 'debates/leaderboard.html', {'top_debaters': top_debaters})


@staff_member_required
def moderation_reports(request):
    reports = Report.objects.select_related('topic', 'comment', 'reported_by').all()
    pending_count = reports.filter(status='pending').count()
    return render(request, 'debates/moderation_reports.html', {'reports': reports, 'pending_count': pending_count})


@staff_member_required
@login_required(login_url='login')
def toggle_user_suspension(request, pk):
    user = get_object_or_404(User, pk=pk)
    profile = get_user_profile(user)
    profile.is_suspended = not profile.is_suspended
    profile.save(update_fields=['is_suspended'])
    status = 'suspended' if profile.is_suspended else 'active'
    messages.success(request, f'User {user.username} is now {status}.')
    return redirect('moderation_reports')


@staff_member_required
@login_required(login_url='login')
def resolve_report(request, pk):
    report = get_object_or_404(Report, pk=pk)
    if request.method == 'POST':
        status = request.POST.get('status')
        admin_note = request.POST.get('admin_note', '').strip()
        if status in dict(Report.STATUS_CHOICES):
            report.status = status
            report.admin_note = admin_note
            report.save(update_fields=['status', 'admin_note'])
            if report.comment and report.comment.user:
                create_notification(report.comment.user, 'A moderator reviewed a report concerning your argument.', '/moderation/reports/')
            if report.topic and report.topic.created_by:
                create_notification(report.topic.created_by, 'A moderator reviewed a report concerning your debate topic.', '/moderation/reports/')
            messages.success(request, 'Report status updated successfully.')
        else:
            messages.error(request, 'Invalid report status.')
    return redirect('moderation_reports')


def signup(request):
    if request.method == 'POST':
        form = CustomSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.get_or_create(user=user)
            login(request, user)
            messages.success(request, f'Welcome to the platform, {user.username}! Your account is active.')
            return redirect('topic_list')
    else:
        form = CustomSignUpForm()
    return render(request, 'registration/signup.html', {'form': form})
