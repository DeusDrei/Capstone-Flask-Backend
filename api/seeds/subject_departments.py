import click
from api.extensions import db
from api.models.subjects import Subject
from api.models.departments import Department
from api.models.subject_departments import SubjectDepartment
from flask.cli import with_appcontext

@click.command("seed_subject_departments")
@with_appcontext
def seed_subject_departments():
    """Seed the database with subject-department associations."""
    if SubjectDepartment.query.first():
        click.echo("⚠️  Subject-Department associations already exist. Skipping seeding.")
        return

    # CAF (college_id=1)
    caf_map = {
        "ACC101": "BSA",  # Fundamentals of Accounting → Accountancy
        "ACC201": "BSMA", # Intermediate Accounting → Management Accounting
        "FIN101": "BSBAFM", # Financial Management → Business Admin (Financial Management)
    }
    # CADBE (college_id=2)
    cadbe_map = {
        "ARCH101": "BS-ARCH",
        "ID101": "BSID",
        "ENVP101": "BSEP",
    }
    # CAL (college_id=3)
    cal_map = {
        "ENG201": "ABELS",
        "FIL101": "ABF",
        "LIT201": "ABLCS",
    }
    # CBA (college_id=4)
    cba_map = {
        "HRM101": "BSBAHRM",
        "MKT101": "BSBA-MM",
        "ENT101": "BSENTREP",
    }
    # COC (college_id=5)
    coc_map = {
        "ADV101": "BADPR",
        "BROAD101": "BABR",
        "JOUR101": "BAJ",
    }
    # CCIS (college_id=6)
    ccis_map = {
        "INTE30033": "BSCS",
        "CS101": "BSCS",
        "IT101": "BSIT",
    }
    # COED (college_id=7)
    coed_map = {
        "EDM101": "PhDEM",
        "LIB101": "BLIS",
    }
    # CE (college_id=8)
    ce_map = {
        "CIV101": "BSCE",
        "MECH101": "BSME",
    }
    # CHK (college_id=9)
    chk_map = {
        "PE101": "BPE",
    }
    # CL (college_id=10)
    cl_map = {
        "LAW101": "JD",
    }
    # CPSPA (college_id=11)
    cpspa_map = {
        "PA101": "BPA",
    }
    # CSSD (college_id=12)
    cssd_map = {
        "SOC101": "BAS",
    }
    # CS (college_id=13)
    cs_map = {
        "BIO101": "BSBIO",
        "CHEM101": "BSCHEM",
        "MATH101": "BSMATH",
    }
    # CTHTM (college_id=14)
    cthtm_map = {
        "HM101": "BSHM",
        "TM101": "BSTM",
        "TRM101": "BSTRM",
    }

    all_maps = [caf_map, cadbe_map, cal_map, cba_map, coc_map, ccis_map, coed_map, ce_map, chk_map, cl_map, cpspa_map, cssd_map, cs_map, cthtm_map]

    try:
        for mapping in all_maps:
            for subj_code, dept_abbr in mapping.items():
                subject = Subject.query.filter_by(code=subj_code).first()
                department = Department.query.filter_by(abbreviation=dept_abbr).first()
                if subject and department:
                    assoc = SubjectDepartment(subject_id=subject.id, department_id=department.id)
                    db.session.add(assoc)
                else:
                    click.echo(f"❌ Could not find subject {subj_code} or department {dept_abbr}")
        db.session.commit()
        click.echo("✅ Successfully seeded subject-department associations!")
    except Exception as e:
        db.session.rollback()
        click.echo(f"❌ Error seeding subject-department associations: {str(e)}")

def register_commands(app):
    app.cli.add_command(seed_subject_departments)