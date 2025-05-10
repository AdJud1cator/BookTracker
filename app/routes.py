from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from .models import User, UserBook, Book, BookShare
from . import db
from app import app
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import desc, func
import calendar
from collections import defaultdict

# ----------------- Registration -----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    error, success = None, None
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            error = 'Please provide both username and password.'
        elif User.query.filter_by(username=username).first():
            error = 'Username already exists.'
        else:
            hashed_pw = generate_password_hash(password)
            db.session.add(User(email=email, username=username, password=hashed_pw))
            db.session.commit()
            success = 'Registration successful! Redirecting to login...'
            return redirect(url_for('dashboard'))
    return render_template('register.html', error=error, success=success)

# ----------------- Login/Logout -----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        error = 'Invalid username or password.'
    return render_template('login.html', error=error)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('homepage'))

# ----------------- Static Pages -----------------
@app.route('/')
def homepage(): return render_template("homepage.html")
@app.route('/contact')
def contact(): return render_template("contact.html")
@app.route('/terms')
def terms(): return render_template("terms.html")
@app.route('/policy')
def policy(): return render_template("policy.html")
@app.route('/copyright')
def copyright(): return render_template("copyright.html")

# ----------------- Main App Pages -----------------
@app.route('/dashboard')
@login_required
def dashboard(): return render_template("dashboard.html")
@app.route('/explore')
@login_required
def explore(): return render_template("explore.html")
@app.route('/library')
@login_required
def library(): return render_template("Library.html")
@app.route('/statistics')
@login_required
def statistics(): return render_template("Statistics.html")
@app.route('/community')
@login_required
def community(): return render_template("community.html")

# ----------------- Book/Library APIs -----------------
@app.route('/my_library_books')
@login_required
def my_library_books():
    books = [{
        "id": ub.book.id,
        "google_id": ub.book.google_id,
        "title": ub.book.title,
        "author": ub.book.author,
        "cover_url": ub.book.cover_url or "https://via.placeholder.com/60x90?text=No+Cover",
        "status": ub.status
    } for ub in UserBook.query.filter_by(user_id=current_user.id)]
    return jsonify(books)

@app.route('/my_books')
@login_required
def my_books():
    books = [{
        "google_id": ub.book.google_id or "",
        "title": ub.book.title,
        "author": ub.book.author,
        "genre": ub.book.genre,
        "cover_url": ub.book.cover_url or "https://via.placeholder.com/60x90?text=No+Cover",
        "status": ub.status,
        "date_added": ub.date_added.isoformat() if ub.date_added else "",
        "date_completed": ub.date_completed.isoformat() if ub.date_completed else ""
    } for ub in UserBook.query.filter_by(user_id=current_user.id)]
    return jsonify(books)

@app.route('/details')
@login_required
def details():
    googleid = request.args.get('googleid')
    if not googleid:
        return "No book ID provided.", 400
    return render_template('details.html', googleid=googleid)

@app.route('/add_book', methods=['POST'])
@login_required
def add_book():
    data = request.get_json()
    google_id = data.get('google_id')
    title = data.get('title')
    author = data.get('author')
    description = data.get('description')
    cover_url = data.get('cover_url')
    status = data.get('status')
    genre = data.get('genre')
    page_count = data.get('page_count')

    # Create or get book
    book = Book.query.filter_by(google_id=google_id).first()
    if not book:
        book = Book(
            google_id=google_id,
            title=title,
            author=author,
            description=description,
            cover_url=cover_url,
            genre=genre,
            page_count=page_count
        )
        db.session.add(book)
        db.session.commit()

    # Add or update UserBook
    userbook = UserBook.query.filter_by(user_id=current_user.id, book_id=book.id).first()
    message = "Book status updated in your library!" if userbook else "Book added to your library!"
    if userbook:
        userbook.status = status
    else:
        db.session.add(UserBook(user_id=current_user.id, book_id=book.id, status=status))
    db.session.commit()
    return jsonify({"success": True, "message": message})

# ----------------- Community/Sharing APIs -----------------
@app.route('/share_book', methods=['POST'])
@login_required
def share_book():
    data = request.get_json()
    book_id = data.get('book_id')
    usernames = data.get('usernames', [])
    status = data.get('status')

    book = Book.query.get(book_id)
    if not book:
        return jsonify({"success": False, "message": "Book not found."}), 404

    shared_users = []
    for username in usernames:
        user = User.query.filter_by(username=username).first()
        if user and user.id != current_user.id:
            db.session.add(BookShare(
                from_user_id=current_user.id,
                to_user_id=user.id,
                book_id=book.id,
                status=status
            ))
            shared_users.append(username)
    db.session.commit()
    if shared_users:
        return jsonify({"success": True, "message": f"Book shared with: {', '.join(shared_users)}"})
    return jsonify({"success": False, "message": "No valid users to share with."})

