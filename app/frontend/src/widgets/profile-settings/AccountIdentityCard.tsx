import { useState } from "react";
import type { UserAccountDraft } from "../../entities/account/model";
import { useLocale } from "../../shared/i18n/useLocale";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";

interface AccountIdentityCardProps {
  title: string;
  description: string;
  account: UserAccountDraft;
  onChange: (account: UserAccountDraft) => void;
  submitLabel?: string;
  onSave?: (account: UserAccountDraft) => Promise<void>;
}

export function AccountIdentityCard({
  title,
  description,
  account,
  onChange,
  submitLabel,
  onSave,
}: AccountIdentityCardProps) {
  const { tr } = useLocale();
  const [isSaving, setIsSaving] = useState(false);
  const isValid = account.login.trim().length >= 3 && account.email.includes("@");

  const handleSave = async () => {
    if (!onSave) {
      return;
    }

    setIsSaving(true);
    try {
      await onSave({
        login: account.login.trim(),
        email: account.email.trim(),
      });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Card className="space-y-4">
      <div className="text-lg font-semibold text-ink">{title}</div>
      <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">{description}</div>
      <div className="grid gap-4 md:grid-cols-2">
        <label className="space-y-2 text-sm text-slate-700">
          <span>{tr("Login")}</span>
          <input
            value={account.login}
            onChange={(event) => onChange({ ...account, login: event.target.value })}
            placeholder={tr("Choose a login")}
            className="w-full rounded-2xl border border-white/70 bg-white/80 px-4 py-3 outline-none"
          />
        </label>
        <label className="space-y-2 text-sm text-slate-700">
          <span>{tr("Email")}</span>
          <input
            type="email"
            value={account.email}
            onChange={(event) => onChange({ ...account, email: event.target.value })}
            placeholder={tr("name@example.com")}
            className="w-full rounded-2xl border border-white/70 bg-white/80 px-4 py-3 outline-none"
          />
        </label>
      </div>
      <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
        {tr("Login and email are stored in the user account table. Learning answers stay in a separate onboarding table.")}
      </div>
      {onSave && submitLabel ? (
        <Button onClick={() => void handleSave()} disabled={isSaving || !isValid}>
          {isSaving ? tr("Saving...") : submitLabel}
        </Button>
      ) : null}
    </Card>
  );
}
