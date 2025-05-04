from flask import Blueprint, render_template, request, redirect, url_for
from .models import Book
from . import db
from app import app

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        return redirect(url_for('dashboard'))
    return render_template("Login.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        return redirect(url_for('login'))
    return render_template("Register.html")

@app.route('/dashboard')
def dashboard():
    return render_template("Dashboard.html")

@app.route('/library')
def library():
    books = Book.query.all()
    return render_template("Library.html", books=books)


@app.route('/add_book', methods=['GET', 'POST'])
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
def statistics():
    return render_template("Statistics.html")

@app.route('/share', methods=['GET', 'POST'])
def share():
    if request.method == "POST":
        return redirect(url_for('dashboard'))
    return render_template("Share.html")

@app.route('/details')
def details():
    return render_template("Details.html")

@app.route('/404')
def error404():
    return render_template("404.html")