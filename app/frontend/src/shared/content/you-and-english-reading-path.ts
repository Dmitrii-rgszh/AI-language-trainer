type LocalizedMission = {
  id: string;
  title: string;
  stageLabel: string;
  summary: string;
  transfer: string;
};

export function getYouAndEnglishReadingPath(locale: "ru" | "en"): LocalizedMission[] {
  if (locale === "ru") {
    return [
      {
        id: "you-progress",
        title: "Let’s Talk About Progress",
        stageLabel: "Философия роста",
        summary:
          "Использовать эту главу как мягкий вход в маршрут: английский не как борьба за идеальность, а как путь к свободе, лёгкости и внутреннему движению.",
        transfer:
          "После чтения: назвать, какой именно живой опыт ученик хочет получить через английский, а не только какой уровень он хочет достичь.",
      },
      {
        id: "you-pyramid",
        title: "The Pyramid of Language Success",
        stageLabel: "Ритуал дня",
        summary:
          "Сделать из этой главы каноническую основу daily ritual: слова из жизни, чтение ради удовольствия, спонтанный голос и регулярность без перегруза.",
        transfer:
          "После чтения: выбрать один микро-ритуал на сегодня и сразу встроить его в маршрут.",
      },
      {
        id: "you-mistakes",
        title: "Making Mistakes",
        stageLabel: "Антистыд",
        summary:
          "Использовать эту историю для reading -> speaking/writing response о смущении, ошибках и цене перфекционизма.",
        transfer:
          "После чтения: рассказать о собственной awkward language moment и назвать, что именно она дала для роста.",
      },
      {
        id: "you-fear",
        title: "About Fear",
        stageLabel: "Свобода от оценки",
        summary:
          "Поднимать тему страха осуждения, школьной зажатости и необходимости более лёгкой, игровой среды для речи.",
        transfer:
          "После чтения: выбрать, какой страх сегодня сильнее всего мешает говорить живо, и как маршрут должен его ослабить.",
      },
      {
        id: "you-here-now",
        title: "Here and Now",
        stageLabel: "Неопределённость и присутствие",
        summary:
          "Использовать текст как основу для толерантности к неопределённости и борьбы с freeze-реакцией, когда ученик хочет быть полностью готовым заранее.",
        transfer:
          "После чтения: сделать короткий response-pass без полной подготовки и зафиксировать, что произошло с уровнем напряжения.",
      },
      {
        id: "you-yes",
        title: "Just Say Yes",
        stageLabel: "Жизнь и контакт",
        summary:
          "Вести ученика к мысли, что язык растёт через движение, контакт и участие в жизни, но без потери границ и чувства безопасности.",
        transfer:
          "После чтения: придумать один безопасный yes-action, где английский можно использовать в реальной жизни уже на этой неделе.",
      },
    ];
  }

  return [
    {
      id: "you-progress",
      title: "Let’s Talk About Progress",
      stageLabel: "Growth philosophy",
      summary:
        "Use this chapter as a soft route entry: English is not a fight for perfection, but a path toward freedom, lightness, and inner movement.",
      transfer:
        "After reading: name the real lived experience the learner wants from English, not only the target level.",
    },
    {
      id: "you-pyramid",
      title: "The Pyramid of Language Success",
      stageLabel: "Daily ritual",
      summary:
        "Turn this chapter into the backbone of the daily ritual: real-life words, reading for pleasure, spontaneous voice, and regularity without overload.",
      transfer:
        "After reading: choose one micro-ritual for today and place it directly into the route.",
    },
    {
      id: "you-mistakes",
      title: "Making Mistakes",
      stageLabel: "Anti-shame",
      summary:
        "Use this story for a reading -> speaking/writing response about embarrassment, mistakes, and the cost of perfectionism.",
      transfer:
        "After reading: tell one personal awkward language moment and name what it gave the learner.",
    },
    {
      id: "you-fear",
      title: "About Fear",
      stageLabel: "Freedom from judgment",
      summary:
        "Open the theme of fear of judgment, school-conditioned tension, and the need for lighter, more playful speaking conditions.",
      transfer:
        "After reading: identify which fear is most alive today and how the route should soften it.",
    },
    {
      id: "you-here-now",
      title: "Here and Now",
      stageLabel: "Ambiguity and presence",
      summary:
        "Use the text to build tolerance to ambiguity and weaken the freeze response that comes from needing perfect readiness before speaking.",
      transfer:
        "After reading: do one short response pass without full preparation and notice what changed in the learner's tension.",
    },
    {
      id: "you-yes",
      title: "Just Say Yes",
      stageLabel: "Life and contact",
      summary:
        "Guide the learner toward the idea that language grows through movement, contact, and real life, without losing healthy boundaries.",
      transfer:
        "After reading: choose one safe yes-action where English can be used in real life this week.",
    },
  ];
}
