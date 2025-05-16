from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from .models import User, UserBook, Book, BookShare
from . import db
from app import bp
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import desc, func
import calendar, re
from collections import defaultdict
from datetime import datetime, timezone
from app.forms import RegistrationForm, LoginForm


# ----------------- Registration -----------------
@bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    error, success = None, None
    if form.validate_on_submit():
        email = form.email.data
        username = form.username.data
        password = form.password.data
        confirm_password = form.confirm_password.data
        
        # Checks for errors
        if not username:
            form.username.errors.append('Username is required')

        if len(username) < 5:
            form.username.errors.append('Username must be at least 5 characters')

        if User.query.filter_by(username=username).first():
            form.username.errors.append('Username already exists')

        if not email:
            form.email.errors.append('Email is required')

        if not re.match(r'^[\w\.-]+@([\w-]+\.)+[\w-]{2,4}$', email):
            form.email.errors.append('Invalid email address')

        if User.query.filter_by(email=email).first():
            form.email.errors.append('Email already exists')

        if not password:
            form.password.errors.append('Password is required')

        if len(password) < 6:
            form.password.errors.append('Password must be at least 6 characters')

        if not re.match(r'.*[a-z].*', password):
            form.password.errors.append('Password must contain a lowercase letter')

        if not re.match(r'.*[A-Z].*', password):
            form.password.errors.append('Password must contain an uppercase letter')
        
        if not re.match(r'.*\d.*', password):
            form.password.errors.append('Password must contain a number')

        if not confirm_password:
            form.confirm_password.errors.append('Must confirm password')

        if not password==confirm_password:
            form.confirm_password.errors.append('Passwords do not match')


        if not (form.username.errors or form.email.errors or form.password.errors or form.confirm_password.errors):
            # Create new user
            hashed_pw = generate_password_hash(password)
            db.session.add(User(email=email, username=username, password=hashed_pw))
            db.session.commit()
            success = 'Registration successful! Redirecting to login...'
            return redirect(url_for('main.login'))
        
    return render_template('register.html', form=form, error=error, success=success)

# ----------------- Login/Logout -----------------
@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    error, success = None, None
    
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            success = 'Registration successful! Redirecting to login...'
            login_user(user)
            return redirect(url_for('main.dashboard'))
        else: 
            form.username.errors.append('Invalid username or password')

    return render_template('login.html', form=form, error=error, success=success)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.homepage'))

# ----------------- Static Pages -----------------
@bp.route('/')
def homepage():  
    if current_user.is_authenticated:
        base_template = "base_member.html"
    else:
        base_template = "base_anon.html"
    return render_template("homepage.html", base_template=base_template)
@bp.route('/contact')
def contact(): 
    if current_user.is_authenticated:
        base_template = "base_member.html"
    else:
        base_template = "base_anon.html"
    return render_template("contact.html", base_template=base_template)
@bp.route('/terms')
def terms(): 
    if current_user.is_authenticated:
        base_template = "base_member.html"
    else:
        base_template = "base_anon.html"
    return render_template("terms.html", base_template=base_template)
@bp.route('/policy')
def policy(): 
    if current_user.is_authenticated:
        base_template = "base_member.html"
    else:
        base_template = "base_anon.html"
    return render_template("policy.html", base_template=base_template)
@bp.route('/copyright')
def copyright(): 
    if current_user.is_authenticated:
        base_template = "base_member.html"
    else:
        base_template = "base_anon.html"
    return render_template("copyright.html", base_template=base_template)

@bp.route('/forgot')
def forgot(): return render_template("forgot.html")

# ----------------- Main App Pages -----------------
@bp.route('/dashboard')
@login_required
def dashboard(): 
    feed_items = BookShare.query\
        .filter(
            (BookShare.from_user_id == current_user.id) |
            (BookShare.to_user_id == current_user.id)
        )\
        .order_by(BookShare.timestamp.desc())\
        .limit(10).all()

    has_feed = len(feed_items) > 0

    currently_reading_books = UserBook.query\
        .filter(UserBook.user_id == current_user.id, UserBook.status == 'currently_reading')\
        .all()

    has_currently_reading = len(currently_reading_books) > 0

    return render_template("dashboard.html", active_page='dashboard', has_feed=has_feed, has_currently_reading=has_currently_reading)

