/**
 * DEBATESPHERE - INTERACTIVE CLIENT JAVASCRIPT
 * Handles Dark/Light Mode, Live Voting AJAX, Emoji Reactions, Bookmarking, and UI enhancements.
 */

document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initVoting();
    initReactions();
    initBookmarks();
    initReplyToggles();
    initShareButtons();
    initSearchShortcut();
});

// ==========================================
// THEME SWITCHER (Dark / Light Mode)
// ==========================================
function initTheme() {
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    const htmlElement = document.documentElement;

    // Check saved preference or system preference
    const savedTheme = localStorage.getItem('debatesphere_theme');
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    const initialTheme = savedTheme || (prefersDark ? 'dark' : 'light');

    setTheme(initialTheme);

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            const currentTheme = htmlElement.getAttribute('data-bs-theme') || 'light';
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            setTheme(newTheme);
            localStorage.setItem('debatesphere_theme', newTheme);
            showToast(`Switched to ${newTheme} mode`, 'info');
        });
    }

    function setTheme(theme) {
        htmlElement.setAttribute('data-bs-theme', theme);
        if (theme === 'dark') {
            document.body.classList.add('dark-mode');
            if (themeToggleBtn) {
                themeToggleBtn.innerHTML = '<i class="fa-solid fa-sun text-warning"></i>';
                themeToggleBtn.setAttribute('title', 'Switch to Light Mode');
            }
        } else {
            document.body.classList.remove('dark-mode');
            if (themeToggleBtn) {
                themeToggleBtn.innerHTML = '<i class="fa-solid fa-moon text-secondary"></i>';
                themeToggleBtn.setAttribute('title', 'Switch to Dark Mode');
            }
        }
    }
}

// ==========================================
// CSRF TOKEN HELPER
// ==========================================
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// ==========================================
// LIVE AJAX VOTING
// ==========================================
function initVoting() {
    const voteForm = document.getElementById('debate-vote-form');
    if (!voteForm) return;

    voteForm.addEventListener('submit', async (e) => {
        // Find which button was clicked
        const submitter = e.submitter;
        if (!submitter || !submitter.name || submitter.name !== 'choice') return;

        e.preventDefault();
        const choice = submitter.value;
        const url = voteForm.getAttribute('action');
        const csrfToken = voteForm.querySelector('[name=csrfmiddlewaretoken]').value || getCookie('csrftoken');

        try {
            submitter.disabled = true;
            const originalHtml = submitter.innerHTML;
            submitter.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';

            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrfToken
                },
                body: new URLSearchParams({
                    choice: choice,
                    csrfmiddlewaretoken: csrfToken
                })
            });

            submitter.innerHTML = originalHtml;
            submitter.disabled = false;

            if (response.status === 403) {
                showToast('Please log in to cast your vote!', 'warning');
                return;
            }

            const data = await response.json();
            if (data.status === 'ok') {
                // Update live progress bar
                const barFor = document.getElementById('vote-bar-for');
                const barAgainst = document.getElementById('vote-bar-against');
                const countFor = document.getElementById('vote-count-for');
                const countAgainst = document.getElementById('vote-count-against');
                const totalVotes = document.getElementById('vote-total-count');
                const userVoteBanner = document.getElementById('user-current-vote-banner');

                if (barFor) {
                    barFor.style.width = `${data.for_percent}%`;
                    barFor.textContent = `${data.for_percent}% For`;
                }
                if (barAgainst) {
                    barAgainst.style.width = `${data.against_percent}%`;
                    barAgainst.textContent = `${data.against_percent}% Against`;
                }
                if (countFor) countFor.textContent = data.for_votes;
                if (countAgainst) countAgainst.textContent = data.against_votes;
                if (totalVotes) totalVotes.textContent = `${data.total_votes} total votes cast`;

                // Update vote button active styling
                document.querySelectorAll('.btn-vote-choice').forEach(btn => btn.classList.remove('active'));
                submitter.classList.add('active');

                if (userVoteBanner) {
                    userVoteBanner.innerHTML = `<span class="badge ${choice === 'for' ? 'bg-success' : 'bg-danger'} px-3 py-2">You voted: ${choice.toUpperCase()}</span>`;
                }

                showToast(data.message || 'Vote recorded successfully!', 'success');
            } else {
                showToast(data.message || 'Error recording vote.', 'error');
            }
        } catch (err) {
            console.error('Vote error:', err);
            // Fallback standard submit
            voteForm.submit();
        }
    });
}

