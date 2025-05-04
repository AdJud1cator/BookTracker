from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user

from app import app, db
from app.models import Book, User

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            login_user(user)
            flash("Logged in successfully.")
            return redirect(url_for('dashboard'))
        flash("Invalid credentials.")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        #email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash("Passwords do not match.")
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash("Username already exists.")
            return redirect(url_for('register'))

        user = User(username=username, password = password)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("Registered successfully. Please log in.")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.")
    return redirect(url_for('login'))
 
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template("Dashboard.html")

@app.route('/library')
@login_required
def library():
    books = Book.query.all()
    return render_template("Library.html", books=books)


@app.route('/add_book', methods=['GET', 'POST'])
@login_required
def add_book():
    title = request.form.get("title")
    author = request.form.get("author")
    genre = request.form.get("genre")
    description = request.form.get("description")
    if title and author:
        db.session.add(Book(
            title=title,
            author=author,
            genre=genre,
            description=description
        ))
        db.session.commit()

    if request.method == "POST":
        return redirect(url_for('library'))
    return render_template("AddBook.html")

@app.route('/statistics')
@login_required
def statistics():
    return render_template("Statistics.html")

@app.route('/share', methods=['GET', 'POST'])
@login_required
def share():
    if request.method == "POST":
        return redirect(url_for('dashboard'))
    return render_template("Share.html")

@app.route('/details')
@login_required
def details():
    return render_template("Details.html")

@app.route('/404')
def error404():
    return render_template("404.html")