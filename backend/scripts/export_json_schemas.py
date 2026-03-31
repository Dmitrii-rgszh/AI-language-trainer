import json
import sys
from pathlib import Path

from pydantic import TypeAdapter

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.schemas.blueprint import (
    LessonBlockBlueprint,
    LessonBlockRunBlueprint,
    LessonTemplateBlueprint,
    LessonRunBlueprint,
    MistakeRecordBlueprint,
    ProfessionTopicBlueprint,
    ProgressSnapshotBlueprint,
    UserProfileBlueprint,
    VocabularyItemBlueprint,
)

PROJECT_ROOT = BACKEND_ROOT.parent
OUTPUT_DIR = PROJECT_ROOT / "docs" / "schemas"


def write_schema(filename: str, schema: dict) -> None:
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["x-generated-from"] = "backend/app/schemas/blueprint.py"
    (OUTPUT_DIR / filename).write_text(
        json.dumps(schema, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    model_schemas = {
        "user-profile.schema.json": UserProfileBlueprint.model_json_schema(),
        "lesson-template.schema.json": LessonTemplateBlueprint.model_json_schema(),
        "lesson-run.schema.json": LessonRunBlueprint.model_json_schema(),
        "lesson-block-run.schema.json": LessonBlockRunBlueprint.model_json_schema(),
        "mistake-record.schema.json": MistakeRecordBlueprint.model_json_schema(),
        "progress-snapshot.schema.json": ProgressSnapshotBlueprint.model_json_schema(),
        "vocabulary-item.schema.json": VocabularyItemBlueprint.model_json_schema(),
        "profession-topic.schema.json": ProfessionTopicBlueprint.model_json_schema(),
    }

    for filename, schema in model_schemas.items():
        write_schema(filename, schema)

    write_schema(
        "lesson-block.schema.json",
        TypeAdapter(LessonBlockBlueprint).json_schema(),
    )


if __name__ == "__main__":
    main()
