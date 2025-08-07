import click
from api.extensions import db
from api.models.universityims import UniversityIM
from api.models.colleges import College
from api.models.departments import Department
from api.models.subjects import Subject
from flask.cli import with_appcontext

@click.command("seed_universityims")
@with_appcontext
def seed_universityims():
    """Seed the database with initial university IM records."""
    if UniversityIM.query.first():
        click.echo("⚠️  University IM records already exist in database. Skipping seeding.")
        return
    
    # Ensure required foreign key data exists
    college = College.query.filter_by(abbreviation="CCIS").first()
    dept = Department.query.filter_by(abbreviation="BSIT").first()
    subjects = Subject.query.limit(5).all()
    
    if not college or not dept or not subjects:
        click.echo("❌ Required seed data missing. Please seed colleges, departments, and subjects first.")
        return
    
    university_ims = [
        {
            "college_id": college.id,
            "department_id": dept.id,
            "subject_id": subjects[0].id,
            "year_level": 1
        },
        {
            "college_id": college.id,
            "department_id": dept.id,
            "subject_id": subjects[1].id,
            "year_level": 1
        },
        {
            "college_id": college.id,
            "department_id": dept.id,
            "subject_id": subjects[2].id,
            "year_level": 2
        },
        {
            "college_id": college.id,
            "department_id": dept.id,
            "subject_id": subjects[3].id,
            "year_level": 2
        },
        {
            "college_id": college.id,
            "department_id": dept.id,
            "subject_id": subjects[4].id,
            "year_level": 3
        }
    ]

    try:
        for im_data in university_ims:
            university_im = UniversityIM(
                college_id=im_data["college_id"],
                department_id=im_data["department_id"],
                subject_id=im_data["subject_id"],
                year_level=im_data["year_level"]
            )
            db.session.add(university_im)
        
        db.session.commit()
        click.echo("✅ Successfully seeded university IM records!")
    except Exception as e:
        db.session.rollback()
        click.echo(f"❌ Error seeding university IM records: {str(e)}")

def register_commands(app):
    app.cli.add_command(seed_universityims)