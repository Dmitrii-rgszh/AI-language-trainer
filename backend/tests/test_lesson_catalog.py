from app.content.lessons.catalog import LESSON_TEMPLATE_CATALOG


def test_lesson_template_catalog_has_unique_template_ids() -> None:
    template_ids = [template["id"] for template in LESSON_TEMPLATE_CATALOG]

    assert len(template_ids) == len(set(template_ids))


def test_lesson_template_catalog_keeps_expected_track_coverage() -> None:
    assert len(LESSON_TEMPLATE_CATALOG) == 5
    assert LESSON_TEMPLATE_CATALOG[0]["id"] == "template-trainer-daily-flow"
    assert LESSON_TEMPLATE_CATALOG[-1]["id"] == "template-cross-cultural-daily-flow"
