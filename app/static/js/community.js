let myLibrary = [];
let selectedBook = null;
let userList = [];
let selectedUser = null;
let currentUsername = null;
let feedPage = 1;
let feedPages = 1;

// Fuzzy match helper
function fuzzyMatch(str, query) {
    str = str.toLowerCase();
    query = query.toLowerCase();
    if (str.includes(query)) return true;
    let i = 0;
    for (let c of str) {
        if (c === query[i]) i++;
        if (i === query.length) return true;
    }
    return false;
}

// Book autocomplete rendering
function renderBookSuggestions(matches) {
    const suggestions = document.getElementById('bookSuggestions');
    if (!suggestions) return;

    suggestions.innerHTML = '';
    if (!matches.length) {
        suggestions.style.display = 'none';
        return;
    }
    matches.forEach((book, idx) => {
        const item = document.createElement('div');
        item.className = 'autocomplete-item' + (idx === 0 ? ' active' : '');
        item.innerHTML = `
            <img src="${book.cover_url || 'https://via.placeholder.com/40x60?text=No+Cover'}" alt="">
            <div>
                <div style="font-weight:600;">${book.title}</div>
                <div style="font-size:0.97em;color:var(--bs-primary,#0d6efd);">${book.author}</div>
            </div>
        `;
        item.onmousedown = e => e.preventDefault();
        item.onclick = () => {
            const input = document.getElementById('bookSearchInput');
            const statusDisplay = document.getElementById('statusDisplay');
            if (!input || !statusDisplay) return;
            input.value = book.title;
            suggestions.style.display = 'none';
            selectedBook = book;
            statusDisplay.textContent = book.status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
            statusDisplay.className = "fw-semibold text-primary";
        };
        suggestions.appendChild(item);
    });
    suggestions.style.display = 'block';
}

// User autocomplete rendering
function renderUserSuggestions(matches) {
    const suggestions = document.getElementById('userSuggestions');
    if (!suggestions) return;

    suggestions.innerHTML = '';
    if (!matches.length) {
        suggestions.style.display = 'none';
        return;
    }
    matches.forEach((username, idx) => {
        const item = document.createElement('div');
        item.className = 'autocomplete-item' + (idx === 0 ? ' active' : '');
        item.innerHTML = `<span style="font-weight:600;">${username}</span>`;
        item.onmousedown = e => e.preventDefault();
        item.onclick = () => {
            const input = document.getElementById('userSearchInput');
            if (!input) return;
            input.value = username;
            selectedUser = username;
            suggestions.style.display = 'none';
            suggestions.innerHTML = '';
            input.focus();
        };
        suggestions.appendChild(item);
    });
    suggestions.style.display = 'block';
}

function renderFeed(feed, page, pages) {
    const feedList = document.getElementById('feedList');
    const feedPagination = document.getElementById('feedPagination');
    if (!feedList || !feedPagination) return;

    if (!feed.length) {
        feedList.innerHTML = '<div class="text-muted">No shares yet. Start sharing books with friends!</div>';
        feedPagination.innerHTML = '';
        return;
    }
    feedList.innerHTML = '';
    feed.forEach(item => {
        const div = document.createElement('div');
        div.className = 'feed-item';

        let message = "";
        if (currentUsername && item.from_username === currentUsername) {
            message = `You shared <b>${item.title}</b> with <b>${item.to_username}</b> on <span>${item.timestamp}</span>`;
        } else if (currentUsername && item.to_username === currentUsername) {
            message = `<b>${item.from_username}</b> shared <b>${item.title}</b> with you on <span>${item.timestamp}</span>`;
        } else {
            message = `<b>${item.from_username}</b> shared <b>${item.title}</b> with <b>${item.to_username}</b> on <span>${item.timestamp}</span>`;
        }
        const detailsUrl = `/details?googleid=${item.google_id}`;
        div.onclick = () => window.location.href = detailsUrl;
        div.style.cursor = 'pointer';
        div.innerHTML = `
            <img class="feed-book-cover" src="${item.cover_url || 'https://via.placeholder.com/70x100?text=No+Cover'}" alt="Book cover">
            <div class="feed-book-info">
                <div class="feed-book-title">${item.title}</div>
                <div class="feed-book-status">Status: <span class="badge bg-secondary">${item.status.replace('_', ' ')}</span></div>
                <div class="feed-meta">${message}</div>
            </div>
        `;
        feedList.appendChild(div);
    });

    // Pagination UI
    feedPagination.innerHTML = '';
    if (pages > 1) {
        for (let i = 1; i <= pages; i++) {
            const btn = document.createElement('button');
            btn.textContent = i;
            btn.className = (i === page) ? 'active' : '';
            btn.onclick = () => {
                loadFeed(i);
                feedPage = i;
            };
            feedPagination.appendChild(btn);
        }
    }
}

