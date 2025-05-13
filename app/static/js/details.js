const googleid = document.getElementById('detailsCard').dataset.googleid;
  let bookTitle = "", bookAuthors = "", bookCover = "", bookDesc = "", bookGenre = "", pageCount = null;

  function renderStars(rating) {
    if (!rating) return '';
    let stars = '';
    let rounded = Math.round(rating * 2) / 2;
    for (let i = 1; i <= 5; i++) {
      if (rounded >= i) stars += '★';
      else if (rounded >= i - 0.5) stars += '☆';
      else stars += '☆';
    }
    return `<span style="color:#f9bc1a; font-size:1.15em;">${stars}</span>`;
  }

  async function fetchBookDetails() {
    const url = `https://www.googleapis.com/books/v1/volumes/${googleid}`;
    const resp = await fetch(url);
    const data = await resp.json();
    return data;
  }

  function displayBookDetails(book) {
    const info = book.volumeInfo || {};
    bookTitle = info.title || 'No Title';
    bookAuthors = (info.authors && info.authors.join(', ')) || 'Unknown Author';
    bookCover = (info.imageLinks && info.imageLinks.thumbnail) || 'https://via.placeholder.com/150x220?text=No+Cover';
    bookDesc = info.description || '';
    bookGenre = (info.categories && info.categories.length > 0) ? info.categories[0].split('/')[0].trim() : 'Uncategorised';
    pageCount = info.pageCount || null;

    document.getElementById('bookCover').src = bookCover;
    document.getElementById('bookTitle').textContent = bookTitle;
    document.getElementById('bookAuthors').textContent = bookAuthors;
    document.getElementById('bookPublisher').textContent = info.publisher || 'Unknown Publisher';
    document.getElementById('bookPublished').textContent = info.publishedDate || 'Unknown Date';
    document.getElementById('bookPages').textContent = info.pageCount || 'Unknown';
    document.getElementById('bookCategories').textContent = bookGenre;

    let isbn = '-';
    if (info.industryIdentifiers && info.industryIdentifiers.length) {
      isbn = info.industryIdentifiers.map(i => i.identifier).join(', ');
    }
    document.getElementById('bookISBN').textContent = isbn;

    document.getElementById('bookDescription').innerHTML = bookDesc || '<span class="text-muted">No description available.</span>';
    document.getElementById('previewLink').href = (info.previewLink || '#');

    // Rating stars and count
    const rating = info.averageRating;
    document.getElementById('bookRating').innerHTML = rating ? renderStars(rating) + ` <span style="font-size:1.02em; color:#888;">${rating.toFixed(1)}</span>` : '<span class="text-muted">Not rated</span>';
    document.getElementById('ratingsCount').textContent = info.ratingsCount ? `(${info.ratingsCount} ratings)` : '';

    // Hide loading, show details
    document.getElementById('loadingOverlay').style.display = 'none';
    const card = document.getElementById('detailsCard');
    card.style.opacity = 1;
    card.style.pointerEvents = 'auto';
  }

  function setStatus(status) {
    fetch("/add_book", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        google_id: googleid,
        title: bookTitle,
        author: bookAuthors,
        description: bookDesc,
        cover_url: bookCover,
        genre: bookGenre,
        page_count: pageCount,
        status: status
      })
    })
      .then(response => response.json())
      .then(data => {
        Swal.fire({
          icon: data.success ? 'success' : 'error',
          title: data.message
        });
      });
  }

  // Show loading overlay immediately
  document.getElementById('loadingOverlay').style.display = 'flex';
  document.getElementById('detailsCard').style.opacity = 0;
  document.getElementById('detailsCard').style.pointerEvents = 'none';

  fetchBookDetails().then(displayBookDetails);