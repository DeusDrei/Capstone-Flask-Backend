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

    # Build a mapping of college_id to departments
    from random import choice, randint
    college_departments = {}
    for dept in departments:
        college_departments.setdefault(dept.college_id, []).append(dept)

    university_ims = []
    for subj in subjects:
        college_abbr = subject_college_map.get(subj.code)
        college_id = college_map.get(college_abbr)
        if college_id:
            # Pick a department within the same college
            dept_list = college_departments.get(college_id, [])
            department_id = choice(dept_list).id if dept_list else None
            year_level = randint(1, 4)
            university_ims.append({
                "college_id": college_id,
                "department_id": department_id,
                "subject_id": subj.id,
                "year_level": year_level
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