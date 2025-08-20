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
    colleges = College.query.all()
    departments = Department.query.all()
    subjects = Subject.query.all()

    if not colleges or not departments or not subjects:
        click.echo("❌ Required seed data missing. Please seed colleges, departments, and subjects first.")
        return

    university_ims = []
    for i, college in enumerate(colleges):
        for j, dept in enumerate(departments):
            for year in range(1, 3):
                subj_idx = (i * 2 + j + year) % len(subjects)
                university_ims.append({
                    "college_id": college.id,
                    "department_id": dept.id,
                    "subject_id": subjects[subj_idx].id,
                    "year_level": year
                })

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