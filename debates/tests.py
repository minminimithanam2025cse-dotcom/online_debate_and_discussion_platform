from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from debates.models import Bookmark, Comment, Notification, Profile, Reaction, Report, Tag, Topic, Vote


class DebatePlatformTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='debater_one', password='password123', email='one@example.com')
        self.user2 = User.objects.create_user(username='debater_two', password='password123', email='two@example.com')
        self.admin = User.objects.create_superuser(username='admin_mod', password='password123', email='mod@example.com')

        self.tag_ai = Tag.objects.create(name='artificial-intelligence')
        self.topic = Topic.objects.create(
            title='AI will benefit humanity more than harm it',
            description='A balanced exploration of technological advancement and human flourishing.',
            category='technology',
            created_by=self.user1,
            is_featured=True,
        )
        self.topic.tags.add(self.tag_ai)

    def test_topic_list_renders_and_filters(self):
        response = self.client.get(reverse('topic_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'AI will benefit humanity')

        # Filter by category
        cat_resp = self.client.get(reverse('topic_list') + '?category=technology')
        self.assertEqual(cat_resp.status_code, 200)
        self.assertContains(cat_resp, 'AI will benefit humanity')

        # Search query
        search_resp = self.client.get(reverse('topic_list') + '?q=humanity')
        self.assertEqual(search_resp.status_code, 200)
        self.assertContains(search_resp, 'AI will benefit humanity')

        # Empty search result
        empty_resp = self.client.get(reverse('topic_list') + '?q=nonexistentxyz')
        self.assertEqual(empty_resp.status_code, 200)
        self.assertContains(empty_resp, 'No debates found')

    def test_topic_creation(self):
        self.client.login(username='debater_one', password='password123')
        response = self.client.post(reverse('topic_create'), {
            'title': 'Remote work increases productivity',
            'description': 'Debating distributed workforce models.',
            'category': 'culture',
            'tags_input': 'work, culture',
        })
        self.assertEqual(response.status_code, 302)
        new_topic = Topic.objects.get(title='Remote work increases productivity')
        self.assertEqual(new_topic.category, 'culture')
        self.assertEqual(new_topic.created_by, self.user1)
        self.assertTrue(new_topic.tags.filter(name='work').exists())

    def test_voting_flow_and_ajax(self):
        self.client.login(username='debater_two', password='password123')

        # Regular POST
        response = self.client.post(reverse('topic_vote', args=[self.topic.pk]), {'choice': 'for'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.topic.for_votes, 1)
        self.assertEqual(self.topic.against_votes, 0)

        # Change vote via AJAX
        ajax_resp = self.client.post(
            reverse('topic_vote', args=[self.topic.pk]),
            {'choice': 'against'},
            headers={'x-requested-with': 'XMLHttpRequest', 'Accept': 'application/json'}
        )
        self.assertEqual(ajax_resp.status_code, 200)
        data = ajax_resp.json()
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['choice'], 'against')
        self.assertEqual(self.topic.for_votes, 0)
        self.assertEqual(self.topic.against_votes, 1)

    def test_comment_with_stance_and_reply(self):
        self.client.login(username='debater_two', password='password123')

        # Post an argument In Favor
        response = self.client.post(reverse('topic_detail', args=[self.topic.pk]), {
            'text': 'AI automation lowers healthcare diagnostics costs.',
            'stance': 'for',
        })
        self.assertEqual(response.status_code, 302)
        comment = Comment.objects.get(topic=self.topic, parent__isnull=True)
        self.assertEqual(comment.stance, 'for')
        self.assertEqual(comment.user, self.user2)

        # Post reply as rebuttal (against)
        self.client.login(username='debater_one', password='password123')
        reply_resp = self.client.post(reverse('topic_detail', args=[self.topic.pk]), {
            'text': 'Diagnostic models still carry distribution shift risks without human audits.',
            'stance': 'against',
            'parent_id': comment.pk,
        })
        self.assertEqual(reply_resp.status_code, 302)
        self.assertEqual(comment.replies.count(), 1)
        self.assertEqual(comment.replies.first().stance, 'against')

    def test_comment_reaction_ajax(self):
        comment = Comment.objects.create(
            topic=self.topic,
            user=self.user1,
            text='Thoughtful argument on safety protocols.',
            stance='for',
        )
        self.client.login(username='debater_two', password='password123')

        # Add insightful reaction
        response = self.client.post(
            reverse('comment_react', args=[comment.pk]),
            {'reaction': 'insightful'},
            headers={'x-requested-with': 'XMLHttpRequest'}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['active_emoji'], 'insightful')
        self.assertEqual(comment.reaction_counts['insightful'], 1)

        # Toggle reaction off
        toggle_resp = self.client.post(
            reverse('comment_react', args=[comment.pk]),
            {'reaction': 'insightful'},
            headers={'x-requested-with': 'XMLHttpRequest'}
        )
        self.assertEqual(toggle_resp.status_code, 200)
        data2 = toggle_resp.json()
        self.assertIsNone(data2['active_emoji'])
        self.assertEqual(comment.reaction_counts['insightful'], 0)

    def test_topic_bookmark_toggle(self):
        self.client.login(username='debater_one', password='password123')
        response = self.client.post(
            reverse('topic_bookmark', args=[self.topic.pk]),
            headers={'x-requested-with': 'XMLHttpRequest'}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['bookmarked'])
        self.assertTrue(Bookmark.objects.filter(user=self.user1, topic=self.topic).exists())

        # Toggle off
        response_off = self.client.post(
            reverse('topic_bookmark', args=[self.topic.pk]),
            headers={'x-requested-with': 'XMLHttpRequest'}
        )
        self.assertFalse(response_off.json()['bookmarked'])
        self.assertFalse(Bookmark.objects.filter(user=self.user1, topic=self.topic).exists())

    def test_user_reputation_and_leaderboard(self):
        profile = Profile.objects.get_or_create(user=self.user1)[0]
        # user1 has 1 topic (15pts), + 0 comments, + 0 votes
        self.assertGreaterEqual(profile.reputation_score, 15)

        response = self.client.get(reverse('leaderboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'debater_one')
        self.assertContains(response, 'HALL OF DISCOURSE')

    def test_suspended_user_restrictions(self):
        profile = Profile.objects.get_or_create(user=self.user2)[0]
        profile.is_suspended = True
        profile.save()

        self.client.login(username='debater_two', password='password123')

        # Attempt to create topic
        resp = self.client.post(reverse('topic_create'), {
            'title': 'Test title',
            'description': 'Test desc',
            'category': 'technology',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Topic.objects.filter(title='Test title').exists())

        # Attempt to vote
        vote_resp = self.client.post(reverse('topic_vote', args=[self.topic.pk]), {'choice': 'for'})
        self.assertEqual(vote_resp.status_code, 302)
        self.assertEqual(self.topic.total_votes, 0)

    def test_moderation_dashboard_and_report(self):
        # User 2 reports topic
        self.client.login(username='debater_two', password='password123')
        report_resp = self.client.post(reverse('report_topic', args=[self.topic.pk]), {
            'reason': 'Needs citation verification.',
        })
        self.assertEqual(report_resp.status_code, 302)
        report = Report.objects.get(topic=self.topic)
        self.assertEqual(report.reported_by, self.user2)

        # Admin views dashboard
        self.client.login(username='admin_mod', password='password123')
        dash_resp = self.client.get(reverse('moderation_reports'))
        self.assertEqual(dash_resp.status_code, 200)
        self.assertContains(dash_resp, 'Needs citation verification')

        # Admin resolves report
        resolve_resp = self.client.post(reverse('resolve_report', args=[report.pk]), {
            'status': 'reviewed',
            'admin_note': 'Verified legitimate discussion topic.',
        })
        self.assertEqual(resolve_resp.status_code, 302)
        report.refresh_from_db()
        self.assertEqual(report.status, 'reviewed')
        self.assertEqual(report.admin_note, 'Verified legitimate discussion topic.')
