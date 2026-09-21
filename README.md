# Spend Tracker API

A simple expense tracking application built with Django and Django REST Framework.

## Features

- JWT authentication
- User registration and login
- Create and list expenses
- Category-based expenses
- Filter expenses by category and date range
- Monthly spending summary
- Category spending insights for increases above 20%
- Input validation and error handling
- Automated API tests
- Minimal responsive frontend

## Tech Stack

- Python
- Django
- Django REST Framework
- SimpleJWT
- SQLite
- django-filter
- HTML
- CSS
- JavaScript

## API Endpoints

POST   /api/auth/register/
POST   /api/auth/login/
POST   /api/auth/refresh/

GET    /api/categories/

POST   /api/expenses/
GET    /api/expenses/

GET    /api/summary/

## Running Locally

Create and activate a virtual environment:

python -m venv venv

Install dependencies:

pip install -r requirements.txt

Run migrations:

python manage.py migrate

Start the server:

python manage.py runserver

Then open the frontend in the browser.

## Testing

Run:

python manage.py test

## AI Usage

AI tools including ChatGPT and GitHub Copilot were used during development for implementation assistance, test creation, debugging, and reviewing possible approaches. I manually reviewed the generated changes, verified the functionality, and accepted changes only after understanding and testing them rather than blindly accepting AI-generated code.
