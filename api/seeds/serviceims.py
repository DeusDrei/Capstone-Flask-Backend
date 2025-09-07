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

    # Map college abbreviation to its ID
    college_map = {c.abbreviation: c.id for c in colleges}

    # Map subject code to correct college abbreviation based on comments in subjects.py
    subject_college_map = {
        # CAF
        "ACC101": "CAF", "ACC201": "CAF", "FIN101": "CAF",
        # CADBE
        "ARCH101": "CADBE", "ID101": "CADBE", "ENVP101": "CADBE",
        # CAL
        "ENG201": "CAL", "FIL101": "CAL", "LIT201": "CAL",
        # CBA
        "HRM101": "CBA", "MKT101": "CBA", "ENT101": "CBA",
        # COC
        "ADV101": "COC", "BROAD101": "COC", "JOUR101": "COC",
        # CCIS
        "CS101": "CCIS", "IT101": "CCIS", "INTE30033": "CCIS",
        # COED
        "EDM101": "COED", "LIB101": "COED",
        # CE
        "CIV101": "CE", "MECH101": "CE",
        # CHK
        "PE101": "CHK",
        # CL
        "LAW101": "CL",
        # CPSPA
        "PA101": "CPSPA",
        # CSSD
        "SOC101": "CSSD",
        # CS
        "BIO101": "CS", "CHEM101": "CS", "MATH101": "CS",
        # CTHTM
        "HM101": "CTHTM", "TM101": "CTHTM", "TRM101": "CTHTM"
    }

    # Assign each subject to its correct college
    service_ims = []
    for subj in subjects:
        college_abbr = subject_college_map.get(subj.code)
        college_id = college_map.get(college_abbr)
        if college_id:
            service_ims.append({
                "college_id": college_id,
                "subject_id": subj.id
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