# Introduction
This project aims to create a solid boilerplate that can be reused for creating API applications with Flask. It boasts a solid selection of straightforward dependencies and a modern dependency management with Poetry.

### Features
- Login and Registration
- JWT Authentication and Middleware for API routes

## Poetry Guide
### Install Poetry
`pip install poetry`

### Ensure that the virtual environment is created inside the project directory
`poetry config virtualenvs.in-project true`

### Initialize a new Poetry project
`poetry init`

### Install dependencies
`poetry add flask flask-sqlalchemy`

### Install dependencies from poetry.lock
`poetry install --no-root`

## Unittest
### Running all unittests
`python -m unittest`

## Migrations with Flask-Migrate
### Create a migrations folder
`flask db init`

### Generate a new migrations script saved in /migrations/versions/
`flask db migrate -m "Migration message..."`

### Apply migration scripts to the actual connected database
`flask db upgrade`

### Revert to a previous migration (rollback)
`flask db downgrade`                - Downgrade to the previous migration
`flask db downgrade -1`             - Downgrade 1 step or 1 version
`flask db downgrade <version_id>`   - Downgrade to a specific version or migration

## Dependencies
1. Flask - Python server of choice
2. Flask_Smorest - Used to generate Swagger documentation
3. Flask-Marshmallow - Serializer
4. Apispec - Required for integration between mashmallow and flask_smorest
5. Poetry - Dependency and project management
6. Unittest - Module for creating and running automated tests for integrated and unit testing
7. Flask-Migrate - Dependency for database migrations

## Project Structure Guide
```
project-root/
|
|-- api/
|   |-- __init__.py
|   |-- config.py           // Mostly contains all fetching of environment variables
|   |-- create_app.py
|   |-- middleware.py
|   |-- extensions.py       // Instantiates other dependencies to be used like SQLAlchemy or Migrate
|   |-- models/             // Contains the database representations of each entity
|   |   |--__init__.py
|   |
|   |-- routes/             // Contains the routes that handle HTTP requests and responses
|   |   |--__init__.py
|   |
|   |-- schemas/            // Contains the schemas that handle serialization and input validation
|   |   |--__init__.py
|   |
|   |-- services/           // Contains the functions that provide additional functionality like email
|   |   |--__init__.py
|
|-- migrations/
|
|-- tests/
|   |-- __init__.py
|
|-- .env
|-- .env.example
|-- .gitignore
|-- app.py
|-- poetry.toml
|-- README.md
```
