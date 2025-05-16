import unittest
from werkzeug.security import generate_password_hash
from app import create_app, db
from config import TestingConfig
from app.models import User, UserBook, Book, BookShare
from app.utils import (
    validate_registration_form, register_user, validate_login_form,
    get_all_usernames, get_user_library_books, get_user_books,
    add_book_to_library, delete_book_from_library, share_book_with_user,
    get_community_feed, get_stats_summary
)

class DummyForm:
    def __init__(self, username, email, password, confirm_password):
        self.username = type('obj', (object,), {'data': username})()
        self.email = type('obj', (object,), {'data': email})()
        self.password = type('obj', (object,), {'data': password})()
        self.confirm_password = type('obj', (object,), {'data': confirm_password})()

class UtilsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestingConfig)
        self.app_ctx = self.app.app_context()
        self.app_ctx.push()
        db.create_all()
        self.user = User(username="testuser", email="test@example.com")
        self.user.password = generate_password_hash("Password1")
        db.session.add(self.user)
        db.session.commit()
        self.user_id = self.user.id

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_ctx.pop()

    def test_validate_registration_form_valid(self):
        form = DummyForm("newuser", "new@example.com", "Password1", "Password1")
        valid, errors = validate_registration_form(form)
        self.assertTrue(valid)
        self.assertEqual(errors, {})

    def test_validate_registration_form_invalid(self):
        form = DummyForm("", "bademail", "pass", "notmatching")
        valid, errors = validate_registration_form(form)
        self.assertFalse(valid)
        self.assertIn('username', errors)
        self.assertIn('email', errors)
        self.assertIn('password', errors)
        self.assertIn('confirm_password', errors)

    def test_register_user(self):
        form = DummyForm("reguser", "reg@example.com", "Password1", "Password1")
        user = register_user(form)
        self.assertIsNotNone(User.query.filter_by(username="reguser").first())
        self.assertEqual(user.email, "reg@example.com")

    def test_validate_login_form_success(self):
        class LoginForm:
            username = type('obj', (object,), {'data': "testuser"})()
            password = type('obj', (object,), {'data': "Password1"})()
        valid, user = validate_login_form(LoginForm)
        self.assertTrue(valid)
        self.assertEqual(user.username, "testuser")

    def test_validate_login_form_fail(self):
        class LoginForm:
            username = type('obj', (object,), {'data': "testuser"})()
            password = type('obj', (object,), {'data': "WrongPass"})()
        valid, user = validate_login_form(LoginForm)
        self.assertFalse(valid)
        self.assertIsNone(user)

    def test_get_all_usernames(self):
        user2 = User(username="otheruser", email="other@example.com")
        user2.password = generate_password_hash("Password2")
        db.session.add(user2)
        db.session.commit()
        usernames = get_all_usernames(self.user_id)
        self.assertIn("otheruser", usernames)
        self.assertNotIn("testuser", usernames)

    def test_add_and_get_user_library_books(self):
        # Add a book
        data = {
            "google_id": "gid1",
            "title": "Book1",
            "author": "Author1",
            "description": "Desc",
            "cover_url": "url",
            "status": "wishlist",
            "genre": "Fiction",
            "page_count": 100
        }
        add_book_to_library(self.user_id, data)
        books = get_user_library_books(self.user_id)
        self.assertEqual(len(books), 1)
        self.assertEqual(books[0].book.title, "Book1")

    def test_delete_book_from_library(self):
        # Add a book
        data = {
            "google_id": "gid2",
            "title": "Book2",
            "author": "Author2",
            "description": "Desc2",
            "cover_url": "url2",
            "status": "wishlist",
            "genre": "Fiction",
            "page_count": 120
        }
        add_book_to_library(self.user_id, data)
        books = get_user_library_books(self.user_id)
        user_book_id = books[0].id
        result, status = delete_book_from_library(self.user_id, user_book_id)
        self.assertEqual(status, 200)
        books = get_user_library_books(self.user_id)
        self.assertEqual(len(books), 0)

    def test_share_book_with_user(self):
        # Add second user and a book
        user2 = User(username="shareuser", email="share@example.com")
        user2.password = generate_password_hash("Password2")
        db.session.add(user2)
        db.session.commit()
        data = {
            "google_id": "gid3",
            "title": "Book3",
            "author": "Author3",
            "description": "Desc3",
            "cover_url": "url3",
            "status": "wishlist",
            "genre": "Fiction",
            "page_count": 150
        }
        add_book_to_library(self.user_id, data)
        user_book = get_user_library_books(self.user_id)[0]
        result, code = share_book_with_user(self.user_id, user_book.id, "shareuser", "wishlist")
        self.assertTrue(result['success'])
        self.assertEqual(code, 200)

    def test_stats_summary(self):
        data = {
            "google_id": "gid4",
            "title": "Book4",
            "author": "Author4",
            "description": "Desc4",
            "cover_url": "url4",
            "status": "completed",
            "genre": "Nonfiction",
            "page_count": 123
        }
        add_book_to_library(self.user_id, data)
        summary = get_stats_summary(self.user_id)
        self.assertEqual(summary['total_books_read'], 1)
        self.assertEqual(summary['total_pages_read'], 123)
        self.assertEqual(summary['favorite_genre'], "Nonfiction")
        self.assertEqual(summary['most_read_author'], "Author4")

if __name__ == '__main__':
    unittest.main()
