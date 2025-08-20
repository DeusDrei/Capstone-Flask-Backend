import click
from api.extensions import db
from api.models.serviceims import ServiceIM
from api.models.colleges import College
from api.models.subjects import Subject
from flask.cli import with_appcontext
from datetime import datetime, UTC

@click.command("seed_serviceims")
@with_appcontext
def seed_serviceims():
    """Seed the database with initial service IM records."""
    if ServiceIM.query.first():
        click.echo("⚠️  Service IM records already exist in database. Skipping seeding.")
        return
    
    # Ensure required foreign key data exists
    colleges = College.query.all()
    subjects = Subject.query.all()
    
    if not colleges or not subjects:
        click.echo("❌ Required seed data missing. Please seed colleges and subjects first.")
        return

    current_time = datetime.now(UTC)
    admin_user = "system"

    # Assign 2-3 unique subjects to each college for ServiceIMs
    service_ims = []
    for i, college in enumerate(colleges):
        for j in range(2):
            subj_idx = (i * 2 + j) % len(subjects)
            service_ims.append({
                "college_id": college.id,
                "subject_id": subjects[subj_idx].id
            })

    try:
        for im_data in service_ims:
            service_im = ServiceIM(
                college_id=im_data["college_id"],
                subject_id=im_data["subject_id"]
            )
            db.session.add(service_im)
        
        db.session.commit()
        click.echo("✅ Successfully seeded service IM records!")
    except Exception as e:
        db.session.rollback()
        click.echo(f"❌ Error seeding service IM records: {str(e)}")

def register_commands(app):
    app.cli.add_command(seed_serviceims)