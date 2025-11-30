"""
Analytics Service Module

Contains business logic for analytics endpoints, extracted from routes.
Follows the service pattern used in other services (e.g., instructionalmaterial_service.py).
"""
import csv
import io
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from flask import current_app
from sqlalchemy import func, case, and_, or_

from api.extensions import db
from api.models import (
    InstructionalMaterial,
    UniversityIM,
    ServiceIM,
    ActivityLog,
    User,
    College,
    Department,
    IMSubmission,
)


class AnalyticsService:
    """Service class for analytics business logic."""

    # ============ Helper Methods ============

    @staticmethod
    def get_filtered_im_query(
        college_id: Optional[int] = None,
        department_id: Optional[int] = None
    ):
        """
        Returns a base query for InstructionalMaterial filtered by college/department.
        This joins through UniversityIM to get college and department relationships.
        """
        query = db.session.query(InstructionalMaterial)

        if college_id or department_id:
            # Join with UniversityIM to filter by college/department
            # InstructionalMaterial.university_im_id -> UniversityIM.id
            query = query.join(
                UniversityIM,
                InstructionalMaterial.university_im_id == UniversityIM.id
            )

            if college_id:
                query = query.filter(UniversityIM.college_id == college_id)

            if department_id:
                query = query.filter(UniversityIM.department_id == department_id)

        return query

    @staticmethod
    def _get_status_category(status: str) -> str:
        """Categorize status for analytics."""
        completed_statuses = ['Certified', 'Published']
        active_statuses = [
            'For Department Checking',
            'For Subject Area Checking', 
            'For UTLDO Checking',
            'For IMER Evaluation',
            'For PIMEC Evaluation',
            'For Resubmission'
        ]

        if status in completed_statuses:
            return 'completed'
        elif status in active_statuses:
            return 'active'
        else:
            return 'other'

    # ============ Overview Analytics ============

    @staticmethod
    def get_overview(
        college_id: Optional[int] = None,
        department_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get overview analytics for the dashboard.
        Returns total IMs, status breakdown, and monthly trends.
        """
        base_query = AnalyticsService.get_filtered_im_query(college_id, department_id)

        # Total IMs
        total_ims = base_query.count()

        # Status breakdown
        status_counts = (
            base_query
            .with_entities(
                InstructionalMaterial.status,
                func.count(InstructionalMaterial.id).label('count')
            )
            .group_by(InstructionalMaterial.status)
            .all()
        )

        status_breakdown = {status: count for status, count in status_counts}

        # Monthly trends (last 6 months)
        six_months_ago = datetime.now() - timedelta(days=180)
        monthly_data = (
            base_query
            .filter(InstructionalMaterial.created_at >= six_months_ago)
            .with_entities(
                func.strftime('%Y-%m', InstructionalMaterial.created_at).label('month'),
                func.count(InstructionalMaterial.id).label('count')
            )
            .group_by(func.strftime('%Y-%m', InstructionalMaterial.created_at))
            .order_by(func.strftime('%Y-%m', InstructionalMaterial.created_at))
            .all()
        )

        monthly_trends = [{'month': month, 'count': count} for month, count in monthly_data]

        return {
            'total_ims': total_ims,
            'status_breakdown': status_breakdown,
            'monthly_trends': monthly_trends
        }

    # ============ College Analytics ============

    @staticmethod
    def get_college_analytics(
        college_id: Optional[int] = None,
        department_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get college-level analytics with IM counts.
        Fixed to properly count IMs through UniversityIM join without double-counting.
        """
        # Get all colleges (or specific one if filtered)
        colleges_query = db.session.query(College)
        if college_id:
            colleges_query = colleges_query.filter(College.id == college_id)
        colleges = colleges_query.all()

        college_data = []
        for college in colleges:
            # Query IMs through UniversityIM to get college association
            # This is the ONLY way an IM relates to a college
            college_ims_query = (
                db.session.query(InstructionalMaterial)
                .join(UniversityIM, InstructionalMaterial.university_im_id == UniversityIM.id)
                .filter(UniversityIM.college_id == college.id)
            )

            # Apply department filter if provided
            if department_id:
                college_ims_query = college_ims_query.filter(
                    UniversityIM.department_id == department_id
                )

            # Get status counts for this college
            status_counts = (
                college_ims_query
                .with_entities(
                    InstructionalMaterial.status,
                    func.count(InstructionalMaterial.id).label('count')
                )
                .group_by(InstructionalMaterial.status)
                .all()
            )

            # Build status dict and calculate totals
            status_dict = {status: count for status, count in status_counts}
            total = sum(status_dict.values())
            completed = status_dict.get('Certified', 0) + status_dict.get('Published', 0)

            college_data.append({
                'id': college.id,
                'abbreviation': college.abbreviation,
                'name': college.name,
                'total_ims': total,
                'completed': completed,
                'completion_rate': round((completed / total * 100), 1) if total > 0 else 0,
                'status_breakdown': status_dict
            })

        return {
            'colleges': college_data,
            'total_colleges': len(college_data)
        }

    # ============ Department Analytics ============

    @staticmethod
    def get_department_analytics(college_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get department-level analytics with IM counts.
        """
        # Get departments (filtered by college if provided)
        dept_query = db.session.query(Department)
        if college_id:
            dept_query = dept_query.filter(Department.college_id == college_id)
        departments = dept_query.all()

        department_data = []
        for dept in departments:
            # Query IMs through UniversityIM
            dept_ims_query = (
                db.session.query(InstructionalMaterial)
                .join(UniversityIM, InstructionalMaterial.university_im_id == UniversityIM.id)
                .filter(UniversityIM.department_id == dept.id)
            )

            # Get status counts
            status_counts = (
                dept_ims_query
                .with_entities(
                    InstructionalMaterial.status,
                    func.count(InstructionalMaterial.id).label('count')
                )
                .group_by(InstructionalMaterial.status)
                .all()
            )

            status_dict = {status: count for status, count in status_counts}
            total = sum(status_dict.values())
            completed = status_dict.get('Certified', 0) + status_dict.get('Published', 0)

            department_data.append({
                'id': dept.id,
                'abbreviation': dept.abbreviation,
                'name': dept.name,
                'college_id': dept.college_id,
                'total_ims': total,
                'completed': completed,
                'completion_rate': round((completed / total * 100), 1) if total > 0 else 0,
                'status_breakdown': status_dict
            })

        return {
            'departments': department_data,
            'total_departments': len(department_data)
        }

    # ============ User Contributions ============

    @staticmethod
    def get_user_contributions(
        limit: int = 10,
        college_id: Optional[int] = None,
        department_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get top contributors by IM count.
        """
        # Base query: count IMs per user (assigned_by)
        query = (
            db.session.query(
                User.id,
                User.first_name,
                User.last_name,
                User.email,
                func.count(InstructionalMaterial.id).label('total_ims')
            )
            .join(InstructionalMaterial, User.id == InstructionalMaterial.assigned_by)
        )

        # Apply filters through UniversityIM join
        if college_id or department_id:
            query = query.join(
                UniversityIM,
                InstructionalMaterial.university_im_id == UniversityIM.id
            )
            if college_id:
                query = query.filter(UniversityIM.college_id == college_id)
            if department_id:
                query = query.filter(UniversityIM.department_id == department_id)

        contributors = (
            query
            .group_by(User.id)
            .order_by(func.count(InstructionalMaterial.id).desc())
            .limit(limit)
            .all()
        )

        return {
            'contributors': [
                {
                    'id': c.id,
                    'name': f"{c.first_name} {c.last_name}",
                    'email': c.email,
                    'total_ims': c.total_ims
                }
                for c in contributors
            ]
        }

    # ============ Activity Timeline ============

    @staticmethod
    def get_activity_timeline(
        days: int = 30,
        college_id: Optional[int] = None,
        department_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get activity log timeline for the specified period.
        """
        start_date = datetime.now() - timedelta(days=days)

        # Query activity logs
        query = (
            db.session.query(
                func.date(ActivityLog.created_at).label('date'),
                ActivityLog.action,
                func.count(ActivityLog.id).label('count')
            )
            .filter(ActivityLog.created_at >= start_date)
        )

        # Filter by IM if college/department specified
        if college_id or department_id:
            # Get IM IDs that match the filter
            im_subquery = AnalyticsService.get_filtered_im_query(
                college_id, department_id
            ).with_entities(InstructionalMaterial.id).subquery()

            query = query.filter(ActivityLog.record_id.in_(im_subquery))

        timeline_data = (
            query
            .group_by(func.date(ActivityLog.created_at), ActivityLog.action)
            .order_by(func.date(ActivityLog.created_at))
            .all()
        )

        # Group by date
        timeline = {}
        for date, action, count in timeline_data:
            date_str = str(date)
            if date_str not in timeline:
                timeline[date_str] = {'date': date_str, 'actions': {}}
            timeline[date_str]['actions'][action] = count

        return {
            'timeline': list(timeline.values()),
            'days': days
        }

    # ============ Submissions by User ============

    @staticmethod
    def get_submissions_by_user(
        limit: int = 10,
        college_id: Optional[int] = None,
        department_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get top users by submission count.
        """
        query = (
            db.session.query(
                User.id,
                User.first_name,
                User.last_name,
                func.count(IMSubmission.id).label('submission_count')
            )
            .join(IMSubmission, User.id == IMSubmission.user_id)
            .join(InstructionalMaterial, IMSubmission.im_id == InstructionalMaterial.id)
        )

        if college_id or department_id:
            query = query.join(
                UniversityIM,
                InstructionalMaterial.university_im_id == UniversityIM.id
            )
            if college_id:
                query = query.filter(UniversityIM.college_id == college_id)
            if department_id:
                query = query.filter(UniversityIM.department_id == department_id)

        users = (
            query
            .group_by(User.id)
            .order_by(func.count(IMSubmission.id).desc())
            .limit(limit)
            .all()
        )

        return {
            'users': [
                {
                    'id': u.id,
                    'name': f"{u.first_name} {u.last_name}",
                    'submissions': u.submission_count
                }
                for u in users
            ]
        }

    # ============ Submissions Timeline ============

    @staticmethod
    def get_submissions_timeline(
        days: int = 30,
        college_id: Optional[int] = None,
        department_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get submission timeline for the specified period.
        """
        start_date = datetime.now() - timedelta(days=days)

        query = (
            db.session.query(
                func.date(IMSubmission.date_submitted).label('date'),
                func.count(IMSubmission.id).label('count')
            )
            .join(InstructionalMaterial, IMSubmission.im_id == InstructionalMaterial.id)
            .filter(IMSubmission.date_submitted >= start_date)
        )

        if college_id or department_id:
            query = query.join(
                UniversityIM,
                InstructionalMaterial.university_im_id == UniversityIM.id
            )
            if college_id:
                query = query.filter(UniversityIM.college_id == college_id)
            if department_id:
                query = query.filter(UniversityIM.department_id == department_id)

        timeline_data = (
            query
            .group_by(func.date(IMSubmission.date_submitted))
            .order_by(func.date(IMSubmission.date_submitted))
            .all()
        )

        return {
            'timeline': [
                {'date': str(date), 'submissions': count}
                for date, count in timeline_data
            ],
            'days': days
        }

    # ============ Deadline Analytics ============

    @staticmethod
    def get_deadline_analytics(
        college_id: Optional[int] = None,
        department_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get deadline status breakdown.
        Handles IMs with and without due dates.
        """
        now = datetime.now()
        seven_days = now + timedelta(days=7)
        thirty_days = now + timedelta(days=30)

        base_query = AnalyticsService.get_filtered_im_query(college_id, department_id)

        # Exclude completed statuses for deadline tracking
        active_query = base_query.filter(
            ~InstructionalMaterial.status.in_(['Certified', 'Published'])
        )

        # IMs without due_date
        no_deadline = active_query.filter(
            InstructionalMaterial.due_date.is_(None)
        ).count()

        # IMs with due_date
        with_deadline_query = active_query.filter(
            InstructionalMaterial.due_date.isnot(None)
        )

        overdue = with_deadline_query.filter(
            InstructionalMaterial.due_date < now
        ).count()

        due_soon = with_deadline_query.filter(
            and_(
                InstructionalMaterial.due_date >= now,
                InstructionalMaterial.due_date <= seven_days
            )
        ).count()

        due_this_month = with_deadline_query.filter(
            and_(
                InstructionalMaterial.due_date > seven_days,
                InstructionalMaterial.due_date <= thirty_days
            )
        ).count()

        on_track = with_deadline_query.filter(
            InstructionalMaterial.due_date > thirty_days
        ).count()

        # Get list of overdue and due soon IMs
        overdue_ims = (
            with_deadline_query
            .filter(InstructionalMaterial.due_date < now)
            .order_by(InstructionalMaterial.due_date)
            .limit(10)
            .all()
        )

        due_soon_ims = (
            with_deadline_query
            .filter(
                and_(
                    InstructionalMaterial.due_date >= now,
                    InstructionalMaterial.due_date <= seven_days
                )
            )
            .order_by(InstructionalMaterial.due_date)
            .limit(10)
            .all()
        )

        def get_im_subject_name(im):
            """Helper to get subject name from IM's university_im or service_im"""
            if im.university_im and im.university_im.subject:
                return im.university_im.subject.name
            elif im.service_im and im.service_im.subject:
                return im.service_im.subject.name
            return 'N/A'

        return {
            'summary': {
                'overdue': overdue,
                'due_soon': due_soon,
                'due_this_month': due_this_month,
                'on_track': on_track,
                'no_deadline': no_deadline
            },
            'overdue_ims': [
                {
                    'id': im.id,
                    'subject': get_im_subject_name(im),
                    'status': im.status,
                    'due_date': im.due_date.isoformat() if im.due_date else None
                }
                for im in overdue_ims
            ],
            'due_soon_ims': [
                {
                    'id': im.id,
                    'subject': get_im_subject_name(im),
                    'status': im.status,
                    'due_date': im.due_date.isoformat() if im.due_date else None
                }
                for im in due_soon_ims
            ]
        }

    # ============ Workflow Analytics ============

    @staticmethod
    def get_workflow_analytics(
        college_id: Optional[int] = None,
        department_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get workflow stage breakdown showing where IMs are in the pipeline.
        Uses actual statuses from the system.
        """
        base_query = AnalyticsService.get_filtered_im_query(college_id, department_id)

        # Define workflow stages with actual statuses
        workflow_stages = [
            {
                'name': 'For Department Checking',
                'statuses': ['For Department Checking'],
                'stage_order': 1
            },
            {
                'name': 'For Subject Area Checking',
                'statuses': ['For Subject Area Checking'],
                'stage_order': 2
            },
            {
                'name': 'For UTLDO Checking',
                'statuses': ['For UTLDO Checking'],
                'stage_order': 3
            },
            {
                'name': 'For IMER Evaluation',
                'statuses': ['For IMER Evaluation'],
                'stage_order': 4
            },
            {
                'name': 'For PIMEC Evaluation',
                'statuses': ['For PIMEC Evaluation'],
                'stage_order': 5
            },
            {
                'name': 'For Resubmission',
                'statuses': ['For Resubmission'],
                'stage_order': 6
            },
            {
                'name': 'Certified',
                'statuses': ['Certified'],
                'stage_order': 7
            },
            {
                'name': 'Published',
                'statuses': ['Published'],
                'stage_order': 8
            }
        ]

        stages_data = []
        total_active = 0
        total_completed = 0

        for stage in workflow_stages:
            count = base_query.filter(
                InstructionalMaterial.status.in_(stage['statuses'])
            ).count()

            # Track active vs completed
            if stage['name'] in ['Certified', 'Published']:
                total_completed += count
            else:
                total_active += count

            stages_data.append({
                'name': stage['name'],
                'count': count,
                'stage_order': stage['stage_order']
            })

        return {
            'stages': stages_data,
            'total_active': total_active,
            'total_completed': total_completed
        }

    # ============ Export Functions ============

    @staticmethod
    def export_overview_to_csv(
        college_id: Optional[int] = None,
        department_id: Optional[int] = None
    ) -> str:
        """
        Export overview analytics to CSV format.
        Returns CSV string.
        """
        overview = AnalyticsService.get_overview(college_id, department_id)
        colleges = AnalyticsService.get_college_analytics(college_id, department_id)
        departments = AnalyticsService.get_department_analytics(college_id)
        workflow = AnalyticsService.get_workflow_analytics(college_id, department_id)
        deadlines = AnalyticsService.get_deadline_analytics(college_id, department_id)

        output = io.StringIO()
        writer = csv.writer(output)

        # Overview section
        writer.writerow(['ANALYTICS OVERVIEW REPORT'])
        writer.writerow([f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'])
        writer.writerow([])

        # Summary stats
        writer.writerow(['SUMMARY'])
        writer.writerow(['Total IMs', overview['total_ims']])
        writer.writerow(['Active IMs', workflow['total_active']])
        writer.writerow(['Completed IMs', workflow['total_completed']])
        writer.writerow([])

        # Status breakdown
        writer.writerow(['STATUS BREAKDOWN'])
        writer.writerow(['Status', 'Count'])
        for status, count in overview['status_breakdown'].items():
            writer.writerow([status, count])
        writer.writerow([])

        # Deadline summary
        writer.writerow(['DEADLINE STATUS'])
        writer.writerow(['Category', 'Count'])
        for category, count in deadlines['summary'].items():
            writer.writerow([category.replace('_', ' ').title(), count])
        writer.writerow([])

        # Workflow stages
        writer.writerow(['WORKFLOW STAGES'])
        writer.writerow(['Stage', 'Count'])
        for stage in workflow['stages']:
            writer.writerow([stage['name'], stage['count']])
        writer.writerow([])

        # College data
        writer.writerow(['COLLEGE PERFORMANCE'])
        writer.writerow(['College Abbreviation', 'College Name', 'Total IMs', 'Completed', 'Completion Rate (%)'])
        for college in colleges['colleges']:
            writer.writerow([
                college['abbreviation'],
                college['name'],
                college['total_ims'],
                college['completed'],
                college['completion_rate']
            ])
        writer.writerow([])

        # Department data
        writer.writerow(['DEPARTMENT PERFORMANCE'])
        writer.writerow(['Department Abbreviation', 'Department Name', 'Total IMs', 'Completed', 'Completion Rate (%)'])
        for dept in departments['departments']:
            writer.writerow([
                dept['abbreviation'],
                dept['name'],
                dept['total_ims'],
                dept['completed'],
                dept['completion_rate']
            ])
        writer.writerow([])

        # Monthly trends
        writer.writerow(['MONTHLY TRENDS (Last 6 Months)'])
        writer.writerow(['Month', 'IMs Created'])
        for trend in overview['monthly_trends']:
            writer.writerow([trend['month'], trend['count']])

        return output.getvalue()
