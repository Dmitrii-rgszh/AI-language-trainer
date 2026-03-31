from app.schemas.blueprint import ProfessionDomain

PROFESSION_TRACK_CATALOG = [
    {
        "id": "track-insurance",
        "title": "Insurance English",
        "domain": ProfessionDomain.INSURANCE,
        "summary": "Клиентские разговоры, продукты, objections и needs analysis.",
        "lesson_focus": ["client conversations", "value communication", "customer protection"],
    },
    {
        "id": "track-banking",
        "title": "Banking English",
        "domain": ProfessionDomain.BANKING,
        "summary": "Базовая лексика по продуктам, платежам и retail banking.",
        "lesson_focus": ["payments", "cards", "financial conversations"],
    },
    {
        "id": "track-trainer-skills",
        "title": "Trainer Skills",
        "domain": ProfessionDomain.TRAINER_SKILLS,
        "summary": "Фасилитация, coaching language, feedback style и структура тренинга.",
        "lesson_focus": ["facilitation", "feedback language", "coaching language"],
    },
    {
        "id": "track-ai-business",
        "title": "AI for Business",
        "domain": ProfessionDomain.AI_BUSINESS,
        "summary": "Промпты, AI assistants, workflows и explanation style для бизнеса.",
        "lesson_focus": ["prompts", "AI assistants", "risk-aware explanations"],
    },
]

PROFESSION_TOPIC_CATALOG = [
    {
        "id": "topic-trainer-feedback",
        "domain": ProfessionDomain.TRAINER_SKILLS,
        "title": "Trainer Feedback Language",
        "difficulty": "A2-B1",
        "content": "Useful phrases for soft, supportive feedback in workshops and coaching sessions.",
        "examples": [
            "Let's make this part a little clearer.",
            "This example is strong, and we can simplify the wording even more.",
        ],
        "tags": ["feedback", "trainer", "soft language"],
    },
    {
        "id": "topic-insurance-needs",
        "domain": ProfessionDomain.INSURANCE,
        "title": "Insurance Needs Analysis",
        "difficulty": "B1",
        "content": "Client discovery questions, recommendation structure and value communication.",
        "examples": [
            "Could you tell me what kind of financial protection matters most to you?",
        ],
        "tags": ["insurance", "client conversation"],
    },
    {
        "id": "topic-banking-product-explainer",
        "domain": ProfessionDomain.BANKING,
        "title": "Banking Product Explainer",
        "difficulty": "A2-B1",
        "content": "Clear phrases for payments, card issues, account options and next-step explanations.",
        "examples": [
            "I can walk you through the payment options and show what changes next.",
            "Let me explain the fee difference in a simpler way.",
        ],
        "tags": ["banking", "product explanation", "client support"],
    },
    {
        "id": "topic-ai-business-risk-brief",
        "domain": ProfessionDomain.AI_BUSINESS,
        "title": "AI Workflow Briefing",
        "difficulty": "B1",
        "content": "Language for AI pilots, guardrails, workflow updates and risk-aware business explanations.",
        "examples": [
            "We have tested the draft workflow, but a human review step is still required.",
            "This automation saves time, yet we still need a clear approval path.",
        ],
        "tags": ["ai", "workflow", "business explanation"],
    },
]
