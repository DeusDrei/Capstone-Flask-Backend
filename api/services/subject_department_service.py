from api.extensions import db
from api.models.subject_departments import SubjectDepartment
from api.models.subjects import Subject
from api.models.departments import Department
from sqlalchemy.exc import IntegrityError


class SubjectDepartmentService:
    @staticmethod
    def create(subject_id: int, department_id: int):
        if not Subject.query.get(subject_id):
            raise ValueError(f"Subject with ID {subject_id} does not exist")
        if not Department.query.get(department_id):
            raise ValueError(f"Department with ID {department_id} does not exist")
        try:
            assoc = SubjectDepartment(subject_id=subject_id, department_id=department_id)
            db.session.add(assoc)
            db.session.commit()
            return assoc
        except IntegrityError as e:
            db.session.rollback()
            if "unique constraint" in str(e.orig).lower():
                raise ValueError("This subject-department association already exists")
            raise ValueError("Database integrity error")

    @staticmethod
    def get(subject_id: int, department_id: int):
        return SubjectDepartment.query.filter_by(subject_id=subject_id, department_id=department_id).first()

    @staticmethod
    def get_departments_for_subject(subject_id: int):
        return SubjectDepartment.query.filter_by(subject_id=subject_id).all()

    @staticmethod
    def get_subjects_for_department(department_id: int):
        return SubjectDepartment.query.filter_by(department_id=department_id).all()

    @staticmethod
    def delete(subject_id: int, department_id: int):
        assoc = SubjectDepartment.query.filter_by(subject_id=subject_id, department_id=department_id).first()
        if not assoc:
            return False
        db.session.delete(assoc)
        db.session.commit()
        return True