function showCommunityLoadingBar() {
    document.getElementById('communityLoadingBar').style.display = 'block';
    document.getElementById('feedList').style.display = 'none';
}

function hideCommunityLoadingBar() {
    document.getElementById('communityLoadingBar').style.display = 'none';
    document.getElementById('feedList').style.display = 'flex';
}

function loadFeed(page = 1) {
    const feedList = document.getElementById('feedList');
    const feedPagination = document.getElementById('feedPagination');
    showCommunityLoadingBar();
    feedPagination.innerHTML = '';
    fetch(`/community_feed?page=${page}`)
        .then(res => res.json())
        .then(data => {
            hideCommunityLoadingBar();
            renderFeed(data.feed, data.page, data.pages);
        });
}

document.addEventListener('DOMContentLoaded', function () {
    // Get current username for personalized feed
    fetch('/current_username')
        .then(res => res.json())
        .then(data => { currentUsername = data.username; });

    // Fetch user's library for autocomplete
    fetch('/my_library_books')
        .then(res => res.json())
        .then(books => { myLibrary = books; });
    
    // Fetch all usernames for autocomplete
    fetch('/all_usernames')
        .then(res => res.json())
        .then(users => { userList = users; });

    // Book autocomplete
    const bookInput = document.getElementById('bookSearchInput');
    const bookSuggestions = document.getElementById('bookSuggestions');
    const statusDisplay = document.getElementById('statusDisplay');
    const userInput = document.getElementById('userSearchInput');
    const userSuggestions = document.getElementById('userSuggestions');
    const shareForm = document.getElementById('shareForm');


    if (bookInput && bookSuggestions && statusDisplay) {
        bookInput.addEventListener('input', function () {
            const value = bookInput.value.trim().toLowerCase();
            selectedBook = null;
            statusDisplay.textContent = '';
            if (!value) {
                bookSuggestions.style.display = 'none';
                return;
            }
            const matches = myLibrary.filter(book =>
                fuzzyMatch(book.title, value) || fuzzyMatch(book.author, value)
            );
            renderBookSuggestions(matches.slice(0, 8));
        });

        bookInput.addEventListener('focus', () => {
            bookInput.dispatchEvent(new Event('input'));
        });

        document.addEventListener('click', function (e) {
            if (!bookInput.contains(e.target) && !bookSuggestions.contains(e.target)) {
                bookSuggestions.style.display = 'none';
            }
        });
    }

    // User autocomplete (single user)
    if (userInput && userSuggestions) {
        userInput.addEventListener('input', function () {
            const value = userInput.value.trim();
            selectedUser = null;
            if (!value) {
                userSuggestions.style.display = 'none';
                return;
            }
            const matches = userList.filter(username => fuzzyMatch(username, value));
            renderUserSuggestions(matches.slice(0, 8));
        });

        userInput.addEventListener('focus', function () {
            userInput.dispatchEvent(new Event('input'));
        });

        document.addEventListener('click', function (e) {
            if (!userInput.contains(e.target) && !userSuggestions.contains(e.target)) {
                userSuggestions.style.display = 'none';
            }
        });
    }

    // Share form submission
    if (shareForm && bookInput && userInput && statusDisplay) {
        shareForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const username = userInput.value.trim();
            if (!selectedBook || !username) {
                document.getElementById('shareMsg').textContent = "Please select a book and enter a username.";
                return;
            }
            document.getElementById('shareMsg').textContent = "Sharing...";
            fetch('/share_book', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    book_id: selectedBook.id,
                    username: username,
                    status: selectedBook.status
                })
            })
                .then(res => res.json())
                .then(data => {
                    document.getElementById('shareMsg').textContent = data.message;
                    loadFeed(feedPage); // reload current feed page after sharing
                    // Reset form
                    userInput.value = "";
                    bookInput.value = "";
                    statusDisplay.textContent = "";
                    selectedBook = null;
                    selectedUser = null;
                });
        });
    }

    // Initial feed load
    loadFeed();
});
