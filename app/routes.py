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
from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, PasswordField
from wtforms.validators import DataRequired

# ----------------- Forms -----------------
class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

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
def homepage(): return render_template("homepage.html")
@bp.route('/forgot')
def forgot(): return render_template("forgot.html")
@bp.route('/contact')
def contact(): return render_template("contact.html")
@bp.route('/terms')
def terms(): return render_template("terms.html")
@bp.route('/policy')
def policy(): return render_template("policy.html")
@bp.route('/copyright')
def copyright(): return render_template("copyright.html")

# ----------------- Main App Pages -----------------
@bp.route('/dashboard')
@login_required
def dashboard(): return render_template("dashboard.html")
@bp.route('/explore')
@login_required
def explore(): return render_template("explore.html")
@bp.route('/library')
@login_required
def library(): return render_template("Library.html")
@bp.route('/statistics')
@login_required
def statistics(): return render_template("Statistics.html")
@bp.route('/community')
@login_required
def community(): return render_template("community.html")

# ----------------- Book/Library APIs -----------------
@bp.route('/my_library_books')
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
        date_completed = datetime.now() if status == "completed" else None
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

@bp.route('/community_feed')
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

@bp.route('/user_suggestions')
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

@bp.route('/stats/avg_pages_by_genre')
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