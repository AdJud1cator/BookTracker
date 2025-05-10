from app import db
from app.models import Book
new_book = Book(title="Test Book", author="Someone", rating=4.5)
db.session.add(new_book)
db.session.commit()
Book.query.filter_by(title="Test Book").first().rating
