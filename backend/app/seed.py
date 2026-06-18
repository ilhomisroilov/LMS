"""Idempotent seed data for v1.2 (multi-tenant).

Creates two organizations so tenant-isolation can be demonstrated/tested:
  • Org A "EduCore Demo"     — full demo: admin, manager, teachers, students, ...
  • Org B "Second Academy"   — minimal: its own admin + student (cross-tenant)

Plus an INVITED user (no password) to exercise the invite flow.

Run with:  python -m app.seed
"""
from datetime import date, timedelta

from sqlalchemy import select

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.attendance import Attendance
from app.models.course import Course
from app.models.enums import AttendanceStatus, LessonContentType, PaymentStatus, StudentStatus
from app.models.group import Group, GroupStudent
from app.models.lesson import Lesson
from app.models.organization import Branch, Organization
from app.models.parent import Parent
from app.models.payment import Payment
from app.models.role import Role, RoleName
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.user import User

ROLES = [
    (RoleName.super_admin, "Platform operator"),
    (RoleName.admin, "Full organization access"),
    (RoleName.manager, "Branch operations (no org config)"),
    (RoleName.teacher, "Manage groups, attendance, lessons, tests"),
    (RoleName.student, "View own schedule, payments, lessons, tests"),
    (RoleName.parent, "View child progress & payments"),
]


def get_or_create_role(db, name: RoleName, desc: str) -> Role:
    role = db.scalar(select(Role).where(Role.name == name.value))
    if not role:
        role = Role(name=name.value, description=desc)
        db.add(role)
        db.flush()
    return role


def get_or_create_org(db, *, name: str, slug: str) -> Organization:
    org = db.scalar(select(Organization).where(Organization.slug == slug))
    if not org:
        org = Organization(name=name, slug=slug)
        db.add(org)
        db.flush()
        db.add(Branch(organization_id=org.id, name="Main Branch"))
        db.flush()
    return org


def get_or_create_user(db, *, org, full_name, phone, password, role: Role,
                       lang="uz", status="active") -> User:
    user = db.scalar(select(User).where(User.phone == phone))
    if not user:
        user = User(
            full_name=full_name, phone=phone,
            hashed_password=hash_password(password) if password else None,
            role_id=role.id, language=lang, organization_id=org.id, status=status,
            is_active=(status == "active"),
        )
        db.add(user)
        db.flush()
    return user