@bp.route('/explore')
@login_required
def explore(): return render_template("explore.html", active_page='explore')
@bp.route('/library')
@login_required
def library(): return render_template("library.html", active_page='library')
@bp.route('/statistics')
@login_required
def statistics(): return render_template("statistics.html", active_page='statistics')
@bp.route('/community')
@login_required
def community(): return render_template("community.html", active_page='community')

@bp.route('/all_usernames')
@login_required
def all_usernames():
    # Exclude current user
    users = User.query.filter(User.id != current_user.id).all()
    usernames = [user.username for user in users]
    return jsonify(usernames)

@bp.route('/current_username')
@login_required
def current_username():
    return jsonify({'username': current_user.username})


# ----------------- Book/Library APIs -----------------
@bp.route('/my_library_books')
@login_required
def my_library_books():
    user_books = UserBook.query.filter_by(user_id=current_user.id).all()
    return jsonify([
        {
            "id": user_book.id,
            "google_id": user_book.book.google_id,
            "title": user_book.book.title,
            "author": user_book.book.author,
            "cover_url": user_book.book.cover_url,
            "status": user_book.status,
            "description": user_book.book.description or "",
        }
        for user_book in user_books
    ])


@bp.route('/my_books')
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

@bp.route('/details')
@login_required
def details():
    googleid = request.args.get('googleid')
    if not googleid:
        return "No book ID provided.", 400
    return render_template('details.html', googleid=googleid)

@bp.route('/add_book', methods=['POST'])
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
        if status == "completed":
            userbook.date_completed = datetime.now(timezone.utc)
        else:
            userbook.date_completed = None
    else:
        date_completed = datetime.now(timezone.utc) if status == "completed" else None
        db.session.add(UserBook(
            user_id=current_user.id,
            book_id=book.id,
            status=status,
            date_completed=date_completed
        ))
    db.session.commit()
    return jsonify({"success": True, "message": message})

# ----------------- Community/Sharing APIs -----------------
@bp.route('/share_book', methods=['POST'])
@login_required
def share_book():
    data = request.get_json()
    book_id = data.get('book_id')
    username = data.get('username')
    status = data.get('status')

    if not book_id or not username or not status:
        return jsonify({'success': False, 'message': 'Missing data.'}), 400

    # Find the recipient user
    to_user = User.query.filter_by(username=username).first()
    if not to_user:
        return jsonify({'success': False, 'message': 'User not found.'}), 404

    # Prevent sharing with self
    if to_user.id == current_user.id:
        return jsonify({'success': False, 'message': 'You cannot share with yourself.'}), 400

    # Find the book
    user_book = UserBook.query.filter_by(id=book_id, user_id=current_user.id).first()
    if not user_book:
        return jsonify({'success': False, 'message': 'Book not found in your library.'}), 404

    # Create the BookShare
    share = BookShare(
        from_user_id=current_user.id,
        to_user_id=to_user.id,
        book_id=user_book.book_id,
        status=status
    )
    db.session.add(share)
    db.session.commit()

    return jsonify({'success': True, 'message': f'Shared "{user_book.book.title}" with {username}.'})

@bp.route('/community_feed')
@login_required
def community_feed():
    page = request.args.get('page', 1, type=int)
    per_page = 10

    # Show shares where the user is sender or receiver, newest first
    shares = BookShare.query.filter(
        (BookShare.from_user_id == current_user.id) | (BookShare.to_user_id == current_user.id)
    ).order_by(BookShare.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)

    feed = []
    for share in shares.items:
        book = share.book
        feed.append({
            'title': book.title,
            'cover_url': book.cover_url,
            'status': share.status.title(),
            'from_username': share.from_user.username,
            'to_username': share.to_user.username,
            'timestamp': share.timestamp.strftime('%Y-%m-%d %H:%M'),
        })

    return jsonify({
        'feed': feed,
        'has_next': shares.has_next,
        'has_prev': shares.has_prev,
        'page': shares.page,
        'pages': shares.pages
    })

