# ⚡ DebateSphere (v2.0) — Structured Civil Discourse Platform

A modern, production-ready, full-stack web application built with **Django 5.2**, **Bootstrap 5.3**, and **modern JavaScript Fetch API**. DebateSphere transforms online discussions into balanced, structured, and evidence-driven intellectual arenas.

---

## 🌟 Key Features & Highlights

### 1. 🏛️ Interactive Debate Arena & Live Stance Bar
- **Real-Time Split Stance Visualization:** Dynamic visual breakdown comparing **In Favor (PRO)** vs. **Against (CON)** perspectives.
- **Zero-Reload Live AJAX Voting:** Cast or toggle your vote with instant progress bar animations and live count updates without refreshing the page.

### 2. 💬 Structured Argumentation by Stance
- **Declared Argument Stances:** Debaters declare their stance—**In Favor**, **Against (Rebuttal)**, or **Neutral (Inquiry)**—when contributing.
- **Perspective Filtering:** Filter debate threads by stance to analyze both sides of complex dilemmas objectively.
- **Interactive Reactions:** Live reactions (👍 Like, 👎 Disagree, 💡 Insightful, 🎯 Well Argued) with instant counter updates.
- **Collapsible Nested Rebuttals:** Clean threaded replies tree with inline response boxes.

### 3. 🎨 World-Class Modern UI / UX Design
- **Dark Mode & Light Mode:** Seamless theme toggle with smooth transitions and persistent `localStorage` support.
- **Typography & Aesthetics:** Powered by **Plus Jakarta Sans** and **Inter** with **FontAwesome 6** iconography and subtle glassmorphic elevation.
- **Quick Keyboard Shortcut:** Press `/` anywhere to immediately focus the debate search bar.
- **Share & Bookmark:** 1-click clipboard link sharing and instant AJAX topic bookmarking.

### 4. 🏆 Reputation System & Debater Leaderboard
- **Community Points Engine:** Earn reputation for initiating approved debate motions (+15 pts), posting arguments (+5 pts), receiving insightful reactions (+4 pts), and casting verified votes (+2 pts).
- **Gamified Rank Titles:** Progress from *Novice Debater* ➔ *Active Contributor* ➔ *Master of Logic* ➔ *Grand Debater*.
- **Hall of Discourse (Leaderboard):** Real-time rankings page celebrating the community's top intellectual contributors.

### 5. 🛡️ Moderation & Community Safety
- **Report System:** Flag inappropriate debate motions or comments for review with descriptive audit reasons.
- **Moderator Dashboard:** Dedicated `/moderation/reports/` portal for staff to audit pending reports, leave notes, and suspend disruptive accounts.
- **Account Suspension Guard:** Suspended accounts are immediately restricted from voting or creating new content.

### 6. 🔔 Real-Time Notifications
- Activity alerts when another debater votes on your topic, replies to your argument, or reacts to your points.
- Instant navbar notification preview dropdown with "Mark all as read" capability.

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10+ (Recommended Python 3.12 or 3.14)
- Virtual Environment (`.venv`)

### 1. Activate Virtual Environment
```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

### 2. Apply Migrations
```bash
python manage.py migrate
```

### 3. Seed Realistic Demo Debates & Profiles
Populate the platform with high-quality debates on AI ethics, remote work, clean energy, and welfare economics:
```bash
python manage.py seed_debates
```

### 4. Run the Development Server
```bash
python manage.py runserver
```
Visit **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)** in your browser!

---

## 🔐 Demo Accounts

| Username | Password | Role | Description |
| :--- | :--- | :--- | :--- |
| `admin` | `admin123` | **Superuser / Staff** | Moderator Desk & Full Administrative Access |
| `elena_rostova` | `password123` | Active Debater | AI Ethicist & Policy Researcher |
| `david_kim` | `password123` | Active Debater | Remote Work Advocate & Software Architect |
| `marcus_vance` | `password123` | Active Debater | Clean Energy Engineer |
| `priya_sharma` | `password123` | Active Debater | Macroeconomist |

*You can also click **Join Debate** anytime on the navbar to create a brand new account!*

---

## 🧪 Automated Test Suite

A complete test suite is included in `debates/tests.py` verifying voting flows, AJAX endpoints, comment stances, reactions, bookmarks, moderation permissions, and leaderboards:

```bash
python manage.py test
```
*All 9 test cases pass with 100% success.*

---

## 📂 Project Architecture

```
debate-platform-v2/
├── debate_platform/         # Django project settings & URL routing
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── debates/                 # Core debates application
│   ├── management/commands/ # Seed command (seed_debates.py)
│   ├── templatetags/        # Custom template filters (initials, get_item)
│   ├── forms.py             # Topic, Comment, Report, Profile, Signup forms
│   ├── models.py            # Topic, Comment, Vote, Reaction, Bookmark, Profile
│   ├── tests.py             # 9 Comprehensive unit & integration tests
│   ├── urls.py              # Debate app URL routing
│   └── views.py             # Controller views & AJAX endpoints
├── static/
│   ├── css/styles.css       # Complete design system & dark mode variables
│   └── js/main.js           # AJAX voting, reactions, bookmarks & theme switcher
├── templates/
│   ├── base.html            # Master layout with navigation & notification drawer
│   ├── 404.html & 500.html  # Custom styled error pages
│   ├── debates/
│   │   ├── topic_list.html  # Arena feed with hero, categories & trending
│   │   ├── topic_detail.html# Live voting bar, stance filter & argument stream
│   │   ├── topic_form.html  # Debate motion submission
│   │   ├── comment_form.html# Argument editor
│   │   ├── profile.html     # User reputation, badges & activity tabs
│   │   ├── leaderboard.html # Hall of Discourse rankings
│   │   ├── notifications.html
│   │   └── moderation_reports.html
│   └── registration/
│       ├── login.html
│       └── signup.html
└── requirements.txt
```
