from inspect import signature

from fastapi.params import Depends as DependsMarker

from app.api.dependencies import require_profile
from app.api.routes import adaptive, daily_loop, dashboard, diagnostic, journey, lessons
from app.api.routes import listening, mistakes, progress, pronunciation, recommendations, speaking, writing


def test_profile_bound_routes_use_fastapi_dependency_injection() -> None:
    route_functions = [
        adaptive.get_adaptive_loop,
        adaptive.get_vocabulary_hub,
        adaptive.review_vocabulary_item,
        adaptive.start_recovery_run,
        daily_loop.get_today_daily_loop,
        daily_loop.start_today_daily_loop,
        dashboard.get_dashboard,
        diagnostic.get_diagnostic_roadmap,
        diagnostic.start_diagnostic_checkpoint,
        journey.complete_route_reentry_support_step,
        lessons.get_recommended_lesson,
        lessons.start_lesson_run,
        lessons.get_active_lesson_run,
        lessons.discard_lesson_run,
        lessons.restart_lesson_run,
        lessons.submit_block_result,
        lessons.complete_lesson_run,
        listening.get_listening_history,
        listening.get_listening_trends,
        mistakes.get_mistakes,
        progress.get_progress,
        pronunciation.get_pronunciation_attempts,
        pronunciation.get_pronunciation_trends,
        pronunciation.assess_pronunciation,
        recommendations.get_next_recommendation,
        speaking.get_speaking_feedback,
        speaking.get_speaking_voice_feedback,
        speaking.get_speaking_attempts,
        writing.review_writing,
        writing.get_writing_attempts,
    ]

    for route_function in route_functions:
        parameters = signature(route_function).parameters
        assert "profile" in parameters, f"{route_function.__name__} should accept injected profile"
        profile_parameter = parameters["profile"]
        assert isinstance(profile_parameter.default, DependsMarker)
        assert profile_parameter.default.dependency is require_profile
