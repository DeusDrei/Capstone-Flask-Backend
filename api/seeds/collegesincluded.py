import click
from api.extensions import db
from api.models.collegesincluded import CollegeIncluded
from api.models.colleges import College
from api.models.users import User
from flask.cli import with_appcontext
from datetime import datetime, UTC

@click.command("seed_collegesincluded")
@with_appcontext
def seed_collegesincluded():
    """Seed the database with college-user associations (1 user to multiple colleges)."""
    if CollegeIncluded.query.first():
        click.echo("⚠️  CollegeIncluded records already exist in database. Skipping seeding.")
        return
    
    # Get one admin user and multiple colleges
    user = User.query.filter(User.role.in_(['Technical Admin'])).first()
    colleges = College.query.limit(5).all() 
    
    if not user or not colleges:
        click.echo("❌ Required seed data missing. Please seed users and colleges first.")
        return

    current_time = datetime.now(UTC)
    
    college_included = [
        {
            "college_id": college.id,
            "user_id": user.id
        } for college in colleges  # Create association for each college
    ]

    try:
        for ci_data in college_included:
            # Skip if association already exists
            if not CollegeIncluded.query.filter_by(
                college_id=ci_data["college_id"],
                user_id=ci_data["user_id"]
            ).first():
                association = CollegeIncluded(
                    college_id=ci_data["college_id"],
                    user_id=ci_data["user_id"]
                )
                db.session.add(association)
        
        db.session.commit()
        click.echo(f"✅ Successfully seeded {len(college_included)} CollegeIncluded records for user {user.id}!")
    except Exception as e:
        db.session.rollback()
        click.echo(f"❌ Error seeding CollegeIncluded records: {str(e)}")

def register_commands(app):
    app.cli.add_command(seed_collegesincluded)