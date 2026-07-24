from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import Comment, Profile, Report, Tag, Topic


class TopicForm(forms.ModelForm):
    tags_input = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Add tags, comma-separated'}))

    class Meta:
        model = Topic
        fields = ['title', 'description', 'category', 'tags_input']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Topic title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Describe the debate topic...'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_title(self):
        title = self.cleaned_data['title'].strip()
        if not title:
            raise ValidationError('Title cannot be empty.')
        return title

    def clean_description(self):
        description = self.cleaned_data['description'].strip()
        if not description:
            raise ValidationError('Description cannot be empty.')
        return description

    def clean_tags_input(self):
        raw_tags = self.cleaned_data.get('tags_input', '')
        cleaned = []
        if raw_tags:
            for tag in raw_tags.split(','):
                name = tag.strip().lower()
                if name:
                    cleaned.append(name)
        return cleaned

    def save(self, commit=True):
        topic = super().save(commit=False)
        if commit:
            topic.save()
            self.save_m2m()

        tag_names = self.cleaned_data.get('tags_input', [])
        if tag_names:
            tag_objects = []
            for name in tag_names:
                tag, _ = Tag.objects.get_or_create(name=name)
                tag_objects.append(tag)
            topic.tags.set(tag_objects)

        if commit:
            topic.save()
        return topic


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Write your comment...'}),
        }

    def clean_text(self):
        text = self.cleaned_data['text'].strip()
        if not text:
            raise ValidationError('Comment text cannot be empty.')
        return text


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['reason']
        widgets = {
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Please describe the issue.'}),
        }

    def clean_reason(self):
        reason = self.cleaned_data['reason'].strip()
        if not reason:
            raise ValidationError('A reason is required for the report.')
        return reason


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'avatar']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Tell the community a little about yourself.'}),
            'avatar': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class CustomSignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
        }

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('A user with that email already exists.')
        return email
