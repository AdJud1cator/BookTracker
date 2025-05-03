from flask import render_template
from app import app

@app.route('/')
def login():
    return render_template("Login.html")

@app.route('/register')
def register():
    return render_template("Register.html")

@app.route('/dashboard')
def dashboard():
    return render_template("Dashboard.html")

@app.route('/library')
def library():
    return render_template("Library.html")

@app.route('/add')
def add():
    return render_template("AddBook.html")

@app.route('/statistics')
def statistics():
    return render_template("Statistics.html")

@app.route('/share')
def share():
    return render_template("share.html")

@app.route('/details')
def details():
    return render_template("Details.html")

@app.route('/404')
def error404():
    return render_template("404.html")