from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from debates.models import Bookmark, Comment, Profile, Reaction, Tag, Topic, Vote


class Command(BaseCommand):
    help = 'Seeds realistic, high quality debates and debater profiles'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE('Seeding database with rich debate topics and community activity...'))

        # 1. Create or get admin
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@debateplatform.local', 'is_staff': True, 'is_superuser': True}
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            Profile.objects.get_or_create(user=admin_user, defaults={'bio': 'Lead Moderator & Platform Administrator'})
            self.stdout.write(self.style.SUCCESS('Created admin user (admin / admin123)'))

        # 2. Seed vibrant demo users
        users_data = [
            {'username': 'elena_rostova', 'email': 'elena@example.com', 'bio': 'Tech ethicist and AI policy researcher at Oxford.'},
            {'username': 'marcus_vance', 'email': 'marcus@example.com', 'bio': 'Clean energy engineer & climate economics enthusiast.'},
            {'username': 'priya_sharma', 'email': 'priya@example.com', 'bio': 'Macroeconomist specializing in labor trends & welfare policy.'},
            {'username': 'david_kim', 'email': 'david@example.com', 'bio': 'Senior Software Architect. Remote-work advocate since 2018.'},
            {'username': 'sarah_connor', 'email': 'sarah@example.com', 'bio': 'Cybersecurity analyst & digital rights activist.'},
        ]

        users = {}
        for ud in users_data:
            u, _ = User.objects.get_or_create(
                username=ud['username'],
                defaults={'email': ud['email']}
            )
            u.set_password('password123')
            u.save()
            prof, _ = Profile.objects.get_or_create(user=u)
            prof.bio = ud['bio']
            prof.save()
            users[ud['username']] = u

        # 3. Tags
        tags_list = ['ai-ethics', 'future-of-work', 'clean-energy', 'economics', 'space', 'technology', 'governance', 'sports']
        tags = {}
        for t_name in tags_list:
            tag, _ = Tag.objects.get_or_create(name=t_name)
            tags[t_name] = tag

        # 4. Debates
        topics_data = [
            {
                'title': 'Should frontier Artificial General Intelligence (AGI) models require mandatory international oversight?',
                'description': 'As autonomous reasoning capabilities accelerate beyond human baselines in coding, mathematics, and agentic workflows, should training frontier models require binding global compliance treaties akin to the IAEA for nuclear materials, or would strict regulation stifle innovation and concentrate power in state-backed monopolies?',
                'category': 'technology',
                'created_by': users['elena_rostova'],
                'is_featured': True,
                'status': 'active',
                'tags': ['ai-ethics', 'technology', 'governance'],
                'comments': [
                    {
                        'user': users['sarah_connor'],
                        'stance': 'for',
                        'text': 'Without mandatory pre-deployment evaluations and strict compute-cluster tracking, catastrophic risks—from automated zero-day exploits to rogue agentic behaviors—cannot be mitigated retroactively. Proactive international governance is an absolute necessity.',
                        'reactions': [('insightful', users['elena_rostova']), ('well_argued', users['priya_sharma'])],
                        'replies': [
                            {
                                'user': users['david_kim'],
                                'stance': 'against',
                                'text': 'While safety is vital, global treaties with autocratic regimes will be ignored by adversaries while suffocating open-source innovation in democratic nations. Compute tracking leads directly to surveillance and monopoly cartelization.',
                                'reactions': [('like', users['marcus_vance'])]
                            }
                        ]
                    },
                    {
                        'user': users['marcus_vance'],
                        'stance': 'against',
                        'text': 'History shows that early over-regulation of foundational general-purpose technologies slows down positive externalities—like AI-accelerated drug discovery and materials science—more than it halts bad actors.',
                        'reactions': [('like', users['david_kim'])]
                    },
                    {
                        'user': users['priya_sharma'],
                        'stance': 'neutral',
                        'text': 'The middle ground might be an open auditing framework: require independent red-teaming and reproducible safety evaluations without imposing compute licensing bottlenecks on emerging startups.',
                        'reactions': [('insightful', users['elena_rostova']), ('like', users['sarah_connor'])]
                    }
                ],
                'votes': [
                    (users['elena_rostova'], 'for'),
                    (users['sarah_connor'], 'for'),
                    (users['priya_sharma'], 'for'),
                    (users['david_kim'], 'against'),
                    (users['marcus_vance'], 'against'),
                ]
            },
            {
                'title': 'Is Full Remote Work objectively superior to Mandatory Return-to-Office (RTO) policies?',
                'description': 'Debate on the long-term economic, psychological, and productivity impacts of distributed remote work versus co-located office mandates for knowledge workers. Does asynchronous remote work unlock higher output and global talent access, or does it erode spontaneous mentorship and corporate social cohesion?',
                'category': 'culture',
                'created_by': users['david_kim'],
                'is_featured': False,
                'status': 'active',
                'tags': ['future-of-work', 'culture'],
                'comments': [
                    {
                        'user': users['david_kim'],
                        'stance': 'for',
                        'text': 'Eliminating 2-hour daily commutes restores 500+ hours per year to employees, cuts carbon emissions, and allows companies to hire the top 0.1% worldwide instead of being confined to a 30-mile radius around expensive metropolitan hubs.',
                        'reactions': [('like', users['sarah_connor']), ('well_argued', users['marcus_vance'])]
                    },
                    {
                        'user': users['priya_sharma'],
                        'stance': 'against',
                        'text': 'Junior talent onboarding suffers immensely in 100% remote environments. The subtle osmosis of watching senior colleagues resolve escalations, pitch clients, and navigate negotiations cannot be replicated on Slack or asynchronous tickets.',
                        'reactions': [('insightful', users['elena_rostova'])]
                    }
                ],
                'votes': [
                    (users['david_kim'], 'for'),
                    (users['sarah_connor'], 'for'),
                    (users['marcus_vance'], 'for'),
                    (users['priya_sharma'], 'against'),
                ]
            },
            {
                'title': 'Next-generation Nuclear Power is indispensable for meeting Net-Zero carbon goals by 2050',
                'description': 'Can intermittent renewable sources (solar and wind) paired with battery storage realistically stabilize the global electrical grid alone, or are Small Modular Reactors (SMRs) and advanced nuclear fission crucial baseload partners?',
                'category': 'science',
                'created_by': users['marcus_vance'],
                'is_featured': True,
                'status': 'active',
                'tags': ['clean-energy', 'science'],
                'comments': [
                    {
                        'user': users['marcus_vance'],
                        'stance': 'for',
                        'text': 'Modern SMRs operate with passive cooling safety systems and minimal land footprint per gigawatt-hour compared to wind/solar farms. We cannot decarbonize high-temperature industrial heat and heavy steel manufacturing with wind turbines alone.',
                        'reactions': [('well_argued', users['david_kim']), ('insightful', users['elena_rostova'])]
                    },
                    {
                        'user': users['sarah_connor'],
                        'stance': 'against',
                        'text': 'Capital expenditure and multi-decade construction delays make conventional nuclear too slow. Capital invested today in utility-scale solar and long-duration iron-air batteries delivers 4x faster carbon abatement per dollar spent.',
                        'reactions': [('like', users['priya_sharma'])]
                    }
                ],
                'votes': [
                    (users['marcus_vance'], 'for'),
                    (users['elena_rostova'], 'for'),
                    (users['david_kim'], 'for'),
                    (users['sarah_connor'], 'against'),
                ]
            },
            {
                'title': 'Universal Basic Income (UBI) should replace complex fragmented welfare programs',
                'description': 'With automation and machine learning reshaping workforce composition, is an unconditional direct cash floor the most humane and economically efficient framework, or would it trigger hyperinflation and fiscal insolvency?',
                'category': 'politics',
                'created_by': users['priya_sharma'],
                'is_featured': False,
                'status': 'active',
                'tags': ['economics', 'governance'],
                'comments': [
                    {
                        'user': users['priya_sharma'],
                        'stance': 'for',
                        'text': 'Traditional means-tested welfare creates punishing effective marginal tax rates and traps recipients in poverty bureaucracies. Direct unconditional cash restores dignity, eliminates administrative overhead, and empowers local economies.',
                        'reactions': [('well_argued', users['david_kim'])]
                    }
                ],
                'votes': [
                    (users['priya_sharma'], 'for'),
                    (users['elena_rostova'], 'for'),
                    (users['marcus_vance'], 'against'),
                ]
            }
        ]

        for td in topics_data:
            topic, _ = Topic.objects.get_or_create(
                title=td['title'],
                defaults={
                    'description': td['description'],
                    'category': td['category'],
                    'created_by': td['created_by'],
                    'is_featured': td.get('is_featured', False),
                    'status': td.get('status', 'active'),
                    'views_count': 142,
                }
            )
            # Assign tags
            t_objs = [tags[name] for name in td.get('tags', []) if name in tags]
            topic.tags.set(t_objs)

            # Comments
            for c_data in td.get('comments', []):
                cmt, _ = Comment.objects.get_or_create(
                    topic=topic,
                    user=c_data['user'],
                    text=c_data['text'],
                    defaults={'stance': c_data.get('stance', 'neutral')}
                )
                for rx_emoji, rx_user in c_data.get('reactions', []):
                    Reaction.objects.get_or_create(user=rx_user, comment=cmt, emoji=rx_emoji)

                for r_data in c_data.get('replies', []):
                    reply, _ = Comment.objects.get_or_create(
                        topic=topic,
                        user=r_data['user'],
                        parent=cmt,
                        text=r_data['text'],
                        defaults={'stance': r_data.get('stance', 'neutral')}
                    )
                    for rx_emoji, rx_user in r_data.get('reactions', []):
                        Reaction.objects.get_or_create(user=rx_user, comment=reply, emoji=rx_emoji)

            # Votes
            for v_user, v_choice in td.get('votes', []):
                Vote.objects.update_or_create(
                    topic=topic,
                    user=v_user,
                    defaults={'choice': v_choice}
                )

            # Bookmarks
            Bookmark.objects.get_or_create(user=users['elena_rostova'], topic=topic)

        self.stdout.write(self.style.SUCCESS('Successfully seeded rich debate platform data!'))
