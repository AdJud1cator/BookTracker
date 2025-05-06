from flask import redirect, render_template, request, url_for
from app import app

@app.route('/', methods=['GET', 'POST'])
def landing():
    return render_template("Landing.html")

@app.route('/privacy')
def privacy():
    return render_template("Privacy.html")

@app.route('/terms')
def terms():
    return render_template("Terms.html")

@app.route('/faq')
def faq():
    return render_template("FAQ.html")

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    return render_template("forgot.html")

@app.route('/login', methods=['GET', 'POST'])
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
    return render_template("Library.html")

@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == "POST":
        return redirect(url_for('dashboard'))
    return render_template("AddBook.html")

@app.route('/statistics')
def statistics():
    return render_template("Statistics.html")

@app.route('/share', methods=['GET', 'POST'])
def share():
    if request.method == "POST":
        return redirect(url_for('dashboard'))
    return render_template("share.html")

@app.route('/details')
def details():
    return render_template("Details.html")

@app.route('/404')
def error404():
    return render_template("404.html")