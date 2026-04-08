import type { AppLocale } from "../../shared/i18n/locale";

export function getWelcomeAiTutorReplayPrompt(locale: AppLocale) {
  return locale === "ru"
    ? "Как бы ты вежливо заказал кофе без сахара на английском языке?"
    : "How would you politely order a coffee without sugar in English?";
}

export function getWelcomeAiTutorIntroVariants(locale: AppLocale) {
  const replayPrompt = getWelcomeAiTutorReplayPrompt(locale);

  if (locale === "ru") {
    return [
      `Привет, я Лиза. Я помогу тебе говорить по-английски естественно и уверенно. Для начала скажи: ${replayPrompt}`,
      `Привет, я Лиза, и мы будем учиться через реальные ситуации. Представь, что ты в кафе: ${replayPrompt}`,
      `Привет, я Лиза. Здесь мы тренируем не отдельные слова, а живую речь. Первая ситуация: ${replayPrompt}`,
    ];
  }

  return [
    `Hi, I am Liza. I will help you speak English naturally and confidently. To begin, tell me: ${replayPrompt}`,
    `Hi, I am Liza, and we will learn through real-life situations. Imagine you are in a cafe: ${replayPrompt}`,
    `Hi, I am Liza. Here we train real speech, not isolated words. First situation: ${replayPrompt}`,
  ];
}
