from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import CommentForm, CustomSignUpForm, ReportForm, TopicForm
from .models import Comment, Report, Topic, Vote


def custom_404(request, exception):
    return render(request, '404.html', status=404)


def custom_500(request):
    return render(request, '500.html', status=500)


def topic_list(request):
    queryset = Topic.objects.select_related('created_by').prefetch_related('comments', 'votes')
    q = request.GET.get('q', '').strip()
    sort = request.GET.get('sort', 'newest')

    if q:
        queryset = queryset.filter(Q(title__icontains=q) | Q(description__icontains=q) | Q(category__icontains=q))

    queryset = queryset.annotate(
        vote_count=Count('votes', distinct=True),
        discussion_count=Count('comments', distinct=True),
    )

    if sort == 'most_voted':
        queryset = queryset.order_by('-vote_count', '-created_at')
    elif sort == 'most_discussed':
        queryset = queryset.order_by('-discussion_count', '-created_at')
    else:
        queryset = queryset.order_by('-created_at')

    paginator = Paginator(queryset, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'q': q,
        'sort': sort,
        'sort_options': [
            ('newest', 'Newest'),
            ('most_voted', 'Most voted'),
            ('most_discussed', 'Most discussed'),
        ],
    }
    return render(request, 'debates/topic_list.html', context)


@login_required(login_url='login')
def topic_create(request):
    if request.method == 'POST':
        form = TopicForm(request.POST)
        if form.is_valid():
            topic = form.save(commit=False)
            topic.created_by = request.user
            topic.save()
            messages.success(request, 'Your topic was created successfully.')
            return redirect('topic_detail', pk=topic.pk)
    else:
        form = TopicForm()
    return render(request, 'debates/topic_form.html', {'form': form, 'title': 'Create Topic'})


def topic_detail(request, pk):
    topic = get_object_or_404(Topic.objects.select_related('created_by'), pk=pk)
    comments = topic.comments.select_related('user', 'parent').prefetch_related('replies__user').filter(parent__isnull=True)
    vote_history = topic.votes.select_related('user')
    total_votes = topic.total_votes
    for_count = topic.for_votes
    against_count = topic.against_votes

    for_percent = round((for_count / total_votes) * 100, 1) if total_votes else 0
    against_percent = round((against_count / total_votes) * 100, 1) if total_votes else 0

    user_vote = None
    if request.user.is_authenticated:
        user_vote = topic.votes.filter(user=request.user).first()

    comment_form = CommentForm()
    if request.method == 'POST' and request.user.is_authenticated:
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
            comment.save()
            messages.success(request, 'Your comment was posted.')
            return redirect('topic_detail', pk=topic.pk)
        messages.error(request, 'Please correct the comment errors below.')

    return render(
        request,
        'debates/topic_detail.html',
        {
            'topic': topic,
            'comments': comments,
            'vote_history': vote_history,
            'comment_form': comment_form,
            'user_vote': user_vote,
            'for_percent': for_percent,
            'against_percent': against_percent,
            'for_count': for_count,
            'against_count': against_count,
            'total_votes': total_votes,
        },
    )


@login_required(login_url='login')
def topic_vote(request, pk):
    topic = get_object_or_404(Topic, pk=pk)
    if request.method != 'POST':
        return redirect('topic_detail', pk=topic.pk)

    choice = request.POST.get('choice')
    if choice not in ('for', 'against'):
        messages.error(request, 'Please choose a valid vote option.')
        return redirect('topic_detail', pk=topic.pk)

    vote = topic.votes.filter(user=request.user).first()
    if vote:
        vote.choice = choice
        vote.save(update_fields=['choice'])
        messages.success(request, 'Your vote was updated successfully.')
    else:
        Vote.objects.create(topic=topic, user=request.user, choice=choice)
        messages.success(request, 'Your vote was recorded successfully.')

    return redirect('topic_detail', pk=topic.pk)


@login_required(login_url='login')
def comment_edit(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    if comment.user != request.user:
        messages.error(request, 'You can only edit your own comments.')
        return redirect('topic_detail', pk=comment.topic.pk)

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your comment has been updated.')
            return redirect('topic_detail', pk=comment.topic.pk)
    else:
        form = CommentForm(instance=comment)
    return render(request, 'debates/comment_form.html', {'form': form, 'comment': comment})


@login_required(login_url='login')
def comment_delete(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    if comment.user != request.user:
        messages.error(request, 'You can only delete your own comments.')
        return redirect('topic_detail', pk=comment.topic.pk)

    topic_pk = comment.topic.pk
    comment.delete()
    messages.success(request, 'Comment deleted successfully.')
    return redirect('topic_detail', pk=topic_pk)


@login_required(login_url='login')
def report_topic(request, pk):
    topic = get_object_or_404(Topic, pk=pk)
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.topic = topic
            report.reported_by = request.user
            report.save()
            messages.success(request, 'Your report has been submitted for review.')
            return redirect('topic_detail', pk=topic.pk)
    else:
        form = ReportForm()
    return render(request, 'debates/report_form.html', {'form': form, 'item_type': 'topic', 'item': topic})


@login_required(login_url='login')
def report_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.comment = comment
            report.reported_by = request.user
            report.save()
            messages.success(request, 'Your report has been submitted for review.')
            return redirect('topic_detail', pk=comment.topic.pk)
    else:
        form = ReportForm()
    return render(request, 'debates/report_form.html', {'form': form, 'item_type': 'comment', 'item': comment})


def user_profile(request, username):
    user = get_object_or_404(User, username=username)
    topics = Topic.objects.filter(created_by=user).order_by('-created_at')
    comments = Comment.objects.filter(user=user).select_related('topic').order_by('-created_at')
    votes = Vote.objects.filter(user=user).select_related('topic').order_by('-created_at')
    return render(
        request,
        'debates/profile.html',
        {'profile_user': user, 'topics': topics, 'comments': comments, 'votes': votes},
    )


@staff_member_required
def moderation_reports(request):
    reports = Report.objects.select_related('topic', 'comment', 'reported_by').all()
    return render(request, 'debates/moderation_reports.html', {'reports': reports})


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
            messages.success(request, 'Report status updated.')
        else:
            messages.error(request, 'Invalid report status.')
    return redirect('moderation_reports')


def signup(request):
    if request.method == 'POST':
        form = CustomSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Your account has been created successfully.')
            return redirect('topic_list')
    else:
        form = CustomSignUpForm()
    return render(request, 'registration/signup.html', {'form': form})
