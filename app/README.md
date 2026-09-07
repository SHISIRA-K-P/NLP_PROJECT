# Automated Review Rating System

## Project Description

A Django-based automated review rating system.

## Technologies

- Python
- Django
- Django REST Framework
- Pandas
- NumPy
- Scikit-learn

## Project Structure

- data - Dataset files
- notebooks - Jupyter notebooks
- models - Machine learning models
- app - Django application
- frontend - Frontend application

## Setup

Create virtual environment:

python -m venv .venv

Activate:

.venv\Scripts\Activate.ps1

Install dependencies:

pip install -r requirements.txt

Run Django:

cd app
python manage.py runserver

Get-Content requirements.txt
python app\manage.py migrate
python app\manage.py runserver

npm run dev