def run() -> None:
    db = SessionLocal()
    try:
        roles = {name: get_or_create_role(db, name, desc) for name, desc in ROLES}
        db.commit()

        org_a = get_or_create_org(db, name="EduCore Demo", slug="educore")
        org_b = get_or_create_org(db, name="Second Academy", slug="second-academy")
        db.commit()

        # ================= ORG A — full demo =================
        get_or_create_user(db, org=org_a, full_name="Bosh Admin",
                           phone=settings.FIRST_ADMIN_PHONE,
                           password=settings.FIRST_ADMIN_PASSWORD, role=roles[RoleName.admin])
        get_or_create_user(db, org=org_a, full_name="Operatsion Manager",
                           phone="+998901112200", password="Manager12345",
                           role=roles[RoleName.manager])
        # Invited user (no password) — demonstrates invite/temp-password flow.
        get_or_create_user(db, org=org_a, full_name="Yangi Xodim (taklif)",
                           phone="+998901119999", password=None,
                           role=roles[RoleName.teacher], status="invited")

        t_user1 = get_or_create_user(db, org=org_a, full_name="Aziz Karimov",
                                     phone="+998901000001", password="teacher123",
                                     role=roles[RoleName.teacher])
        t_user2 = get_or_create_user(db, org=org_a, full_name="Dilnoza Yusupova",
                                     phone="+998901000002", password="teacher123",
                                     role=roles[RoleName.teacher])
        db.flush()
        teacher1 = db.scalar(select(Teacher).where(Teacher.user_id == t_user1.id)) or Teacher(
            user_id=t_user1.id, organization_id=org_a.id, salary=5000000, subjects="English,IELTS")
        teacher2 = db.scalar(select(Teacher).where(Teacher.user_id == t_user2.id)) or Teacher(
            user_id=t_user2.id, organization_id=org_a.id, salary=4500000, subjects="Math,Physics")
        db.add_all([teacher1, teacher2]); db.flush()

        if not db.scalar(select(Course).where(Course.name == "General English",
                                              Course.organization_id == org_a.id)):
            eng = Course(name="General English", description="A1-B2 communicative English",
                         organization_id=org_a.id)
            math = Course(name="Mathematics", description="School & olympiad mathematics",
                          organization_id=org_a.id)
            db.add_all([eng, math]); db.flush()
            db.add_all([
                Lesson(course_id=eng.id, title="Unit 1: Greetings",
                       content_type=LessonContentType.text,
                       content="Hello / Salom — basic greetings.", order_index=1),
                Lesson(course_id=eng.id, title="Unit 2: Present Simple",
                       content_type=LessonContentType.video,
                       content="https://example.com/present-simple", order_index=2),
                Lesson(course_id=math.id, title="Algebra basics",
                       content_type=LessonContentType.text,
                       content="Variables, expressions and equations.", order_index=1),
            ])
            db.flush()
        else:
            eng = db.scalar(select(Course).where(Course.name == "General English",
                                                 Course.organization_id == org_a.id))
            math = db.scalar(select(Course).where(Course.name == "Mathematics",
                                                  Course.organization_id == org_a.id))

        if not db.scalar(select(Group).where(Group.name == "ENG-101",
                                             Group.organization_id == org_a.id)):
            g1 = Group(name="ENG-101", course_id=eng.id, teacher_id=teacher1.id,
                       organization_id=org_a.id,
                       schedule_days="Mon,Wed,Fri", schedule_time="18:00-19:30")
            g2 = Group(name="MATH-201", course_id=math.id, teacher_id=teacher2.id,
                       organization_id=org_a.id,
                       schedule_days="Tue,Thu,Sat", schedule_time="16:00-17:30")
            db.add_all([g1, g2]); db.flush()
        else:
            g1 = db.scalar(select(Group).where(Group.name == "ENG-101",
                                               Group.organization_id == org_a.id))
            g2 = db.scalar(select(Group).where(Group.name == "MATH-201",
                                               Group.organization_id == org_a.id))

        p_user = get_or_create_user(db, org=org_a, full_name="Rustam Toshmatov (Ota-ona)",
                                    phone="+998901000010", password="parent123",
                                    role=roles[RoleName.parent])
        db.flush()
        parent = db.scalar(select(Parent).where(Parent.user_id == p_user.id)) or Parent(
            user_id=p_user.id, organization_id=org_a.id)
        db.add(parent); db.flush()

        demo_students = [
            ("Jasur Toshmatov", "+998901000101", parent.id, g1),
            ("Madina Olimova", "+998901000102", None, g1),
            ("Sardor Rahimov", "+998901000103", None, g2),
        ]
        students = []
        for name, phone, parent_id, group in demo_students:
            u = get_or_create_user(db, org=org_a, full_name=name, phone=phone,
                                   password="student123", role=roles[RoleName.student])
            db.flush()
            st = db.scalar(select(Student).where(Student.user_id == u.id))
            if not st:
                st = Student(user_id=u.id, organization_id=org_a.id, status=StudentStatus.active,
                             parent_phone=p_user.phone if parent_id else None, parent_id=parent_id)
                db.add(st); db.flush()
            if not db.scalar(select(GroupStudent).where(
                    GroupStudent.group_id == group.id, GroupStudent.student_id == st.id)):
                db.add(GroupStudent(group_id=group.id, student_id=st.id))
            students.append((st, group))
        db.flush()

        if not db.scalar(select(Attendance).where(Attendance.organization_id == org_a.id)):
            today = date.today()
            for st, group in students:
                for i, status in enumerate(
                    [AttendanceStatus.present, AttendanceStatus.late, AttendanceStatus.absent]
                ):
                    db.add(Attendance(student_id=st.id, group_id=group.id,
                                      organization_id=org_a.id,
                                      lesson_date=today - timedelta(days=i * 2), status=status))

        if not db.scalar(select(Payment).where(Payment.organization_id == org_a.id)):
            month = date.today().strftime("%Y-%m")
            specs = [(students[0][0], 500000, 500000, PaymentStatus.paid),
                     (students[1][0], 500000, 250000, PaymentStatus.partial),
                     (students[2][0], 600000, 0, PaymentStatus.unpaid)]
            for st, amount, paid, status in specs:
                db.add(Payment(student_id=st.id, organization_id=org_a.id, amount=amount,
                               amount_paid=paid, month=month, status=status))

        # ================= ORG B — minimal (cross-tenant) =================
        b_admin = get_or_create_user(db, org=org_b, full_name="Org B Admin",
                                     phone="+998909990001", password="Admin12345",
                                     role=roles[RoleName.admin])
        b_course = db.scalar(select(Course).where(Course.organization_id == org_b.id))
        if not b_course:
            b_course = Course(name="Korean Basics", organization_id=org_b.id)
            db.add(b_course); db.flush()
        b_group = db.scalar(select(Group).where(Group.organization_id == org_b.id))
        if not b_group:
            b_group = Group(name="KOR-101", course_id=b_course.id, organization_id=org_b.id)
            db.add(b_group); db.flush()
        bs_user = get_or_create_user(db, org=org_b, full_name="Org B Student",
                                     phone="+998909990101", password="student123",
                                     role=roles[RoleName.student])
        db.flush()
        if not db.scalar(select(Student).where(Student.user_id == bs_user.id)):
            db.add(Student(user_id=bs_user.id, organization_id=org_b.id,
                           status=StudentStatus.active))

        db.commit()
        print("Seed complete.")
        print("   Org A admin:", settings.FIRST_ADMIN_PHONE, "/", settings.FIRST_ADMIN_PASSWORD)
        print("   Org A manager: +998901112200 / Manager12345")
        print("   Org B admin: +998909990001 / Admin12345")
    finally:
        db.close()


if __name__ == "__main__":
    run()
