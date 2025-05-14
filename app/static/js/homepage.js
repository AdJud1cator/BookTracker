// --- Search Functionality ---
async function fetchBooks(query, maxResults = 20, orderBy = 'relevance') {
    const url = `https://www.googleapis.com/books/v1/volumes?q=${encodeURIComponent(query)}&maxResults=${maxResults}&orderBy=${orderBy}`;
    const resp = await fetch(url);
    const data = await resp.json();
    return (data.items || []);
}
function truncateTitle(title, maxLength = 50) {
    return title.length > maxLength ? title.substring(0, maxLength - 1) + '…' : title;
}
function renderBooks(books) {
    const grid = document.getElementById('booksGrid');
    grid.innerHTML = '';
    if (books.length === 0) {
        grid.innerHTML = '<p style="text-align:center; color:#888; width:100%;">No books found.</p>';
        return;
    }
    books.forEach(book => {
        const info = book.volumeInfo || {};
        const img = (info.imageLinks && info.imageLinks.thumbnail) || 'https://via.placeholder.com/110x160?text=No+Cover';
        const title = info.title ? truncateTitle(info.title) : 'No Title';
        const authors = (info.authors && info.authors.join(', ')) || 'Unknown Author';
        const desc = info.description ? info.description.substring(0, 80) + (info.description.length > 80 ? '…' : '') : '';
        const col = document.createElement('div');
        col.className = 'col-sm-6 col-md-4 col-lg-3 mb-4 d-flex';
        const detailsUrl = `/details?googleid=${book.id}`;
        col.innerHTML = `
            <a href="${detailsUrl}" class="book-card flex-fill d-flex flex-column" style="text-decoration:none; cursor:pointer;">
                <img src="${img}" alt="Book cover">
                <div class="book-title" title="${info.title || ''}">${title}</div>
                <div class="book-author">${authors}</div>
                <div class="book-desc">${desc}</div>
            </a>
        `;
        // Attach click event to the card link to show modal instead of navigating
        col.querySelector('a').addEventListener('click', function (e) {
            e.preventDefault(); // Prevent navigation
            const modal = new bootstrap.Modal(document.getElementById('loginPromptModal'));
            modal.show();
        });
        grid.appendChild(col);
    });
}

function showLoadingBar() {
    document.getElementById('loadingBar').style.display = 'block';
    document.getElementById('booksGrid').style.display = 'none';
}

function hideLoadingBar() {
    document.getElementById('loadingBar').style.display = 'none';
    document.getElementById('booksGrid').style.display = 'flex';
}

const searchForm = document.getElementById('searchForm');
if (searchForm) {
    searchForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        const query = document.getElementById('searchInput').value.trim();
        if (!query) {
            document.getElementById('resultsTitle').textContent = '';
            document.getElementById('booksGrid').innerHTML = '';
            return;
        }
        document.getElementById('resultsTitle').textContent = `Search Results for "${query}"`;
        showLoadingBar();
        const books = await fetchBooks(query, 20, 'relevance');
        renderBooks(books);
        hideLoadingBar();
    });
}