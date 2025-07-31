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
        {
            "role": "Technical Admin", 
            "faculty_id": "ADMIN001",
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
            "role": "UTLDO Admin",  # Using string value instead of enum
            "faculty_id": "UTLDO001",
            "first_name": "UTLDO",
            "middle_name": "",
            "last_name": "Admin",
            "email": "utldo@example.com",
            "password": password_hash,
            "phone_number": "+1234567891",
            "birth_date": datetime.strptime("1990-01-01", "%Y-%m-%d").date(),
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