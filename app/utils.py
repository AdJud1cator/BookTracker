import re
import calendar
from collections import defaultdict
from datetime import datetime, timezone
from sqlalchemy import desc, func
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User, UserBook, Book, BookShare
from . import db

# --------- Registration & Login Utilities ---------

def validate_registration_form(form):
    errors = {'username': [], 'email': [], 'password': [], 'confirm_password': []}
    username = form.username.data
    email = form.email.data
    password = form.password.data
    confirm_password = form.confirm_password.data

    if not username:
        errors['username'].append('Username is required')
    elif len(username) < 5:
        errors['username'].append('Username must be at least 5 characters')
    if User.query.filter_by(username=username).first():
        errors['username'].append('Username already exists')

    if not email:
        errors['email'].append('Email is required')
    elif not re.match(r'^[\w\.-]+@([\w-]+\.)+[\w-]{2,4}$', email):
        errors['email'].append('Invalid email address')
    if User.query.filter_by(email=email).first():
        errors['email'].append('Email already exists')

    if not password:
        errors['password'].append('Password is required')
    elif len(password) < 6:
        errors['password'].append('Password must be at least 6 characters')
    if not re.match(r'.*[a-z].*', password):
        errors['password'].append('Password must contain a lowercase letter')
    if not re.match(r'.*[A-Z].*', password):
        errors['password'].append('Password must contain an uppercase letter')
    if not re.match(r'.*\d.*', password):
        errors['password'].append('Password must contain a number')

    if not confirm_password:
        errors['confirm_password'].append('Must confirm password')
    if password != confirm_password:
        errors['confirm_password'].append('Passwords do not match')

    errors = {k: v for k, v in errors.items() if v}
    return (not errors), errors

def register_user(form):
    hashed_pw = generate_password_hash(form.password.data)
    user = User(email=form.email.data, username=form.username.data, password=hashed_pw)
    db.session.add(user)
    db.session.commit()
    return user

def validate_login_form(form):
    user = User.query.filter_by(username=form.username.data).first()
    if user and check_password_hash(user.password, form.password.data):
        return True, user
    else:
        return False, None

# --------- User Utilities ---------

def get_all_usernames(exclude_user_id):
    users = User.query.filter(User.id != exclude_user_id).all()
    return [user.username for user in users]

# --------- Library Utilities ---------

def get_user_library_books(user_id):
    user_books = UserBook.query.filter_by(user_id=user_id).all()
    return user_books

def get_user_books(user_id):
    return [{
        "google_id": ub.book.google_id or "",
        "title": ub.book.title,
        "author": ub.book.author,
        "genre": ub.book.genre,
        "cover_url": ub.book.cover_url or "https://via.placeholder.com/60x90?text=No+Cover",
        "status": ub.status,
        "date_added": ub.date_added.isoformat() if ub.date_added else "",
        "date_completed": ub.date_completed.isoformat() if ub.date_completed else ""
    } for ub in UserBook.query.filter_by(user_id=user_id)]

def add_book_to_library(user_id, data):
    google_id = data.get('google_id')
    title = data.get('title')
    author = data.get('author')
    description = data.get('description')
    cover_url = data.get('cover_url')
    status = data.get('status')
    genre = data.get('genre')
    page_count = data.get('page_count')

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
    else:
        updated = False
        if not book.title and title:
            book.title = title
            updated = True
        if not book.author and author:
            book.author = author
            updated = True
        if not book.description and description:
            book.description = description
            updated = True
        if not book.cover_url and cover_url:
            book.cover_url = cover_url
            updated = True
        if not book.genre and genre:
            book.genre = genre
            updated = True
        if not book.page_count and page_count:
            book.page_count = page_count
            updated = True
        if updated:
            db.session.commit()

    userbook = UserBook.query.filter_by(user_id=user_id, book_id=book.id).first()
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
            user_id=user_id,
            book_id=book.id,
            status=status,
            date_completed=date_completed
        ))
    db.session.commit()
    return {"success": True, "message": message}

def delete_book_from_library(user_id, user_book_id):
    user_book = UserBook.query.get(user_book_id)
    if not user_book or user_book.user_id != user_id:
        return {'error': 'Unauthorized'}, 403
    db.session.delete(user_book)
    db.session.commit()
    return {'success': True}, 200

# --------- Book Sharing Utilities ---------

def share_book_with_user(from_user_id, book_id, to_username, status):
    if not book_id or not to_username or not status:
        return {'success': False, 'message': 'Missing data.'}, 400

    to_user = User.query.filter_by(username=to_username).first()
    if not to_user:
        return {'success': False, 'message': 'User not found.'}, 404

    if to_user.id == from_user_id:
        return {'success': False, 'message': 'You cannot share with yourself.'}, 400

    user_book = UserBook.query.filter_by(id=book_id, user_id=from_user_id).first()
    if not user_book:
        return {'success': False, 'message': 'Book not found in your library.'}, 404

    share = BookShare(
        from_user_id=from_user_id,
        to_user_id=to_user.id,
        book_id=user_book.book_id,
        status=status
    )
    db.session.add(share)
    db.session.commit()
    return {'success': True, 'message': f'Shared "{user_book.book.title}" with {to_username}.'}, 200

