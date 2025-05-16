import time
import unittest
import multiprocessing

from app.models import User
from app import create_app, db
from config import TestingConfig
from werkzeug.security import generate_password_hash

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

localHost = "http://127.0.0.1:5000/"

class SystemTests(unittest.TestCase):

    def setUp(self):
        testApplication = create_app(TestingConfig)
        self.app_ctx = testApplication.app_context()
        self.app_ctx.push()
        db.create_all()

        self.server_thread = multiprocessing.Process(target=testApplication.run)
        self.server_thread.start()

        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        self.driver = webdriver.Chrome(options=options)

        return super().setUp()
    
    def test_user_registration_redirects_to_login(self):
        self.driver.get(localHost + "register")
        # Fill the registration form
        self.driver.find_element(By.ID, "username").send_keys("testuser1")
        self.driver.find_element(By.ID, "email").send_keys("testuser1@example.com")
        self.driver.find_element(By.ID, "password").send_keys("Testpass1")
        self.driver.find_element(By.ID, "confirm_password").send_keys("Testpass1")
        self.driver.find_element(By.ID, "button[type='submit']").click()

        # Wait for redirect to login page
        WebDriverWait(self.driver, 10).until(
            expected_conditions.url_contains("/login")
        )
        # Assert we're on the login page
        self.assertIn("/login", self.driver.current_url)

    def test_user_login_redirects_to_dashboard(self):
        # First, create a user directly in the database
        hashed_pw = generate_password_hash("Testpass1")
        user = User(username="testuser2", email="testuser2@example.com", password=hashed_pw)
        db.session.add(user)
        db.session.commit()

        self.driver.get(localHost + "login")
        self.driver.find_element(By.ID, "username").send_keys("testuser2")
        self.driver.find_element(By.ID, "password").send_keys("Testpass1")
        self.driver.find_element(By.ID, "submit").click()

        # Wait for redirect to dashboard
        WebDriverWait(self.driver, 10).until(
            expected_conditions.url_contains("/dashboard")
        )
        self.assertIn("/dashboard", self.driver.current_url)
        # Optionally, check for dashboard content
        self.assertTrue("dashboard" in self.driver.page_source.lower())

    def test_registration_with_existing_username(self):
        # Create user directly in the database
        hashed_pw = generate_password_hash("Testpass1")
        user = User(username="existinguser", email="existing@example.com", password=hashed_pw)
        db.session.add(user)
        db.session.commit()

        self.driver.get(localHost + "register")
        self.driver.find_element(By.ID, "username").send_keys("existinguser")
        self.driver.find_element(By.ID, "email").send_keys("another@example.com")
        self.driver.find_element(By.ID, "password").send_keys("Testpass1")
        self.driver.find_element(By.ID, "confirm_password").send_keys("Testpass1")
        self.driver.find_element(By.ID, "submit").click()

        # Should stay on register page and show error
        WebDriverWait(self.driver, 5).until(
            expected_conditions.url_contains("/register")
        )
        self.assertIn("/register", self.driver.current_url)
        self.assertTrue("Username already exists" in self.driver.page_source)

    def test_registration_with_mismatched_passwords(self):
        self.driver.get(localHost + "register")
        self.driver.find_element(By.ID, "username").send_keys("mismatchuser")
        self.driver.find_element(By.ID, "email").send_keys("mismatch@example.com")
        self.driver.find_element(By.ID, "password").send_keys("Testpass1")
        self.driver.find_element(By.ID, "confirm_password").send_keys("Wrongpass1")
        self.driver.find_element(By.ID, "submit").click()

        WebDriverWait(self.driver, 5).until(
            expected_conditions.url_contains("/register")
        )
        self.assertIn("/register", self.driver.current_url)
        self.assertTrue("Passwords do not match" in self.driver.page_source)

    def test_dashboard_requires_login_redirect(self):
        # Ensure not logged in
        self.driver.get(localHost + "logout")
        self.driver.get(localHost + "dashboard")
        WebDriverWait(self.driver, 5).until(
            expected_conditions.url_contains("/login")
        )
        self.assertIn("/login", self.driver.current_url)

    def test_logout_redirects_to_homepage(self):
        # Register and login first
        self.driver.get(localHost + "register")
        self.driver.find_element(By.ID, "username").send_keys("logoutuser")
        self.driver.find_element(By.ID, "email").send_keys("logoutuser@example.com")
        self.driver.find_element(By.ID, "password").send_keys("Testpass1")
        self.driver.find_element(By.ID, "confirm_password").send_keys("Testpass1")
        self.driver.find_element(By.ID, "submit").click()
        WebDriverWait(self.driver, 5).until(
            expected_conditions.url_contains("/login")
        )
        self.driver.get(localHost + "login")
        self.driver.find_element(By.ID, "username").send_keys("logoutuser")
        self.driver.find_element(By.ID, "password").send_keys("Testpass1")
        self.driver.find_element(By.ID, "submit").click()
        WebDriverWait(self.driver, 5).until(
            expected_conditions.url_contains("/dashboard")
        )
        # Now logout
        self.driver.get(localHost + "logout")
        WebDriverWait(self.driver, 5).until(
            expected_conditions.url_to_be(localHost)
        )
        self.assertEqual(self.driver.current_url, localHost)
        self.assertTrue("You have been logged out" in self.driver.page_source)

    def tearDown(self):
        self.server_thread.terminate()
        self.driver.close()
        db.session.remove()
        db.drop_all()
        self.app_ctx.pop()
        return super().tearDown()