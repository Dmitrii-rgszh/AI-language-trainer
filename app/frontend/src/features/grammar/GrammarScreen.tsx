import { Link } from "react-router-dom";
import { routes } from "../../shared/constants/routes";
import { useLocale } from "../../shared/i18n/useLocale";
import { useAppStore } from "../../shared/store/app-store";
import { Card } from "../../shared/ui/Card";
import { ProgressBar } from "../../shared/ui/ProgressBar";
import { SectionHeading } from "../../shared/ui/SectionHeading";
import { LizaCoachPanel } from "../../widgets/liza/LizaCoachPanel";
import { LivingDepthSection } from "../../widgets/living-background/LivingDepthSection";
import { livingDepthSectionIds } from "../../widgets/living-background/livingBackgroundConfig";

export function GrammarScreen() {
  const { locale, tr } = useLocale();
  const grammarTopics = useAppStore((state) => state.grammarTopics);
  const weakestTopic = [...grammarTopics].sort((left, right) => left.mastery - right.mastery)[0] ?? null;
  const strongestTopic = [...grammarTopics].sort((left, right) => right.mastery - left.mastery)[0] ?? null;
  const replayCta = locale === "ru" ? "Послушать ещё раз" : "Hear it again";
  const coachTitle = locale === "ru" ? "Liza Grammar Layer" : "Liza Grammar Layer";
  const coachMessage =
    locale === "ru"
      ? weakestTopic
        ? `Сейчас лучше не пытаться охватить всю grammar сразу. Я бы начала с темы «${tr(weakestTopic.title)}», а потом сразу перенесла её в речь и письмо, чтобы правило стало рабочим инструментом.`
        : "Я помогу превратить grammar из пугающего набора правил в понятную рабочую систему, которую легко переносить в речь и письмо."
      : weakestTopic
        ? `Do not try to absorb all grammar at once. I would begin with ${tr(weakestTopic.title)}, then move it straight into speaking and writing so the rule becomes usable.`
        : "I can help turn grammar from a scary set of rules into a clear working system you can carry into speaking and writing.";
  const coachSpokenMessage =
    locale === "ru"
      ? weakestTopic
        ? `Сейчас твой лучший grammar-фокус — ${tr(weakestTopic.title)}. Разберём правило просто, а потом сразу перенесём его в живой язык.`
        : "Сейчас я помогу превратить grammar в понятную рабочую систему, а не в пугающий набор правил."
      : weakestTopic
        ? `Your best grammar focus right now is ${tr(weakestTopic.title)}. We will make the rule simple first, then move it into real language right away.`
        : "I will help turn grammar into a clear working system rather than a scary set of abstract rules.";
  const coachSupportingText =
    locale === "ru"
      ? strongestTopic
        ? `Сильнее всего у тебя уже выглядит «${tr(strongestTopic.title)}». Значит здесь можно не объяснять всё заново, а выстраивать более умное grammar-ядро вокруг самых слабых тем.`
        : "Лиза должна помогать не просто читать объяснения, а собирать grammar в понятную карту: что уже держится, что сыпется и что даст максимум эффекта следующим шагом."
      : strongestTopic
        ? `${tr(strongestTopic.title)} already looks stronger. That means we can stop reteaching everything and instead build a smarter grammar core around what is still weak.`
        : "Liza should not just restate explanations. She should help turn grammar into a map of what is stable, what breaks, and what gives the biggest lift next.";

  return (
    <div className="space-y-4">
      <SectionHeading
        eyebrow={tr("Grammar Coach")}
        title={tr("Grammar Center")}
        description={tr("Build control over the grammar patterns that matter most in your next lessons.")}
      />

      <LivingDepthSection id={livingDepthSectionIds.grammarCoach}>
        <LizaCoachPanel
          locale={locale}
          playKey={`grammar:${weakestTopic?.id ?? "empty"}:${strongestTopic?.id ?? "empty"}:${grammarTopics.length}`}
          title={coachTitle}
          message={coachMessage}
          spokenMessage={coachSpokenMessage}
          spokenLanguage={locale}
          replayCta={replayCta}
          primaryAction={(
            <Link to={routes.speaking} className="proof-lesson-primary-button">
              {locale === "ru" ? "Перенести правило в speaking" : "Move the rule into speaking"}
            </Link>
          )}
          secondaryAction={(
            <Link to={routes.writing} className="proof-lesson-secondary-action">
              {locale === "ru" ? "Перейти в writing" : "Go to writing"}
            </Link>
          )}
          supportingText={coachSupportingText}
        />
      </LivingDepthSection>

      <div className="grid gap-4 lg:grid-cols-2">
        {grammarTopics.map((topic) => (
          <Card key={topic.id} className="space-y-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="text-lg font-semibold text-ink">{tr(topic.title)}</div>
                <div className="mt-1 text-xs uppercase tracking-[0.18em] text-coral">{topic.level}</div>
              </div>
              <div className="rounded-2xl bg-white/70 px-3 py-2 text-sm font-semibold text-ink">
                {topic.mastery}%
              </div>
            </div>

            <ProgressBar value={topic.mastery} />
            <div className="text-sm leading-6 text-slate-700">{tr(topic.explanation)}</div>

            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
              {topic.checkpoints.map((checkpoint) => (
                <div key={checkpoint}>• {tr(checkpoint)}</div>
              ))}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
