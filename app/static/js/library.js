function renderBooksGrid(books, gridId) {
    const grid = document.getElementById(gridId);
    grid.innerHTML = '';
    if (!books || books.length === 0) {
        grid.innerHTML = `<p style="text-align:center; color:var(--bs-secondary-color); width:100%;">No books in this section.</p>`;
        return;
    }
    books.forEach(book => {
        const card = document.createElement('a');
        card.className = 'book-card';
        card.href = `/details?googleid=${book.google_id}`;
        card.innerHTML = `
            <img src="${book.cover_url || 'https://via.placeholder.com/110x160?text=No+Cover'}" alt="Book cover">
            <div class="book-title" title="${book.title || ''}">${book.title || 'No Title'}</div>
            <div class="book-author">${book.author || 'Unknown Author'}</div>
            <div class="book-desc">${book.description ? book.description.substring(0, 80) + (book.description.length > 80 ? '…' : '') : ''}</div>
        `;
        grid.appendChild(card);
    });
}

function loadLibrary() {
    fetch('/my_books')
        .then(response => response.json())
        .then(books => {
            renderBooksGrid(books.filter(b => b.status === 'currently_reading'), 'currentlyReadingGrid');
            renderBooksGrid(books.filter(b => b.status === 'completed'), 'completedGrid');
            renderBooksGrid(books.filter(b => b.status === 'wishlist'), 'wishlistGrid');
        });
}

loadLibrary();