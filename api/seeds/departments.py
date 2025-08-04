import click
from api.extensions import db
from api.models.departments import Department
from flask.cli import with_appcontext
from datetime import datetime, UTC

@click.command("seed_departments")
@with_appcontext
def seed_departments():
    """Seed the database with initial departments."""
    # Check if departments already exist
    if Department.query.first():
        click.echo("⚠️  Departments already exist in database. Skipping seeding.")
        return
    
    current_time = datetime.now(UTC)
    admin_user = "system"  # Assuming this matches your user seeding
    
    departments = [
        {
            "abbreviation": "BSIT",
            "name": "Bachelor of Science in Information Technology",
            "created_by": admin_user,
            "updated_by": admin_user,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "abbreviation": "BSCS",
            "name": "Bachelor of Science in Computer Science",
            "created_by": admin_user,
            "updated_by": admin_user,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "abbreviation": "BSA",
            "name": "Bachelor of Science in Accountancy",
            "created_by": admin_user,
            "updated_by": admin_user,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "abbreviation": "BSID",
            "name": "Bachelor of Science in Interior Design",
            "created_by": admin_user,
            "updated_by": admin_user,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "abbreviation": "BSCE",
            "name": "Bachelor of Science in Civil Engineering",
            "created_by": admin_user,
            "updated_by": admin_user,
            "created_at": current_time,
            "updated_at": current_time
        }
    ]

    try:
        # Create departments
        for dept_data in departments:
            department = Department(
                abbreviation=dept_data["abbreviation"],
                name=dept_data["name"],
                created_by=dept_data["created_by"],
                updated_by=dept_data["updated_by"]
            )
            db.session.add(department)
        
        db.session.commit()
        click.echo("✅ Successfully seeded departments!")
    except Exception as e:
        db.session.rollback()
        click.echo(f"❌ Error seeding departments: {str(e)}")

def register_commands(app):
    app.cli.add_command(seed_departments)