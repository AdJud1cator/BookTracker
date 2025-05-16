# BookTracker: A Book Tracking Application

## Purpose and Overview

**BookTracker** is a Flask-based web application designed to help users track their reading journey. The app allows anyone to browse a curated collection of books without requiring an account. Registered users gain access to personalized features, including the ability to add and remove books from their personal library, categorized by reading status: **Currently Reading**, **Completed**, and **Wishlist**.

A unique community page lets users share their library and current reading status with others by searching for usernames. The application also provides a comprehensive **Statistics** page, displaying insightful analytics such as:

- Total Books Read  
- Total Pages Read  
- Favorite Genre  
- Most-Read Author  
- Longest and Shortest Book Read  
- Number of Books Shared  
- Books by Genre (Top 10) – Doughnut Chart  
- Books by Status – Doughnut Chart  
- Top Authors – Bar Chart  
- Books Read Over Time – Line Graph  
- Pages Read Over Time – Line Graph  

Additionally, **BookTracker** supports a **Dark Mode** theme to enhance user experience during low-light conditions, allowing users to switch between light and dark interfaces seamlessly.

---

## Group Members

| UWA ID   | Name            | GitHub Username |
|----------|-----------------|-----------------|
| 24590144 | Ahmed Jashim    | AdJud1cator     |
| 22969466 | Jake Spitteler  | Jakespitteler   |
| 24149342 | Dhava Adhi      | Technetium-95m  |
| 24502509 | Anthony Stewart | tony-stew       |

---

## How to Launch the Application

1. **Clone the repository**  
``` bash
git clone https://github.com/AdJud1cator/BookTracker.git
cd booktracker
```

2. **Install dependencies**  
Ensure you have Python 3.8+ and pip installed. Then run:
``` bash
pip install -r requirements.txt
```

3. **Set the environment variable for SECRET_KEY**  
On Linux/macOS:  
``` bash
export SECRET_KEY='your_secret_key_here'
```
On Windows (Command Prompt):  
``` shell
set SECRET_KEY=your_secret_key_here
```

4. **Run the application**  
``` bash
python run.py
```
The application will be available at [http://127.0.0.1:5000](http://127.0.0.1:5000).

---

## How to Run the Tests

1. **Ensure all dependencies are installed** (see above).  
2. **Run the unit tests**  
From the project root directory, execute:  
``` bash
python -m unittest test.unitTests
python -m unittest test.systemTests
```
This will automatically discover and run all tests in the `test/` directory.

---

Happy reading and tracking with **BookTracker**!  
For any issues, please open an issue on the [GitHub repository](https://github.com/AdJud1cator/BookTracker/issues).