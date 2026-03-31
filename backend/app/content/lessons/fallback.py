from app.content.lessons.catalog import LESSON_TEMPLATE_CATALOG
from app.schemas.lesson import Lesson, LessonBlock
from app.schemas.profile import UserProfile


def build_recommended_lesson(profile: UserProfile) -> Lesson:
    selected = next(
        (
            template
            for template in LESSON_TEMPLATE_CATALOG
            if profile.profession_track in template.get("enabled_tracks", [])
        ),
        LESSON_TEMPLATE_CATALOG[0],
    )

    blocks = [
        LessonBlock(
            id=block["id"],
            block_type=block["block_type"],
            title=block["title"],
            instructions=block["instructions"],
            estimated_minutes=block["estimated_minutes"],
            payload=block["payload"],
        )
        for block in selected["blocks"]
    ]

    return Lesson(
        id=selected["id"],
        lesson_type=selected["lesson_type"],
        title=selected["title"],
        goal=selected["goal"],
        difficulty=selected["difficulty"],
        duration=selected["estimated_duration"],
        modules=[block.block_type for block in blocks],
        blocks=blocks,
        completed=False,
        score=None,
    )

