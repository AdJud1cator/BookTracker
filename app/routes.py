from flask import jsonify, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf.csrf import generate_csrf
from .models import User, UserBook, BookShare
from . import db
from werkzeug.security import generate_password_hash, check_password_hash
import re
from .forms import RegistrationForm, LoginForm
from .controllers import delete_book
from .blueprints import bp

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

# ----------------- Delete Book -----------------

@bp.route('/delete_book/<int:user_book_id>', methods=['DELETE'])
@login_required
def delete_book_route(user_book_id):
    return delete_book(user_book_id)

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
@bp.route('/faq')
def faq(): 
    if current_user.is_authenticated:
        base_template = "base_member.html"
    else:
        base_template = "base_anon.html"
    return render_template("faq.html", base_template=base_template)

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

    return render_template("dashboard.html", 
                           active_page = 'dashboard', 
                           has_feed = has_feed, 
                           has_currently_reading = has_currently_reading, 
                           currently_reading_books = currently_reading_books,
                           feed_items=feed_items
                           )

@bp.route('/explore')
@login_required
def explore(): return render_template("explore.html", active_page='explore')

@bp.route('/library')
@login_required
def library():
    user_books = UserBook.query.filter_by(user_id=current_user.id).all()
    return render_template('library.html', active_page='library', books=user_books)

@bp.route('/statistics')
@login_required
def statistics(): return render_template("statistics.html", active_page='statistics')
@bp.route('/community')
@login_required
def community(): return render_template("community.html", active_page='community')

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