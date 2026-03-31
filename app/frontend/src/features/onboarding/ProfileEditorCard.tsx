import { useEffect, useMemo, useState } from "react";
import type { UserProfile } from "../../entities/user/model";
import { useLocale } from "../../shared/i18n/useLocale";
import type { ProfessionTrackCard } from "../../shared/types/app-data";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";

export const defaultProfile: UserProfile = {
  id: "user-local-1",
  name: "Alex",
  nativeLanguage: "ru",
  currentLevel: "A2",
  targetLevel: "B2",
  professionTrack: "trainer_skills",
  preferredUiLanguage: "ru",
  preferredExplanationLanguage: "ru",
  lessonDuration: 25,
  speakingPriority: 8,
  grammarPriority: 7,
  professionPriority: 9,
};

interface ProfileEditorCardProps {
  initialProfile: UserProfile | null;
  professionTracks: ProfessionTrackCard[];
  title: string;
  description: string;
  submitLabel: string;
  onSave: (profile: UserProfile) => Promise<void>;
}

export function ProfileEditorCard({
  initialProfile,
  professionTracks,
  title,
  description,
  submitLabel,
  onSave,
}: ProfileEditorCardProps) {
  const { tr } = useLocale();
  const [form, setForm] = useState<UserProfile>(initialProfile ?? defaultProfile);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    setForm(initialProfile ?? defaultProfile);
  }, [initialProfile]);

  const activeTrackTitle = useMemo(
    () =>
      professionTracks.find(
        (track) => track.domain === form.professionTrack || track.id === form.professionTrack,
      )?.title ?? form.professionTrack,
    [form.professionTrack, professionTracks],
  );

  const updateField = <K extends keyof UserProfile>(field: K, value: UserProfile[K]) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  const handleSubmit = async () => {
    setIsSaving(true);
    try {
      await onSave(form);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
      <Card className="grid gap-4 md:grid-cols-2">
        <label className="space-y-2 text-sm text-slate-700">
          <span>{tr("Name")}</span>
          <input
            value={form.name}
            onChange={(event) => updateField("name", event.target.value)}
            className="w-full rounded-2xl border border-white/70 bg-white/80 px-4 py-3 outline-none"
          />
        </label>

        <label className="space-y-2 text-sm text-slate-700">
          <span>{tr("Current level")}</span>
          <select
            value={form.currentLevel}
            onChange={(event) => updateField("currentLevel", event.target.value)}
            className="w-full rounded-2xl border border-white/70 bg-white/80 px-4 py-3 outline-none"
          >
            <option>A1</option>
            <option>A2</option>
            <option>B1</option>
            <option>B2</option>
            <option>C1</option>
          </select>
        </label>

        <label className="space-y-2 text-sm text-slate-700">
          <span>{tr("Target level")}</span>
          <select
            value={form.targetLevel}
            onChange={(event) => updateField("targetLevel", event.target.value)}
            className="w-full rounded-2xl border border-white/70 bg-white/80 px-4 py-3 outline-none"
          >
            <option>A2</option>
            <option>B1</option>
            <option>B2</option>
            <option>C1</option>
            <option>C2</option>
          </select>
        </label>

        <label className="space-y-2 text-sm text-slate-700">
          <span>{tr("Profession track")}</span>
          <select
            value={form.professionTrack}
            onChange={(event) => updateField("professionTrack", event.target.value)}
            className="w-full rounded-2xl border border-white/70 bg-white/80 px-4 py-3 outline-none"
          >
            {professionTracks.length > 0 ? (
              professionTracks.map((track) => (
                <option key={track.id} value={track.domain}>
                  {tr(track.title)}
                </option>
              ))
            ) : (
              <>
                <option value="trainer_skills">{tr("Trainer Skills")}</option>
                <option value="insurance">{tr("Insurance English")}</option>
                <option value="banking">{tr("Banking English")}</option>
                <option value="ai_business">{tr("AI for Business")}</option>
              </>
            )}
          </select>
        </label>

        <label className="space-y-2 text-sm text-slate-700">
          <span>{tr("UI language")}</span>
          <select
            value={form.preferredUiLanguage}
            onChange={(event) => updateField("preferredUiLanguage", event.target.value)}
            className="w-full rounded-2xl border border-white/70 bg-white/80 px-4 py-3 outline-none"
          >
            <option value="ru">{tr("Russian")}</option>
            <option value="en">{tr("English")}</option>
          </select>
        </label>

        <label className="space-y-2 text-sm text-slate-700">
          <span>{tr("Explanation language")}</span>
          <select
            value={form.preferredExplanationLanguage}
            onChange={(event) => updateField("preferredExplanationLanguage", event.target.value)}
            className="w-full rounded-2xl border border-white/70 bg-white/80 px-4 py-3 outline-none"
          >
            <option value="ru">Русский</option>
            <option value="en">English</option>
          </select>
        </label>

        <label className="space-y-2 text-sm text-slate-700">
          <span>{tr("Lesson duration")}</span>
          <input
            type="number"
            min={10}
            max={60}
            value={form.lessonDuration}
            onChange={(event) => updateField("lessonDuration", Number(event.target.value))}
            className="w-full rounded-2xl border border-white/70 bg-white/80 px-4 py-3 outline-none"
          />
        </label>

        <div className="space-y-4 md:col-span-2">
          <label className="block space-y-2 text-sm text-slate-700">
            <span>
              {tr("Speaking priority")}: {form.speakingPriority}/10
            </span>
            <input
              type="range"
              min={1}
              max={10}
              value={form.speakingPriority}
              onChange={(event) => updateField("speakingPriority", Number(event.target.value))}
              className="w-full"
            />
          </label>

          <label className="block space-y-2 text-sm text-slate-700">
            <span>
              {tr("Grammar priority")}: {form.grammarPriority}/10
            </span>
            <input
              type="range"
              min={1}
              max={10}
              value={form.grammarPriority}
              onChange={(event) => updateField("grammarPriority", Number(event.target.value))}
              className="w-full"
            />
          </label>

          <label className="block space-y-2 text-sm text-slate-700">
            <span>
              {tr("Profession priority")}: {form.professionPriority}/10
            </span>
            <input
              type="range"
              min={1}
              max={10}
              value={form.professionPriority}
              onChange={(event) => updateField("professionPriority", Number(event.target.value))}
              className="w-full"
            />
          </label>
        </div>
      </Card>

      <Card className="space-y-4">
        <div className="text-lg font-semibold text-ink">{title}</div>
        <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">{description}</div>
        <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
          {`${form.name} ${tr("starts from")} ${form.currentLevel} ${tr("and moves to")} ${form.targetLevel} ${tr("with the")} ${tr(activeTrackTitle)} ${tr("track")}.`}
        </div>
        <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
          {tr("Lesson format")}: {form.lessonDuration} {tr("minutes")}, {tr("explanations in")}{" "}
          {tr(form.preferredExplanationLanguage === "ru" ? "Russian" : "English")}.
        </div>
        <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
          {tr("Priority mix")}: {tr("speaking")} {form.speakingPriority}, {tr("grammar")} {form.grammarPriority},{" "}
          {tr("Profession")} {form.professionPriority}.
        </div>
        <Button onClick={() => void handleSubmit()} className="w-full" disabled={isSaving}>
          {isSaving ? tr("Saving...") : submitLabel}
        </Button>
      </Card>
    </div>
  );
}
