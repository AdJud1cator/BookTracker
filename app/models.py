from . import db
from flask_login import UserMixin

# When you make any changes to the models.py file eg. adding a column to one of the models please open up a terminal in administrator then:
# cd path/to/booktracker
# flask db migrate -m "Describe the change"
# flask db upgrade
# This applies the schema changes to your app.db database


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=True)
    password = db.Column(db.String(128), nullable=False)
    books = db.relationship('UserBook', back_populates='user', cascade='all, delete-orphan')
    sent_shares = db.relationship('BookShare', foreign_keys='BookShare.from_user_id', back_populates='from_user')
    received_shares = db.relationship('BookShare', foreign_keys='BookShare.to_user_id', back_populates='to_user')

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(40), unique=True, nullable=True)
    title = db.Column(db.String(150), nullable=False)
    author = db.Column(db.String(150), nullable=False)
    genre = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    cover_url = db.Column(db.String(300), nullable=True)
    page_count = db.Column(db.Integer, nullable=True)
    #rating = db.Column(db.Float, nullable=True)
    userbooks = db.relationship('UserBook', back_populates='book', cascade='all, delete-orphan')
    shares = db.relationship('BookShare', back_populates='book', cascade='all, delete-orphan')

class UserBook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    status = db.Column(db.String(30), nullable=False)  # 'currently_reading', 'completed', 'wishlist'
    date_added = db.Column(db.DateTime, server_default=db.func.now())
    date_completed = db.Column(db.DateTime, nullable=True)  # For statistics

    user = db.relationship('User', back_populates='books')
    book = db.relationship('Book', back_populates='userbooks')

class BookShare(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    from_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    to_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    status = db.Column(db.String(30), nullable=False)  # status at the time of sharing
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

    from_user = db.relationship('User', foreign_keys=[from_user_id], back_populates='sent_shares')
    to_user = db.relationship('User', foreign_keys=[to_user_id], back_populates='received_shares')
    book = db.relationship('Book', back_populates='shares')