@app.route('/community_feed')
@login_required
def community_feed():
    shares = BookShare.query.order_by(desc(BookShare.timestamp)).limit(50).all()
    feed = [{
        "title": share.book.title,
        "author": share.book.author,
        "cover_url": share.book.cover_url or "https://via.placeholder.com/60x90?text=No+Cover",
        "status": share.status,
        "from_username": share.from_user.username,
        "timestamp": share.timestamp.strftime("%b %d, %Y %H:%M")
    } for share in shares]
    return jsonify(feed)

@app.route('/user_suggestions')
@login_required
def user_suggestions():
    term = request.args.get('q', '').strip()
    if not term:
        return jsonify([])
    users = User.query.filter(
        User.username.ilike(f"%{term}%"),
        User.id != current_user.id
    ).limit(10)
    return jsonify([u.username for u in users])

# ----------------- Statistics APIs -----------------
@app.route('/stats/genres')
@login_required
def stats_genres():
    results = (
        db.session.query(Book.genre, func.count(Book.id))
        .join(UserBook, Book.id == UserBook.book_id)
        .filter(UserBook.user_id == current_user.id)
        .group_by(Book.genre)
        .all()
    )
    genre_counts = {genre or "Other": count for genre, count in results}
    sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
    top_10 = dict(sorted_genres[:10])
    if len(sorted_genres) > 10:
        others = sum(count for _, count in sorted_genres[10:])
        top_10["Other"] = top_10.get("Other", 0) + others
    return jsonify(top_10)

@app.route('/stats/books_over_time')
@login_required
def stats_books_over_time():
    range_type = request.args.get('range', 'months')
    query = (
        db.session.query(UserBook.date_completed)
        .filter(
            UserBook.user_id == current_user.id,
            UserBook.status == 'completed',
            UserBook.date_completed != None
        )
    )
    dates = [ub.date_completed for ub in query if ub.date_completed]

    data = {}
    if range_type == 'weeks':
        week_counts = defaultdict(int)
        for d in dates:
            year, week, _ = d.isocalendar()
            key = f"{year} W{week}"
            week_counts[key] += 1
        sorted_weeks = sorted(week_counts.items())
        data = {
            "labels": [k for k, _ in sorted_weeks],
            "data": [v for _, v in sorted_weeks]
        }
    elif range_type == 'months':
        month_counts = defaultdict(int)
        for d in dates:
            key = f"{calendar.month_abbr[d.month]} {d.year}"
            month_counts[key] += 1
        sorted_months = sorted(month_counts.items(), key=lambda x: (int(x[0].split()[1]), list(calendar.month_abbr).index(x[0].split()[0])))
        data = {
            "labels": [k for k, _ in sorted_months],
            "data": [v for _, v in sorted_months]
        }
    elif range_type == 'years':
        year_counts = defaultdict(int)
        for d in dates:
            year_counts[str(d.year)] += 1
        sorted_years = sorted(year_counts.items())
        data = {
            "labels": [k for k, _ in sorted_years],
            "data": [v for _, v in sorted_years]
        }
    else:  # 'all'
        data = {
            "labels": ["All Time"],
            "data": [len(dates)]
        }
    return jsonify(data)

@app.route('/stats/statuses')
@login_required
def stats_statuses():
    results = (
        db.session.query(UserBook.status, func.count(UserBook.id))
        .filter(UserBook.user_id == current_user.id)
        .group_by(UserBook.status)
        .all()
    )
    status_map = {
        "completed": "Completed",
        "currently_reading": "Currently Reading",
        "wishlist": "Wishlist"
    }
    status_counts = {status_map.get(status, status.title()): count for status, count in results}
    return jsonify(status_counts)

@app.route('/stats/authors')
@login_required
def stats_authors():
    results = (
        db.session.query(Book.author, func.count(Book.id))
        .join(UserBook, Book.id == UserBook.book_id)
        .filter(UserBook.user_id == current_user.id)
        .group_by(Book.author)
        .all()
    )
    author_counts = {author or "Unknown": count for author, count in results}
    sorted_authors = sorted(author_counts.items(), key=lambda x: x[1], reverse=True)
    top_10 = dict(sorted_authors[:10])
    if len(sorted_authors) > 10:
        others = sum(count for _, count in sorted_authors[10:])
        top_10["Other"] = top_10.get("Other", 0) + others
    return jsonify(top_10)

@app.route('/stats/avg_pages_by_genre')
@login_required
def stats_avg_pages_by_genre():
    # You must have a page_count field in Book model for this to work!
    results = (
        db.session.query(Book.genre, func.avg(Book.page_count))  # Change to Book.page_count if you have it!
        .join(UserBook, Book.id == UserBook.book_id)
        .filter(UserBook.user_id == current_user.id)
        .group_by(Book.genre)
        .all()
    )
    avg_pages = {genre or "Other": round(avg or 0) for genre, avg in results}
    return jsonify(avg_pages)
