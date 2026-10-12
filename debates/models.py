from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Topic(models.Model):
    CATEGORY_CHOICES = [
        ('politics', 'Politics'),
        ('technology', 'Technology'),
        ('culture', 'Culture'),
        ('sports', 'Sports'),
        ('science', 'Science'),
        ('general', 'General'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('concluded', 'Concluded'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='general')
    tags = models.ManyToManyField(Tag, related_name='topics', blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='topics')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_featured = models.BooleanField(default=False)
    views_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def comment_count(self):
        return self.comments.count()

    @property
    def for_votes(self):
        return self.votes.filter(choice='for').count()

    @property
    def against_votes(self):
        return self.votes.filter(choice='against').count()

    @property
    def total_votes(self):
        return self.votes.count()

    @property
    def for_percentage(self):
        total = self.total_votes
        return round((self.for_votes / total) * 100, 1) if total > 0 else 50.0

    @property
    def against_percentage(self):
        total = self.total_votes
        return round((self.against_votes / total) * 100, 1) if total > 0 else 50.0


class Comment(models.Model):
    STANCE_CHOICES = [
        ('for', 'In Favor (Pro)'),
        ('against', 'Against (Con)'),
        ('neutral', 'Neutral / Discussion'),
    ]

    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    stance = models.CharField(max_length=10, choices=STANCE_CHOICES, default='neutral')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.user.username}: {self.text[:60]}'

    @property
    def reaction_counts(self):
        counts = {emoji: 0 for emoji, _ in Reaction.EMOJI_CHOICES}
        for reaction in self.reactions.all():
            counts[reaction.emoji] = counts.get(reaction.emoji, 0) + 1
        return counts

    @property
    def reaction_totals(self):
        return self.reaction_counts


class Reaction(models.Model):
    EMOJI_CHOICES = [
        ('like', 'Like 👍'),
        ('dislike', 'Dislike 👎'),
        ('insightful', 'Insightful 💡'),
        ('well_argued', 'Well Argued 🎯'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reactions')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='reactions')
    emoji = models.CharField(max_length=20, choices=EMOJI_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'comment'], name='unique_reaction_per_user_per_comment')
        ]

    def __str__(self):
        return f'{self.user.username} reacted {self.emoji} on comment {self.comment_id}'


class Vote(models.Model):
    CHOICE_CHOICES = [
        ('for', 'For'),
        ('against', 'Against'),
    ]

    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='votes')
    choice = models.CharField(max_length=10, choices=CHOICE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['topic', 'user'], name='unique_vote_per_topic_per_user')
        ]

    def __str__(self):
        return f'{self.user.username} voted {self.choice} on {self.topic.title}'


class Bookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='bookmarks')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['user', 'topic'], name='unique_bookmark_per_user_per_topic')
        ]

    def __str__(self):
        return f'{self.user.username} bookmarked {self.topic.title}'


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    is_suspended = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    @property
    def avatar_url(self):
        if self.avatar and hasattr(self.avatar, 'url'):
            try:
                return self.avatar.url
            except Exception:
                pass
        return f"https://ui-avatars.com/api/?name={self.user.username}&background=0d6efd&color=fff&bold=true"

    @property
    def reputation_score(self):
        # 15 pts per topic, 5 pts per comment, 2 pts per vote cast, 4 pts per reaction received on comments
        topic_pts = self.user.topics.count() * 15
        comment_pts = self.user.comments.count() * 5
        vote_pts = self.user.votes.count() * 2
        reaction_pts = Reaction.objects.filter(comment__user=self.user).count() * 4
        return topic_pts + comment_pts + vote_pts + reaction_pts

    @property
    def rank_badge(self):
        score = self.reputation_score
        if score >= 100:
            return {'title': 'Grand Debater', 'class': 'badge-grand', 'icon': 'fa-crown'}
        elif score >= 50:
            return {'title': 'Master of Logic', 'class': 'badge-master', 'icon': 'fa-award'}
        elif score >= 20:
            return {'title': 'Active Contributor', 'class': 'badge-contributor', 'icon': 'fa-fire'}
        return {'title': 'Novice Debater', 'class': 'badge-novice', 'icon': 'fa-seedling'}


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.message


class Report(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('dismissed', 'Dismissed'),
    ]

    topic = models.ForeignKey(Topic, null=True, blank=True, on_delete=models.CASCADE, related_name='reports')
    comment = models.ForeignKey(Comment, null=True, blank=True, on_delete=models.CASCADE, related_name='reports')
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def clean(self):
        if not self.topic and not self.comment:
            raise ValidationError('A report must target either a topic or a comment.')
        if self.topic and self.comment:
            raise ValidationError('A report may only target one item at a time.')

    def __str__(self):
        target = self.topic.title if self.topic else self.comment.text[:50]
        return f'{target} - {self.status}'
