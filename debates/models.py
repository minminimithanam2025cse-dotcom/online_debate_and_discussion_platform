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

    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='general')
    tags = models.ManyToManyField(Tag, related_name='topics', blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='topics')
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


class Comment(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
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
        ('like', 'Like'),
        ('dislike', 'Dislike'),
        ('insightful', 'Insightful'),
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


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    is_suspended = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


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