// ==========================================
// LIVE AJAX COMMENT REACTIONS
// ==========================================
function initReactions() {
    document.querySelectorAll('.reaction-form-ajax').forEach(form => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const url = form.getAttribute('action');
            const commentId = form.querySelector('[name=comment_id]') ? form.querySelector('[name=comment_id]').value : null;
            const emoji = form.querySelector('[name=reaction]').value;
            const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]').value || getCookie('csrftoken');
            const submitBtn = form.querySelector('button[type=submit]');

            try {
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': csrfToken
                    },
                    body: new URLSearchParams({
                        reaction: emoji,
                        comment_id: commentId || '',
                        csrfmiddlewaretoken: csrfToken
                    })
                });

                if (response.status === 403) {
                    showToast('Please log in to react to arguments.', 'warning');
                    return;
                }

                const data = await response.json();
                if (data.status === 'ok') {
                    // Update count on all reactions for this comment
                    const commentCard = form.closest('.argument-card, .reply-card');
                    if (commentCard && data.counts) {
                        for (const [key, val] of Object.entries(data.counts)) {
                            const countSpan = commentCard.querySelector(`.reaction-count-${key}`);
                            if (countSpan) countSpan.textContent = val;
                        }
                    }

                    // Toggle active class
                    if (data.active_emoji === emoji) {
                        submitBtn.classList.add('active');
                    } else {
                        submitBtn.classList.remove('active');
                    }
                    showToast(data.message, 'info');
                }
            } catch (err) {
                console.error('Reaction error:', err);
                form.submit();
            }
        });
    });
}

// ==========================================
// LIVE AJAX BOOKMARKS
// ==========================================
function initBookmarks() {
    document.querySelectorAll('.bookmark-btn-ajax').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            const url = btn.getAttribute('data-url');
            const csrfToken = getCookie('csrftoken');

            try {
                btn.disabled = true;
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': csrfToken
                    }
                });

                btn.disabled = false;
                if (response.status === 403) {
                    showToast('Please log in to bookmark debates.', 'warning');
                    return;
                }

                const data = await response.json();
                if (data.status === 'ok') {
                    const icon = btn.querySelector('i');
                    if (data.bookmarked) {
                        if (icon) icon.className = 'fa-solid fa-bookmark text-primary';
                        btn.classList.add('active');
                    } else {
                        if (icon) icon.className = 'fa-regular fa-bookmark text-muted';
                        btn.classList.remove('active');
                    }
                    showToast(data.message, 'success');
                }
            } catch (err) {
                console.error('Bookmark error:', err);
                window.location.href = url;
            }
        });
    });
}

// ==========================================
// INLINE REPLY BOX TOGGLING
// ==========================================
function initReplyToggles() {
    document.querySelectorAll('.btn-toggle-reply').forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-target');
            const formContainer = document.getElementById(targetId);
            if (formContainer) {
                const isHidden = formContainer.classList.contains('d-none');
                if (isHidden) {
                    formContainer.classList.remove('d-none');
                    const textarea = formContainer.querySelector('textarea');
                    if (textarea) textarea.focus();
                } else {
                    formContainer.classList.add('d-none');
                }
            }
        });
    });
}

// ==========================================
// SHARE / COPY LINK
// ==========================================
function initShareButtons() {
    document.querySelectorAll('.btn-share-debate').forEach(btn => {
        btn.addEventListener('click', () => {
            const url = window.location.href;
            if (navigator.clipboard) {
                navigator.clipboard.writeText(url).then(() => {
                    showToast('Debate link copied to clipboard! 📋', 'success');
                }).catch(() => {
                    copyFallback(url);
                });
            } else {
                copyFallback(url);
            }
        });
    });

    function copyFallback(text) {
        const temp = document.createElement('input');
        temp.value = text;
        document.body.appendChild(temp);
        temp.select();
        document.execCommand('copy');
        document.body.removeChild(temp);
        showToast('Link copied to clipboard! 📋', 'success');
    }
}

// ==========================================
// SEARCH SHORTCUT (Press "/" to focus search)
// ==========================================
function initSearchShortcut() {
    window.addEventListener('keydown', (e) => {
        if (e.key === '/' && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA') {
            e.preventDefault();
            const searchInput = document.querySelector('input[name=q]');
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
            }
        }
    });
}

// ==========================================
// TOAST NOTIFICATION GENERATOR
// ==========================================
function showToast(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = 'debate-toast';

    let icon = '<i class="fa-solid fa-circle-info text-primary"></i>';
    if (type === 'success') icon = '<i class="fa-solid fa-circle-check text-success"></i>';
    if (type === 'warning') icon = '<i class="fa-solid fa-triangle-exclamation text-warning"></i>';
    if (type === 'error') icon = '<i class="fa-solid fa-circle-exclamation text-danger"></i>';

    toast.innerHTML = `
        ${icon}
        <span class="flex-grow-1 small fw-medium">${message}</span>
        <button type="button" class="btn-close btn-close-white ms-2" style="font-size: 0.65rem;" onclick="this.parentElement.remove()"></button>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        toast.style.transform = 'translateY(10px)';
        setTimeout(() => toast.remove(), 300);
    }, 3800);
}