def get_community_feed(user_id, page=1, per_page=10):
    shares = BookShare.query.filter(
        (BookShare.from_user_id == user_id) | (BookShare.to_user_id == user_id)
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
            'google_id': book.google_id
        })

    return {
        'feed': feed,
        'has_next': shares.has_next,
        'has_prev': shares.has_prev,
        'page': shares.page,
        'pages': shares.pages
    }

# --------- Statistics Utilities ---------

def get_stats_summary(user_id):
    total_books_read = (
        db.session.query(func.count(UserBook.id))
        .filter(UserBook.user_id == user_id, UserBook.status == 'completed')
        .scalar()
    )
    total_pages_read = (
        db.session.query(func.sum(Book.page_count))
        .join(UserBook, Book.id == UserBook.book_id)
        .filter(UserBook.user_id == user_id, UserBook.status == 'completed')
        .scalar() or 0
    )
    genre_result = (
        db.session.query(Book.genre, func.count(Book.id))
        .join(UserBook, Book.id == UserBook.book_id)
        .filter(UserBook.user_id == user_id)
        .group_by(Book.genre)
        .order_by(desc(func.count(Book.id)))
        .first()
    )
    favorite_genre = genre_result[0] if genre_result else None

    author_result = (
        db.session.query(Book.author, func.count(Book.id))
        .join(UserBook, Book.id == UserBook.book_id)
        .filter(UserBook.user_id == user_id)
        .group_by(Book.author)
        .order_by(desc(func.count(Book.id)))
        .first()
    )
    most_read_author = author_result[0] if author_result else None

    longest = (
        db.session.query(Book.title, Book.page_count)
        .join(UserBook, Book.id == UserBook.book_id)
        .filter(UserBook.user_id == user_id, UserBook.status == 'completed', Book.page_count != None)
        .order_by(desc(Book.page_count))
        .first()
    )
    longest_book = {"title": longest[0], "pages": longest[1]} if longest else None

    shortest = (
        db.session.query(Book.title, Book.page_count)
        .join(UserBook, Book.id == UserBook.book_id)
        .filter(UserBook.user_id == user_id, UserBook.status == 'completed', Book.page_count != None)
        .order_by(Book.page_count)
        .first()
    )
    shortest_book = {"title": shortest[0], "pages": shortest[1]} if shortest else None

    books_shared = (
        db.session.query(func.count())
        .select_from(BookShare)
        .filter(BookShare.from_user_id == user_id)
        .scalar()
    )

    return {
        "total_books_read": total_books_read or 0,
        "total_pages_read": total_pages_read or 0,
        "favorite_genre": favorite_genre,
        "most_read_author": most_read_author,
        "longest_book": longest_book,
        "shortest_book": shortest_book,
        "books_shared": books_shared or 0,
    }

def get_books_over_time(user_id, range_type='months'):
    query = (
        db.session.query(UserBook.date_completed)
        .filter(
            UserBook.user_id == user_id,
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
    return data

def get_pages_over_time(user_id, range_type='months'):
    query = (
        db.session.query(UserBook.date_completed, Book.page_count)
        .join(Book, UserBook.book_id == Book.id)
        .filter(
            UserBook.user_id == user_id,
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
    return data

def get_genre_stats(user_id):
    results = (
        db.session.query(Book.genre, func.count(Book.id))
        .join(UserBook, Book.id == UserBook.book_id)
        .filter(UserBook.user_id == user_id)
        .group_by(Book.genre)
        .all()
    )
    genre_counts = {genre or "Other": count for genre, count in results}
    sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
    top_10 = dict(sorted_genres[:10])
    if len(sorted_genres) > 10:
        others = sum(count for _, count in sorted_genres[10:])
        top_10["Other"] = top_10.get("Other", 0) + others
    return top_10

def get_status_stats(user_id):
    results = (
        db.session.query(UserBook.status, func.count(UserBook.id))
        .filter(UserBook.user_id == user_id)
        .group_by(UserBook.status)
        .all()
    )
    status_map = {
        "completed": "Completed",
        "currently_reading": "Currently Reading",
        "wishlist": "Wishlist"
    }
    status_counts = {status_map.get(status, status.title()): count for status, count in results}
    return status_counts

def get_author_stats(user_id):
    results = (
        db.session.query(Book.author, func.count(Book.id))
        .join(UserBook, Book.id == UserBook.book_id)
        .filter(UserBook.user_id == user_id)
        .group_by(Book.author)
        .all()
    )
    author_counts = {author or "Unknown": count for author, count in results}
    sorted_authors = sorted(author_counts.items(), key=lambda x: x[1], reverse=True)
    top_10 = dict(sorted_authors[:10])
    if len(sorted_authors) > 10:
        others = sum(count for _, count in sorted_authors[10:])
        top_10["Other"] = top_10.get("Other", 0) + others
    return top_10
