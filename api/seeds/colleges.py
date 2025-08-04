import click
from api.extensions import db
from api.models.colleges import College
from flask.cli import with_appcontext
from datetime import datetime, UTC

@click.command("seed_colleges")
@with_appcontext
def seed_colleges():
    """Seed the database with initial colleges."""
    # Check if colleges already exist
    if College.query.first():
        click.echo("⚠️  Colleges already exist in database. Skipping seeding.")
        return
    
    current_time = datetime.now(UTC)
    admin_user = "system"  # Assuming this matches your user seeding
    
    colleges = [
        {
            "abbreviation": "CE",
            "name": "College of Engineering",
            "created_by": admin_user,
            "updated_by": admin_user,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "abbreviation": "COC",
            "name": "College of Communication",
            "created_by": admin_user,
            "updated_by": admin_user,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "abbreviation": "CCIS",
            "name": "College of Computer and Information Sciences",
            "created_by": admin_user,
            "updated_by": admin_user,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "abbreviation": "CAF",
            "name": "College of Accountancy and Finance",
            "created_by": admin_user,
            "updated_by": admin_user,
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "abbreviation": "CBA",
            "name": "College of Business Administration",
            "created_by": admin_user,
            "updated_by": admin_user,
            "created_at": current_time,
            "updated_at": current_time
        }
    ]

    try:
        # Create colleges
        for college_data in colleges:
            college = College(
                abbreviation=college_data["abbreviation"],
                name=college_data["name"],
                created_by=college_data["created_by"],
                updated_by=college_data["updated_by"]
            )
            db.session.add(college)
        
        db.session.commit()
        click.echo("✅ Successfully seeded colleges!")
    except Exception as e:
        db.session.rollback()
        click.echo(f"❌ Error seeding colleges: {str(e)}")

def register_commands(app):
    app.cli.add_command(seed_colleges)