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
        # College of Accountancy and Finance (CAF)
        {"abbreviation": "BSA", "name": "Bachelor of Science in Accountancy", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "BSMA", "name": "Bachelor of Science in Management Accounting", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "BSBAFM", "name": "Bachelor of Science in Business Administration Major in Financial Management", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        # College of Architecture, Design and the Built Environment (CADBE)
        {"abbreviation": "BS-ARCH", "name": "Bachelor of Science in Architecture", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "BSID", "name": "Bachelor of Science in Interior Design", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "BSEP", "name": "Bachelor of Science in Environmental Planning", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        # College of Arts and Letters (CAL)
        {"abbreviation": "ABELS", "name": "Bachelor of Arts in English Language Studies", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "ABF", "name": "Bachelor of Arts in Filipinology", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "ABLCS", "name": "Bachelor of Arts in Literary and Cultural Studies", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "AB-PHILO", "name": "Bachelor of Arts in Philosophy", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "BPEA", "name": "Bachelor of Performing Arts major in Theater Arts", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        # College of Business Administration (CBA)
        {"abbreviation": "DBA", "name": "Doctor in Business Administration", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "MBA", "name": "Master in Business Administration", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "BSBAHRM", "name": "Bachelor of Science in Business Administration major in Human Resource Management", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "BSBA-MM", "name": "Bachelor of Science in Business Administration major in Marketing Management", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "BSENTREP", "name": "Bachelor of Science in Entrepreneurship", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "BSOA", "name": "Bachelor of Science in Office Administration", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        # College of Communication (COC)
        {"abbreviation": "BADPR", "name": "Bachelor in Advertising and Public Relations", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "BABR", "name": "Bachelor of Arts in Broadcasting", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "BACR", "name": "Bachelor of Arts in Communication Research", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "BAJ", "name": "Bachelor of Arts in Journalism", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        # College of Computer and Information Sciences (CCIS)
        {"abbreviation": "BSCS", "name": "Bachelor of Science in Computer Science", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "BSIT", "name": "Bachelor of Science in Information Technology", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        # College of Education (COED)
        {"abbreviation": "PhDEM", "name": "Doctor of Philosophy in Education Management", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "MAEM", "name": "Master of Arts in Education Management", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "MBE", "name": "Master in Business Education", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "MLIS", "name": "Master in Library and Information Science", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "MAELT", "name": "Master of Arts in English Language Teaching", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "MAEd-ME", "name": "Master of Arts in Education major in Mathematics Education", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "MAPES", "name": "Master of Arts in Physical Education and Sports", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "MAED-TCA", "name": "Master of Arts in Education major in Teaching in the Challenged Areas", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "PBDE", "name": "Post-Baccalaureate Diploma in Education", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "BTLEd-HE", "name": "Bachelor of Technology and Livelihood Education major in Home Economics", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "BTLEd-IA", "name": "Bachelor of Technology and Livelihood Education major in Industrial Arts", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "BTLEd-ICT", "name": "Bachelor of Technology and Livelihood Education major in Information and Communication Technology", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "BLIS", "name": "Bachelor of Library and Information Science", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "BSEd-ENG", "name": "Bachelor of Secondary Education major in English", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "BSEd-MATH", "name": "Bachelor of Secondary Education major in Mathematics", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "BSEd-SCI", "name": "Bachelor of Secondary Education major in Science", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "BSEd-FIL", "name": "Bachelor of Secondary Education major in Filipino", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "BSEd-SS", "name": "Bachelor of Secondary Education major in Social Studies", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "BEEd", "name": "Bachelor of Elementary Education", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "BECEd", "name": "Bachelor of Early Childhood Education", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        # College of Engineering (CE)
        {"abbreviation": "BSCE", "name": "Bachelor of Science in Civil Engineering", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "BSCpE", "name": "Bachelor of Science in Computer Engineering", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "BSEE", "name": "Bachelor of Science in Electrical Engineering", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "BSECE", "name": "Bachelor of Science in Electronics Engineering", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "BSIE", "name": "Bachelor of Science in Industrial Engineering", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "BSME", "name": "Bachelor of Science in Mechanical Engineering", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "BSRE", "name": "Bachelor of Science in Railway Engineering", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        # College of Human Kinetics (CHK)
        {"abbreviation": "BPE", "name": "Bachelor of Physical Education", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "BSESS", "name": "Bachelor of Science in Exercises and Sports", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        # College of Law (CL)
        {"abbreviation": "JD", "name": "Juris Doctor", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        # College of Political Science and Public Administration (CPSPA)
        {"abbreviation": "DPA", "name": "Doctor in Public Administration", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "MPA", "name": "Master in Public Administration", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "BPA", "name": "Bachelor of Public Administration", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "BAIS", "name": "Bachelor of Arts in International Studies", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "BAPE", "name": "Bachelor of Arts in Political Economy", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "BAPS", "name": "Bachelor of Arts in Political Science", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        # College of Social Sciences and Development (CSSD)
        {"abbreviation": "BAH", "name": "Bachelor of Arts in History", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "BAS", "name": "Bachelor of Arts in Sociology", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "BSC", "name": "Bachelor of Science in Cooperatives", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "BSE", "name": "Bachelor of Science in Economics", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "BSPSY", "name": "Bachelor of Science in Psychology", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        # College of Science (CS)
        {"abbreviation": "BSFT", "name": "Bachelor of Science Food Technology", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "BSAPMATH", "name": "Bachelor of Science in Applied Mathematics", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "BSBIO", "name": "Bachelor of Science in Biology", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "BSCHEM", "name": "Bachelor of Science in Chemistry", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "BSMATH", "name": "Bachelor of Science in Mathematics", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "BSND", "name": "Bachelor of Science in Nutrition and Dietetics", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "BSPHY", "name": "Bachelor of Science in Physics", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "BSSTAT", "name": "Bachelor of Science in Statistics", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        # College of Tourism, Hospitality and Transportation Management (CTHTM)
        {"abbreviation": "BSHM", "name": "Bachelor of Science in Hospitality Management", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "BSTM", "name": "Bachelor of Science in Tourism Management", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time},
        {"abbreviation": "BSTRM", "name": "Bachelor of Science in Transportation Management", "created_by": admin_user, "updated_by": admin_user, "created_at": current_time, "updated_at": current_time}
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