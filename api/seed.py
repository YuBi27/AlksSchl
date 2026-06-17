"""
Тестові дані для розробки.
Запуск: make seed
"""
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from api.models.models import Base, User, StudentProfile, TeacherProfile, InviteCode, Group, StudentGroup, Schedule
from api.config import settings

engine = create_async_engine(settings.database_url)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

TEACHERS = [
    {
        "telegram_id": 10000001,
        "username": "teacher_kovalenko",
        "full_name": "Коваленко Олена Василівна",
        "bio": "Спеціалізуюсь на навчанні дітей від 5 до 12 років. Ігровий підхід.",
        "specialization": "English for Kids",
        "experience_years": 5,
    },
    {
        "telegram_id": 10000002,
        "username": "teacher_bondar",
        "full_name": "Бондар Михайло Олексійович",
        "bio": "Допомагаю досягти результатів у бізнес-переговорах та презентаціях.",
        "specialization": "Business English",
        "experience_years": 8,
    },
    {
        "telegram_id": 10000003,
        "username": "teacher_melnyk",
        "full_name": "Мельник Анна Сергіївна",
        "bio": "Підготувала 150+ студентів до IELTS 7.0+.",
        "specialization": "IELTS / TOEFL Preparation",
        "experience_years": 6,
    },
]

STUDENTS = [
    {"telegram_id": 20000001, "username": "student_01", "full_name": "Іваненко Дмитро Олегович", "phone": "+380991234501", "study_format": "online"},
    {"telegram_id": 20000002, "username": "student_02", "full_name": "Петренко Марія Іванівна", "phone": "+380991234502", "study_format": "offline"},
    {"telegram_id": 20000003, "username": "student_03", "full_name": "Сидоренко Олексій Миколайович", "phone": "+380991234503", "study_format": "online"},
    {"telegram_id": 20000004, "username": "student_04", "full_name": "Коваль Юлія Андріївна", "phone": "+380991234504", "study_format": "hybrid"},
    {"telegram_id": 20000005, "username": "student_05", "full_name": "Мороз Артем Вікторович", "phone": "+380991234505", "study_format": "online"},
    {"telegram_id": 20000006, "username": "student_06", "full_name": "Лисенко Ірина Борисівна", "phone": "+380991234506", "study_format": "offline"},
    {"telegram_id": 20000007, "username": "student_07", "full_name": "Шевченко Максим Дмитрович", "phone": "+380991234507", "study_format": "online"},
    {"telegram_id": 20000008, "username": "student_08", "full_name": "Бойко Вікторія Олександрівна", "phone": "+380991234508", "study_format": "hybrid"},
    {"telegram_id": 20000009, "username": "student_09", "full_name": "Гриценко Назар Петрович", "phone": "+380991234509", "study_format": "online"},
    {"telegram_id": 20000010, "username": "student_10", "full_name": "Ткаченко Аліна Василівна", "phone": "+380991234510", "study_format": "offline"},
]

GROUPS = [
    {"name": "Новачки", "level": "novice"},
    {"name": "Група A1", "level": "A1"},
    {"name": "Група A2", "level": "A2"},
    {"name": "Група B1", "level": "B1"},
    {"name": "Speaking Club", "level": "B2"},
    {"name": "Група C1", "level": "C1"},
]

# (student_telegram_id, group_name, english_level)
STUDENT_GROUP_ASSIGNMENTS = [
    (20000001, "Новачки", "novice"),
    (20000002, "Новачки", "novice"),
    (20000003, "Група A1", "A1"),
    (20000004, "Група A1", "A1"),
    (20000005, "Група A2", "A2"),
    (20000006, "Група A2", "A2"),
    (20000007, "Група B1", "B1"),
    (20000008, "Група B1", "B1"),
    (20000009, "Speaking Club", "B2"),
    (20000010, "Speaking Club", "B2"),
]

