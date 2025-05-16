from flask import jsonify, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf.csrf import generate_csrf
from .models import UserBook, BookShare
from .forms import RegistrationForm, LoginForm
from .blueprints import bp
from .utils import (
    validate_registration_form, register_user,
    validate_login_form, get_all_usernames,
    get_user_library_books, get_user_books,
    add_book_to_library, delete_book_from_library,
    share_book_with_user, get_community_feed,
    get_stats_summary, get_books_over_time,
    get_pages_over_time, get_genre_stats,
    get_status_stats, get_author_stats
)

# ----------------- Registration -----------------

@bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        valid, errors = validate_registration_form(form)
        if valid:
            register_user(form)
            return redirect(url_for('main.login'))
        else:
            for field, msgs in errors.items():
                for msg in msgs:
                    getattr(form, field).errors.append(msg)
    return render_template('register.html', form=form)

# ----------------- Login/Logout -----------------

@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        valid, user = validate_login_form(form)
        if valid:
            login_user(user)
            return redirect(url_for('main.dashboard'))
        else:
            form.username.errors.append('Invalid username or password')
    return render_template('login.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.homepage'))

# ----------------- Delete Book -----------------

@bp.route('/delete_book/<int:user_book_id>', methods=['POST', 'DELETE'])
@login_required
def delete_book_route(user_book_id):
    result, status = delete_book_from_library(current_user.id, user_book_id)
    if status == 200:
        flash("Book deleted successfully.", "success")
    else:
        flash(result.get('error', 'Error deleting book'), "danger")
    return redirect(url_for('main.library'))

# ----------------- Static Pages -----------------

@bp.route('/')
def homepage():
    base_template = "base_member.html" if current_user.is_authenticated else "base_anon.html"
    return render_template("homepage.html", base_template=base_template)

@bp.route('/contact')
def contact():
    base_template = "base_member.html" if current_user.is_authenticated else "base_anon.html"
    return render_template("contact.html", base_template=base_template)

@bp.route('/terms')
def terms():
    base_template = "base_member.html" if current_user.is_authenticated else "base_anon.html"
    return render_template("terms.html", base_template=base_template)

@bp.route('/policy')
def policy():
    base_template = "base_member.html" if current_user.is_authenticated else "base_anon.html"
    return render_template("policy.html", base_template=base_template)

@bp.route('/copyright')
def copyright():
    base_template = "base_member.html" if current_user.is_authenticated else "base_anon.html"
    return render_template("copyright.html", base_template=base_template)

@bp.route('/faq')
def faq():
    base_template = "base_member.html" if current_user.is_authenticated else "base_anon.html"
    return render_template("faq.html", base_template=base_template)

@bp.route('/forgot')
def forgot():
    return render_template("forgot.html")

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

    return render_template(
        "dashboard.html",
        active_page='dashboard',
        has_feed=has_feed,
        has_currently_reading=has_currently_reading
    )

@bp.route('/explore')
@login_required
def explore():
    return render_template("explore.html", active_page='explore')

@bp.route('/library')
@login_required
def library():
    user_books = get_user_library_books(current_user.id)
    return render_template('library.html', active_page='library', books=user_books)

@bp.route('/statistics')
@login_required
def statistics():
    return render_template("statistics.html", active_page='statistics')

@bp.route('/community')
@login_required
def community():
    return render_template("community.html", active_page='community')

@bp.route('/details')
@login_required
def details():
    googleid = request.args.get('googleid')
    if not googleid:
        return "No book ID provided.", 400
    return render_template('details.html', googleid=googleid)

# ----------------- CSRF Token -----------------

@bp.route('/csrf-token', methods=['GET'])
def csrf_token():
    return jsonify({'csrf_token': generate_csrf()})

# ----------------- API Endpoints -----------------

@bp.route('/all_usernames')
@login_required
def all_usernames():
    usernames = get_all_usernames(current_user.id)
    return jsonify(usernames)

@bp.route('/my_library_books')
@login_required
def my_library_books():
    books = get_user_library_books(current_user.id)
    return jsonify(books)

@bp.route('/my_books')
@login_required
def my_books():
    books = get_user_books(current_user.id)
    return jsonify(books)

@bp.route('/add_book', methods=['POST'])
@login_required
def add_book():
    data = request.get_json()
    result = add_book_to_library(current_user.id, data)
    return jsonify(result)

@bp.route('/share_book', methods=['POST'])
@login_required
def share_book():
    data = request.get_json()
    book_id = data.get('book_id')
    username = data.get('username')
    status = data.get('status')
    result, code = share_book_with_user(current_user.id, book_id, username, status)
    return jsonify(result), code

@bp.route('/community_feed')
@login_required
def community_feed():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    feed = get_community_feed(current_user.id, page, per_page)
    return jsonify(feed)

@bp.route('/stats/summary')
@login_required
def stats_summary():
    summary = get_stats_summary(current_user.id)
    return jsonify(summary)

@bp.route('/stats/books_over_time')
@login_required
def stats_books_over_time():
    range_type = request.args.get('range', 'months')
    data = get_books_over_time(current_user.id, range_type)
    return jsonify(data)

@bp.route('/stats/pages_over_time')
@login_required
def stats_pages_over_time():
    range_type = request.args.get('range', 'months')
    data = get_pages_over_time(current_user.id, range_type)
    return jsonify(data)

@bp.route('/stats/genres')
@login_required
def stats_genres():
    data = get_genre_stats(current_user.id)
    return jsonify(data)

@bp.route('/stats/statuses')
@login_required
def stats_statuses():
    data = get_status_stats(current_user.id)
    return jsonify(data)

@bp.route('/stats/authors')
@login_required
def stats_authors():
    data = get_author_stats(current_user.id)
    return jsonify(data)
