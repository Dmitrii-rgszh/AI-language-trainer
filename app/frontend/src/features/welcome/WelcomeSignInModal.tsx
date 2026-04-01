import { Button } from "../../shared/ui/Button";
import { cn } from "../../shared/utils/cn";

type WelcomeSignInModalProps = {
  account: {
    login: string;
    email: string;
  };
  canSubmit: boolean;
  copy: {
    close: string;
    description: string;
    emailLabel: string;
    emailPlaceholder: string;
    loginLabel: string;
    loginPlaceholder: string;
    signingIn: string;
    submit: string;
    title: string;
  };
  error: string | null;
  isOpen: boolean;
  isSubmitting: boolean;
  onClose: () => void;
  onSubmit: () => void;
  setAccount: (updater: (current: { login: string; email: string }) => { login: string; email: string }) => void;
};

export function WelcomeSignInModal({
  account,
  canSubmit,
  copy,
  error,
  isOpen,
  isSubmitting,
  onClose,
  onSubmit,
  setAccount,
}: WelcomeSignInModalProps) {
  if (!isOpen) {
    return null;
  }

  return (
    <div className="welcome-sign-in-modal" role="dialog" aria-modal="true" aria-label={copy.title}>
      <button
        type="button"
        className="welcome-sign-in-modal__backdrop"
        onClick={onClose}
        aria-label={copy.close}
      />
      <div className="welcome-sign-in-modal__panel">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="text-[0.68rem] uppercase tracking-[0.24em] text-coral">{copy.submit}</div>
            <div className="mt-3 text-2xl font-[700] tracking-[-0.03em] text-ink">{copy.title}</div>
            <div className="mt-3 max-w-[28rem] text-sm leading-6 text-slate-600">{copy.description}</div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="rounded-full border border-white/70 bg-white/76 px-3 py-1.5 text-xs font-semibold text-slate-600 transition-colors hover:text-ink"
          >
            {copy.close}
          </button>
        </div>

        <div className="mt-6 grid gap-4 md:grid-cols-2">
          <label className="block">
            <div className="mb-2 text-[0.7rem] font-semibold uppercase tracking-[0.16em] text-slate-500">
              {copy.loginLabel}
            </div>
            <input
              value={account.login}
              onChange={(event) =>
                setAccount((current) => ({ ...current, login: event.target.value }))
              }
              placeholder={copy.loginPlaceholder}
              className="w-full rounded-[20px] border border-white/75 bg-white/78 px-4 py-3 text-sm text-ink outline-none transition-colors placeholder:text-slate-400 focus:border-accent/45"
            />
          </label>

          <label className="block">
            <div className="mb-2 text-[0.7rem] font-semibold uppercase tracking-[0.16em] text-slate-500">
              {copy.emailLabel}
            </div>
            <input
              type="email"
              value={account.email}
              onChange={(event) =>
                setAccount((current) => ({ ...current, email: event.target.value }))
              }
              placeholder={copy.emailPlaceholder}
              className="w-full rounded-[20px] border border-white/75 bg-white/78 px-4 py-3 text-sm text-ink outline-none transition-colors placeholder:text-slate-400 focus:border-accent/45"
            />
          </label>
        </div>

        <div className="mt-4 min-h-[1.5rem] text-sm text-coral">
          {error ? error : null}
        </div>

        <div className="mt-4 flex justify-end gap-3">
          <Button type="button" variant="ghost" onClick={onClose} disabled={isSubmitting}>
            {copy.close}
          </Button>
          <Button
            type="button"
            onClick={onSubmit}
            disabled={!canSubmit}
            className={cn("min-w-[128px]", isSubmitting && "cursor-wait")}
          >
            {isSubmitting ? copy.signingIn : copy.submit}
          </Button>
        </div>
      </div>
    </div>
  );
}