# (group_name, day_of_week, start_time_str, duration_min)
# day_of_week: 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
SCHEDULE_TEMPLATES = [
    ("Новачки",      1, "17:00", 60),   # Tuesday
    ("Новачки",      4, "17:00", 60),   # Friday
    ("Група A1",     1, "18:30", 60),   # Tuesday
    ("Група A1",     3, "18:30", 60),   # Thursday
    ("Група A2",     2, "17:00", 60),   # Wednesday
    ("Група A2",     4, "17:00", 60),   # Friday
    ("Група B1",     1, "19:00", 90),   # Tuesday
    ("Група B1",     3, "19:00", 90),   # Thursday
    ("Speaking Club",0, "11:00", 90),   # Monday
    ("Speaking Club",3, "11:00", 90),   # Thursday
]


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        print("🌱 Seeding database...")

        for t in TEACHERS:
            result = await db.execute(select(User).where(User.telegram_id == t["telegram_id"]))
            if result.scalar_one_or_none():
                print(f"  ⏭ Teacher {t['full_name']} already exists, skipping")
                continue

            user = User(
                telegram_id=t["telegram_id"],
                username=t["username"],
                language="uk",
                role="teacher",
                status="active",
            )
            db.add(user)
            await db.flush()

            profile = TeacherProfile(
                user_id=user.id,
                full_name=t["full_name"],
                photo_file_id=None,
                bio=t["bio"],
                specialization=t["specialization"],
                experience_years=t["experience_years"],
            )
            db.add(profile)
            print(f"  ✅ Teacher: {t['full_name']}")

        for s in STUDENTS:
            result = await db.execute(select(User).where(User.telegram_id == s["telegram_id"]))
            if result.scalar_one_or_none():
                print(f"  ⏭ Student {s['full_name']} already exists, skipping")
                continue

            user = User(
                telegram_id=s["telegram_id"],
                username=s["username"],
                language="uk",
                role="student",
                status="active",
            )
            db.add(user)
            await db.flush()

            profile = StudentProfile(
                user_id=user.id,
                full_name=s["full_name"],
                phone=s["phone"],
                parent_name="Батько/Мати PLACEHOLDER",
                parent_phone="+380991111111",
                study_start_month="2026-01",
                study_format=s["study_format"],
                extra_info=None,
                notion_link=f"https://notion.so/PLACEHOLDER-{user.id}",
            )
            db.add(profile)
            print(f"  ✅ Student: {s['full_name']}")

        result = await db.execute(select(InviteCode).where(InviteCode.code == "TEST-INVITE-2024"))
        if not result.scalar_one_or_none():
            invite = InviteCode(code="TEST-INVITE-2024", created_by=None, role="teacher", expires_at=None)
            db.add(invite)
            print("  ✅ Invite code: TEST-INVITE-2024")

        await db.commit()

        # --- Groups ---
        for g_data in GROUPS:
            result = await db.execute(select(Group).where(Group.name == g_data["name"]))
            if result.scalar_one_or_none():
                print(f"  ⏭ Group '{g_data['name']}' already exists, skipping")
                continue
            group = Group(name=g_data["name"], level=g_data["level"])
            db.add(group)
            print(f"  ✅ Group: {g_data['name']}")
        await db.flush()

        # --- Student → Group assignments ---
        for tg_id, group_name, level in STUDENT_GROUP_ASSIGNMENTS:
            user_result = await db.execute(select(User).where(User.telegram_id == tg_id))
            user = user_result.scalar_one_or_none()
            group_result = await db.execute(select(Group).where(Group.name == group_name))
            group = group_result.scalar_one_or_none()
            if not user or not group:
                continue

            sg_result = await db.execute(
                select(StudentGroup).where(
                    StudentGroup.user_id == user.id,
                    StudentGroup.group_id == group.id,
                )
            )
            if sg_result.scalar_one_or_none():
                continue

            # Set english_level on profile
            profile_result = await db.execute(
                select(StudentProfile).where(StudentProfile.user_id == user.id)
            )
            profile = profile_result.scalar_one_or_none()
            if profile and not profile.english_level:
                profile.english_level = level

            db.add(StudentGroup(user_id=user.id, group_id=group.id))
            print(f"  ✅ Assigned {tg_id} → {group_name}")

        await db.commit()

        # --- Schedules ---
        from api.crud.schedules import create_schedule, generate_lessons_for_schedule, _parse_time
        for group_name, dow, start_t, dur in SCHEDULE_TEMPLATES:
            grp_result = await db.execute(select(Group).where(Group.name == group_name))
            grp = grp_result.scalar_one_or_none()
            if not grp:
                print(f"  ⚠ Group '{group_name}' not found, skipping schedule")
                continue
            existing = await db.execute(
                select(Schedule).where(
                    Schedule.group_id == grp.id,
                    Schedule.day_of_week == dow,
                )
            )
            if existing.scalar_one_or_none():
                print(f"  ⏭ Schedule {group_name} day={dow} already exists, skipping")
                continue
            t = _parse_time(start_t)
            sched = Schedule(group_id=grp.id, day_of_week=dow, start_time=t, duration_min=dur)
            db.add(sched)
            await db.flush()
            count = await generate_lessons_for_schedule(db, sched)
            print(f"  ✅ Schedule: {group_name} day={dow} {start_t} → {count} lessons")

        print("✅ Seed complete!")


if __name__ == "__main__":
    asyncio.run(seed())
