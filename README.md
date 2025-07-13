# DTEAM - Django Developer Practical Test

Welcome! This test will help us see how you structure a Django project, work with various tools, and handle common tasks in web development. Follow the instructions step by step. Good luck!

## Requirements:
Follow PEP 8 and other style guidelines, use clear and concise commit messages and docstrings where needed, structure your project for readability and maintainability, optimize database access using Django's built-in methods, and provide enough details in your README.

## Version Control System
1. Create a **public GitHub repository** for this practical test, for example: `DTEAM-django-practical-test`.
2. Put the text of this test (all instructions) into `README.md`.
3. For each task, create a **separate branch** (for example, `tasks/task-1`, `tasks/task-2`, etc.).
4. When you finish each task, **merge** that branch back into `main` but **do not delete** the original task branch.

## Python Virtual Environment
1. Use **pyenv** to manage the Python version. Create a file named `.python-version` in your repository to store the exact Python version.
2. Use **Poetry** to manage and store project dependencies. This will create a `pyproject.toml` file.
3. Update your `README.md` with clear instructions on how to set up and use pyenv and Poetry for this project.

## Setup Instructions

### Prerequisites
- Python 3.13+ (managed with pyenv or pyenv-win on Windows)
- Poetry for dependency management
- Git

### Installation

#### Step 1: Python Version Management

**On Windows (using pyenv-win):**
```bash
# Install pyenv-win if not already installed
# See: https://github.com/pyenv-win/pyenv-win#installation

# Install Python 3.13
pyenv install 3.13.0
pyenv local 3.13.0
```

**On macOS/Linux (using pyenv):**
```bash
# Install pyenv if not already installed
# See: https://github.com/pyenv/pyenv#installation

# Install Python 3.13
pyenv install 3.13.0
pyenv local 3.13.0
```

**Alternative: Use existing Python 3.13**
If you already have Python 3.13 installed, just create the version file:
```bash
echo 3.13 > .python-version
```

#### Step 2: Poetry Setup
```bash
# Install Poetry if not already installed
# See: https://python-poetry.org/docs/#installation

# Install project dependencies
poetry install

# Activate the virtual environment
poetry shell
```

#### Step 3: Django Setup
```bash
# Run database migrations
python manage.py migrate

# Load initial sample data
python manage.py loaddata initial_data

# Create a superuser (optional, for admin access)
python manage.py createsuperuser

# Run the development server
python manage.py runserver
```

#### Step 4: Access the Application
- **Homepage (CV List):** http://127.0.0.1:8000/
- **Admin Interface:** http://127.0.0.1:8000/admin/
- **Sample CV Detail:** http://127.0.0.1:8000/cv/1/

## Project Structure

```
CVProject/
├── .python-version          # Python version specification
├── pyproject.toml           # Poetry dependencies
├── manage.py               # Django management script
├── db.sqlite3              # SQLite database (created after migrations)
├── CVProject/              # Main project directory
│   ├── __init__.py
│   ├── settings.py         # Django settings
│   ├── urls.py            # Main URL configuration
│   └── wsgi.py            # WSGI configuration
├── main/                   # CV management app
│   ├── __init__.py
│   ├── admin.py           # Admin interface configuration
│   ├── apps.py            # App configuration
│   ├── models.py          # Database models (CV, Skill, Project, Contact)
│   ├── views.py           # View logic
│   ├── urls.py            # App URL configuration
│   ├── tests.py           # Test cases
│   ├── fixtures/          # Sample data
│   │   └── initial_data.json
│   └── migrations/        # Database migrations
├── templates/              # HTML templates
│   ├── base.html          # Base template
│   └── main/
│       ├── cv_list.html   # CV list page
│       └── cv_detail.html # CV detail page
└── static/                # Static files (CSS, JS, images)
```

## Features Implemented (Task 1)

### ✅ Django Fundamentals
- [x] Django project `CVProject` created
- [x] Django app `main` created  
- [x] SQLite database configuration
- [x] CV model with related models (Skills, Projects, Contacts)
- [x] Sample data loaded via fixtures
- [x] List page view with efficient database queries
- [x] Detail page view with optimized data retrieval
- [x] Bootstrap-styled templates
- [x] Comprehensive test coverage

### Models
- **CV**: Core model with personal information (firstname, lastname, email, phone, bio)
- **Skill**: Skills with proficiency levels (beginner, intermediate, advanced, expert)
- **Project**: Projects with technologies, dates, and URLs
- **Contact**: Contact information (LinkedIn, GitHub, Website, Twitter, etc.)

### Views
- **CVListView**: Displays paginated list of all CVs with preview information
- **CVDetailView**: Shows complete CV information including skills, projects, and contacts

### Templates
- **Responsive design** using Bootstrap 5
- **Clean, professional styling** with Font Awesome icons
- **Optimized for readability** with proper typography and spacing

## Loading Sample Data

The project includes sample data that can be loaded using Django fixtures:

```bash
# Load the sample CV data
python manage.py loaddata initial_data
```

This will create:
- 1 sample CV (John Doe)
- 6 skills (Python, Django, React, PostgreSQL, Docker, AWS)
- 3 projects (E-Commerce Platform, Task Management API, Data Analytics Dashboard)
- 3 contact methods (LinkedIn, GitHub, Website)

## Running Tests

Run the comprehensive test suite:

```bash
# Run all tests
python manage.py test

# Run tests with verbose output
python manage.py test --verbosity=2

# Run specific test classes
python manage.py test main.tests.CVModelTest
python manage.py test main.tests.CVListViewTest
python manage.py test main.tests.CVDetailViewTest
```

### Test Coverage
- **Model tests**: CV, Skill, Project, Contact models
- **View tests**: List and detail views with various scenarios
- **URL tests**: Proper URL resolution and routing
- **Template tests**: Correct template usage and context
- **Database optimization tests**: Query efficiency verification

## Development Guidelines

### Code Style
- Follow **PEP 8** style guidelines
- Use **clear, descriptive variable names**
- Add **docstrings** to all classes and functions
- Write **meaningful commit messages**

### Database Optimization
- Use `select_related()` and `prefetch_related()` for efficient queries
- Avoid N+1 query problems
- Add database indexes where appropriate

### Testing
- Write tests for all new features
- Maintain high test coverage
- Test both positive and negative scenarios
- Include edge cases in testing

## Task Progress

- [x] **Task 1**: Django Fundamentals ✅ COMPLETED
- [ ] **Task 2**: PDF Generation Basics
- [ ] **Task 3**: REST API Fundamentals  
- [ ] **Task 4**: Middleware & Request Logging
- [ ] **Task 5**: Template Context Processors
- [ ] **Task 6**: Docker Basics
- [ ] **Task 7**: Celery Basics
- [ ] **Task 8**: OpenAI Basics
- [ ] **Task 9**: Deployment

## Next Steps

After completing Task 1, proceed to Task 2 (PDF Generation Basics) by creating a new branch:

```bash
git add .
git commit -m "Complete Task 1: Django Fundamentals"
git checkout main
git merge tasks/task-1
git checkout -b tasks/task-2
```

---

**Thank you for reviewing Task 1!** The foundation is now set with a solid Django application featuring proper models, views, templates, and comprehensive testing.