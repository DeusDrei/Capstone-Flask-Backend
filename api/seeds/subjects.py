import click
from api.extensions import db
from api.models.subjects import Subject
from flask.cli import with_appcontext
from datetime import datetime, UTC

@click.command("seed_subjects")
@with_appcontext
def seed_subjects():
    """Seed the database with initial subjects."""
    if Subject.query.first():
        click.echo("⚠️  Subjects already exist in database. Skipping seeding.")
        return
    
    current_time = datetime.now(UTC)
    admin_user = "system"
    
    subjects = [
        {
            "code": "MATH101",
            "name": "Introduction to Calculus",
            "created_by": admin_user,
            "updated_by": admin_user
        },
        {
            "code": "CS101",
            "name": "Fundamentals of Computer Science",
            "created_by": admin_user,
            "updated_by": admin_user
        },
        {
            "code": "PHYS101",
            "name": "Basic Principles of Physics",
            "created_by": admin_user,
            "updated_by": admin_user
        },
        {
            "code": "ENG101",
            "name": "Introduction to English Composition",
            "created_by": admin_user,
            "updated_by": admin_user
        },
        {
            "code": "CHEM101",
            "name": "General Chemistry Fundamentals",
            "created_by": admin_user,
            "updated_by": admin_user
        }
    ]

    try:
        for subject_data in subjects:
            subject = Subject(
                code=subject_data["code"],
                name=subject_data["name"],
                created_by=subject_data["created_by"],
                updated_by=subject_data["updated_by"]
            )
            db.session.add(subject)
        
        db.session.commit()
        click.echo("✅ Successfully seeded subjects!")
    except Exception as e:
        db.session.rollback()
        click.echo(f"❌ Error seeding subjects: {str(e)}")

def register_commands(app):
    app.cli.add_command(seed_subjects)