# Content Management System (CMS) for Articles
   This Flask application provides a RESTful API for managing articles, including user authentication, article creation, retrieval, updating, and deletion.

## Features
- User registration and login with JWT authentication.
- Create, read, update, and delete articles.
- Retrieve articles by category.
- Get recently viewed articles by a user.
- Get user profile details.

## Architecture
- Uses Flask for the web framework.
- SQLAlchemy for ORM and database management.
- JWT for user authentication.
- SQLite as the database (can be replaced with any other database supported by SQLAlchemy).

## Database Schema
- User: Stores user information including username, email, and password.
- Article: Stores article information including title, content, category, and timestamps.

## Setup Instructions

### Local Development Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd Backend_assignment_Ocrolus
```

2. **Create virtual environment**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```
3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Run the application**
```bash
python app.py
```

The application will be available at `http://localhost:5000`
