import click
from api.extensions import db
from api.models.users import User
from flask.cli import with_appcontext
from datetime import datetime, UTC
from werkzeug.security import generate_password_hash

@click.command("seed_users")
@with_appcontext
def seed_users():
    """Seed the database with initial admin users."""
    # Check if users already exist
    if User.query.first():
        click.echo("⚠️  Users already exist in database. Skipping seeding.")
        return

    # Generate password hashes
    password_hash = generate_password_hash("Admin@1234")
    
    users = [
        # Technical Admins
        {
            "role": "Technical Admin",
            "staff_id": "ADMIN001",
            "first_name": "System",
            "middle_name": "",
            "last_name": "Admin",
            "email": "admin@example.com",
            "password": password_hash,
            "phone_number": "+1234567890",
            "birth_date": datetime.strptime("1990-01-01", "%Y-%m-%d").date(),
            "created_by": "system",
            "updated_by": "system"
        },
        {
            "role": "Technical Admin",
            "staff_id": "ADMIN002",
            "first_name": "Alice",
            "middle_name": "Marie",
            "last_name": "Smith",
            "email": "alice.smith@example.com",
            "password": password_hash,
            "phone_number": "+1234567892",
            "birth_date": datetime.strptime("1985-05-10", "%Y-%m-%d").date(),
            "created_by": "system",
            "updated_by": "system"
        },
        # UTLDO Admins
        {
            "role": "UTLDO Admin",
            "staff_id": "UTLDO001",
            "first_name": "UTLDO",
            "middle_name": "",
            "last_name": "Admin",
            "email": "utldo@example.com",
            "password": password_hash,
            "phone_number": "+1234567891",
            "birth_date": datetime.strptime("1990-01-01", "%Y-%m-%d").date(),
            "created_by": "system",
            "updated_by": "system"
        },
        {
            "role": "UTLDO Admin",
            "staff_id": "UTLDO002",
            "first_name": "Bob",
            "middle_name": "Lee",
            "last_name": "Johnson",
            "email": "bob.johnson@example.com",
            "password": password_hash,
            "phone_number": "+1234567893",
            "birth_date": datetime.strptime("1988-03-15", "%Y-%m-%d").date(),
            "created_by": "system",
            "updated_by": "system"
        },
        # Faculty
        {
            "role": "Faculty",
            "staff_id": "FAC001",
            "first_name": "Carol",
            "middle_name": "Ann",
            "last_name": "Davis",
            "email": "carol.davis@example.com",
            "password": password_hash,
            "phone_number": "+1234567894",
            "birth_date": datetime.strptime("1992-07-20", "%Y-%m-%d").date(),
            "created_by": "system",
            "updated_by": "system"
        },
        {
            "role": "Faculty",
            "staff_id": "FAC002",
            "first_name": "David",
            "middle_name": "Paul",
            "last_name": "Miller",
            "email": "david.miller@example.com",
            "password": password_hash,
            "phone_number": "+1234567895",
            "birth_date": datetime.strptime("1991-11-30", "%Y-%m-%d").date(),
            "created_by": "system",
            "updated_by": "system"
        },
        # Evaluators
        {
            "role": "Evaluator",
            "staff_id": "EVAL001",
            "first_name": "Eve",
            "middle_name": "Grace",
            "last_name": "Wilson",
            "email": "eve.wilson@example.com",
            "password": password_hash,
            "phone_number": "+1234567896",
            "birth_date": datetime.strptime("1989-09-25", "%Y-%m-%d").date(),
            "created_by": "system",
            "updated_by": "system"
        },
        {
            "role": "Evaluator",
            "staff_id": "EVAL002",
            "first_name": "Frank",
            "middle_name": "Henry",
            "last_name": "Moore",
            "email": "frank.moore@example.com",
            "password": password_hash,
            "phone_number": "+1234567897",
            "birth_date": datetime.strptime("1993-12-12", "%Y-%m-%d").date(),
            "created_by": "system",
            "updated_by": "system"
        }
    ]

    try:
        # Create users one by one to let SQLAlchemy handle the enum conversion
        for user_data in users:
            user = User(**user_data)
            db.session.add(user)
        db.session.commit()
        click.echo("✅ Successfully seeded users!")
    except Exception as e:
        db.session.rollback()
        click.echo(f"❌ Error seeding users: {str(e)}")

def register_commands(app):
    app.cli.add_command(seed_users)