# ----------------- Statistics APIs -----------------
@bp.route('/stats/summary')
@login_required
def stats_summary():
    # Total books read
    total_books_read = (
        db.session.query(func.count(UserBook.id))
        .filter(UserBook.user_id == current_user.id, UserBook.status == 'completed')
        .scalar()
    )
    # Total pages read
    total_pages_read = (
        db.session.query(func.sum(Book.page_count))
        .join(UserBook, Book.id == UserBook.book_id)
        .filter(UserBook.user_id == current_user.id, UserBook.status == 'completed')
        .scalar() or 0
    )
    # Favorite genre
    genre_result = (
        db.session.query(Book.genre, func.count(Book.id))
        .join(UserBook, Book.id == UserBook.book_id)
        .filter(UserBook.user_id == current_user.id)
        .group_by(Book.genre)
        .order_by(desc(func.count(Book.id)))
        .first()
    )
    favorite_genre = genre_result[0] if genre_result else None

    # Most-read author
    author_result = (
        db.session.query(Book.author, func.count(Book.id))
        .join(UserBook, Book.id == UserBook.book_id)
        .filter(UserBook.user_id == current_user.id)
        .group_by(Book.author)
        .order_by(desc(func.count(Book.id)))
        .first()
    )
    most_read_author = author_result[0] if author_result else None

    # Longest book read
    longest = (
        db.session.query(Book.title, Book.page_count)
        .join(UserBook, Book.id == UserBook.book_id)
        .filter(UserBook.user_id == current_user.id, UserBook.status == 'completed', Book.page_count != None)
        .order_by(desc(Book.page_count))
        .first()
    )
    longest_book = {"title": longest[0], "pages": longest[1]} if longest else None

    # Shortest book read
    shortest = (
        db.session.query(Book.title, Book.page_count)
        .join(UserBook, Book.id == UserBook.book_id)
        .filter(UserBook.user_id == current_user.id, UserBook.status == 'completed', Book.page_count != None)
        .order_by(Book.page_count)
        .first()
    )
    shortest_book = {"title": shortest[0], "pages": shortest[1]} if shortest else None

    # Books shared
    books_shared = (
    db.session.query(func.count())
    .select_from(BookShare)
    .filter(BookShare.from_user_id == current_user.id)
    .scalar()
    )

    return jsonify({
        "total_books_read": total_books_read or 0,
        "total_pages_read": total_pages_read or 0,
        "favorite_genre": favorite_genre,
        "most_read_author": most_read_author,
        "longest_book": longest_book,
        "shortest_book": shortest_book,
        "books_shared": books_shared or 0,
    })

@bp.route('/stats/books_over_time')
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

@bp.route('/stats/pages_over_time')
@login_required
def stats_pages_over_time():
    range_type = request.args.get('range', 'months')
    query = (
        db.session.query(UserBook.date_completed, Book.page_count)
        .join(Book, UserBook.book_id == Book.id)
        .filter(
            UserBook.user_id == current_user.id,
            UserBook.status == 'completed',
            UserBook.date_completed != None,
            Book.page_count != None
        )
    )
    data = {}
    if range_type == 'weeks':
        week_counts = defaultdict(int)
        for d, pages in query:
            if d:
                year, week, _ = d.isocalendar()
                key = f"{year} W{week}"
                week_counts[key] += pages or 0
        sorted_weeks = sorted(week_counts.items())
        data = {
            "labels": [k for k, _ in sorted_weeks],
            "data": [v for _, v in sorted_weeks]
        }
    elif range_type == 'months':
        month_counts = defaultdict(int)
        for d, pages in query:
            if d:
                key = f"{calendar.month_abbr[d.month]} {d.year}"
                month_counts[key] += pages or 0
        sorted_months = sorted(month_counts.items(), key=lambda x: (int(x[0].split()[1]), list(calendar.month_abbr).index(x[0].split()[0])))
        data = {
            "labels": [k for k, _ in sorted_months],
            "data": [v for _, v in sorted_months]
        }
    elif range_type == 'years':
        year_counts = defaultdict(int)
        for d, pages in query:
            if d:
                year_counts[str(d.year)] += pages or 0
        sorted_years = sorted(year_counts.items())
        data = {
            "labels": [k for k, _ in sorted_years],
            "data": [v for _, v in sorted_years]
        }
    else:  # 'all'
        total = sum(pages or 0 for _, pages in query)
        data = {
            "labels": ["All Time"],
            "data": [total]
        }
    return jsonify(data)

@bp.route('/stats/genres')
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

@bp.route('/stats/statuses')
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

@bp.route('/stats/authors')
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