from app.core.composition import build_runtime

runtime = build_runtime()

adaptive_study_service = runtime.adaptive_study_service
diagnostic_service = runtime.diagnostic_service
grammar_service = runtime.grammar_service
journey_service = runtime.journey_service
lesson_runtime_service = runtime.lesson_runtime_service
lesson_service = runtime.lesson_service
listening_service = runtime.listening_service
live_avatar_service = runtime.live_avatar_service
mistake_service = runtime.mistake_service
onboarding_service = runtime.onboarding_service
profile_service = runtime.profile_service
profession_service = runtime.profession_service
progress_service = runtime.progress_service
pronunciation_service = runtime.pronunciation_service
provider_service = runtime.provider_service
recommendation_service = runtime.recommendation_service
speaking_service = runtime.speaking_service
stt_service = runtime.stt_service
user_service = runtime.user_service
welcome_tutor_service = runtime.welcome_tutor_service
voice_service = runtime.voice_service
writing_service = runtime.writing_service
