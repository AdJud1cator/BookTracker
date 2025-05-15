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
        grid.innerHTML = '<p style="text-align:center; color:var(--bs-secondary-color); width:100%;">No books found.</p>';
        return;
    }
    books.forEach(book => {
        const info = book.volumeInfo || {};
        const img = (info.imageLinks && info.imageLinks.thumbnail) || 'https://via.placeholder.com/110x160?text=No+Cover';
        const title = info.title ? truncateTitle(info.title) : 'No Title';
        const authors = (info.authors && info.authors.join(', ')) || 'Unknown Author';
        const desc = info.description ? info.description.substring(0, 80) + (info.description.length > 80 ? '…' : '') : '';
        const detailsUrl = `/details?googleid=${book.id}`;
        const card = document.createElement('a');
        card.className = 'book-card';
        card.href = detailsUrl;
        card.style.textDecoration = 'none'; // Optional: removes underline from link
        card.innerHTML = `
            <img src="${img}" alt="Book cover">
            <div class="book-title" title="${info.title || ''}">${title}</div>
            <div class="book-author">${authors}</div>
            <div class="book-desc">${desc}</div>
        `;
        grid.appendChild(card);
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

async function loadTrendingBooks() {
    document.getElementById('resultsTitle').textContent = 'Trending Books';
    showLoadingBar();
    const trendingBooks = await fetchBooks('bestsellers', 20, 'relevance');
    hideLoadingBar();
    renderBooks(trendingBooks);
}

document.getElementById('searchForm').addEventListener('submit', async function (e) {
    e.preventDefault();
    const query = document.getElementById('searchInput').value.trim();
    if (!query) {
        loadTrendingBooks();
        return;
    }
    document.getElementById('resultsTitle').textContent = `Search Results for "${query}"`;
    showLoadingBar();
    const books = await fetchBooks(query, 20, 'relevance');
    hideLoadingBar();
    renderBooks(books);
});


loadTrendingBooks();