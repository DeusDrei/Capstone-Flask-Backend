from api.extensions import db
from api.models.subjects import Subject
from api.services.activitylog_service import ActivityLogService
from api.models.subject_departments import SubjectDepartment
from api.models.departments import Department
from api.models.instructionalmaterials import InstructionalMaterial
from api.models.universityims import UniversityIM
from api.models.serviceims import ServiceIM

class SubjectService:
    @staticmethod
    def create_subject(data):
        """Create a new subject"""
        new_subject = Subject(
            code=data['code'],
            name=data['name'],
            created_by=data['created_by'],
            updated_by=data['updated_by']
        )
        
        db.session.add(new_subject)
        db.session.commit()
        
        if data.get('user_id'):
            ActivityLogService.log_activity(
                user_id=data['user_id'],
                action="CREATE",
                table_name="subjects",
                description=f"Created subject {new_subject.id}",
                record_id=new_subject.id,
                new_values={"name": new_subject.name, "code": new_subject.code}
            )
        
        return new_subject

    @staticmethod
    def get_all_subjects(page=1):
        """Get all active subjects with pagination"""
        per_page = 10 
        return Subject.query.filter_by(is_deleted=False).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )

    @staticmethod
    def get_all_subjects_no_pagination():
        """Get all active subjects (no pagination)"""
        return Subject.query.filter_by(is_deleted=False).all()

    @staticmethod
    def get_subject_by_id(subject_id):
        """Get subject by ID (including soft-deleted ones)"""
        return db.session.get(Subject, subject_id)

    @staticmethod
    def update_subject(subject_id, data):
        """Update subject data"""
        subject = Subject.query.filter_by(id=subject_id, is_deleted=False).first()
        if not subject:
            return None
        
        try:
            # Capture old values before update
            old_values = {
                "name": subject.name,
                "code": subject.code
            }
            
            # Update only the provided fields
            for key, value in data.items():
                if hasattr(subject, key):
                    setattr(subject, key, value)
            
            if 'updated_by' in data:
                subject.updated_by = data['updated_by']
            
            db.session.commit()
            
            if data.get('user_id'):
                ActivityLogService.log_activity(
                    user_id=data['user_id'],
                    action="UPDATE",
                    table_name="subjects",
                    description=f"Updated subject {subject_id}",
                    record_id=subject_id,
                    old_values=old_values,
                    new_values={"name": subject.name, "code": subject.code}
                )
            
            return subject
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Update failed: {str(e)}")

    @staticmethod
    def soft_delete_subject(subject_id):
        """Mark subject as deleted (soft delete)"""
        subject = Subject.query.filter_by(id=subject_id, is_deleted=False).first()
        if not subject:
            return False
        
        subject.is_deleted = True
        db.session.commit()   
        return True

    @staticmethod
    def get_deleted_subjects(page=1):
        """Get all soft-deleted subjects with pagination"""
        per_page = 10 
        return Subject.query.filter_by(is_deleted=True).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )

    @staticmethod
    def restore_subject(subject_id):
        """Restore a soft-deleted subject"""
        subject = Subject.query.filter_by(id=subject_id, is_deleted=True).first()
        if not subject:
            return False
        
        subject.is_deleted = False
        db.session.commit()
        return True

    @staticmethod
    def get_subjects_by_college_id(college_id: int):
        """Return distinct active subjects linked to a college via SubjectDepartment -> Department."""
        q = (
            db.session.query(Subject)
            .join(SubjectDepartment, SubjectDepartment.subject_id == Subject.id)
            .join(Department, Department.id == SubjectDepartment.department_id)
            .filter(Subject.is_deleted == False, Department.college_id == college_id)
            .distinct()
        )
        return q.all()

    @staticmethod
    def get_subject_by_im_id(im_id: int):
        """Resolve subject associated with an InstructionalMaterial.

        Logic:
        - Load IM (including soft deleted? we mimic get_instructional_material_by_id behavior which includes soft deleted) but reject if missing.
        - If IM has university_im_id -> fetch UniversityIM -> subject_id.
        - Else if IM has service_im_id -> fetch ServiceIM -> subject_id.
        - Return Subject (even if soft-deleted? We will respect is_deleted flag and return None if deleted) to stay consistent with get_subject_by_id route.
        """
        im: InstructionalMaterial | None = db.session.get(InstructionalMaterial, im_id)
        if not im:
            return None

        subject_id = None
        if im.university_im_id:
            uni = db.session.get(UniversityIM, im.university_im_id)
            if uni:
                subject_id = uni.subject_id
        if subject_id is None and im.service_im_id:
            svc = db.session.get(ServiceIM, im.service_im_id)
            if svc:
                subject_id = svc.subject_id

        if subject_id is None:
            return None

        subj = db.session.get(Subject, subject_id)
        if not subj or subj.is_deleted:
            return None
        return subj