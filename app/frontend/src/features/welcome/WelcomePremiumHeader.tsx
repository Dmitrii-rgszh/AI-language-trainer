import type { ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { readStoredActiveUserId } from "../../shared/auth/active-user";
import { routes } from "../../shared/constants/routes";
import type { AppLocale } from "../../shared/i18n/locale";
import { BrandLogo } from "../../shared/ui/BrandLogo";
import { cn } from "../../shared/utils/cn";

type LocaleOption = {
  value: AppLocale;
  label: string;
  flagClass: string;
};

type WelcomePremiumHeaderProps = {
  accountPrompt: string;
  accountPromptCompact: string;
  continueWithAccount: string;
  heroVisible: boolean;
  locale: AppLocale;
  localeOptions: LocaleOption[];
  navSlot?: ReactNode;
  onOpenSignIn: () => void;
  setLocale: (locale: AppLocale) => void;
  tr: (value: string) => string;
};

export function WelcomePremiumHeader({
  accountPrompt,
  accountPromptCompact,
  continueWithAccount,
  heroVisible,
  locale,
  localeOptions,
  navSlot,
  onOpenSignIn,
  setLocale,
  tr,
}: WelcomePremiumHeaderProps) {
  const navigate = useNavigate();

  const handleBrandClick = () => {
    navigate(readStoredActiveUserId() ? routes.dashboard : routes.welcome);
  };

  return (
    <div className="welcome-premium-header-shell">
      <div className="welcome-premium-header__fixed">
        <header className={cn("welcome-premium-header welcome-reveal", heroVisible && "is-visible")}>
          <div className="welcome-premium-header__row">
            <div className="welcome-premium-header__brand-stack">
              <button
                type="button"
                onClick={handleBrandClick}
                className="welcome-premium-header__brand-object"
                aria-label={tr("Open dashboard")}
              >
                <BrandLogo className="w-[108px] sm:w-[118px] lg:w-[128px]" />
              </button>
            </div>

            <div className="welcome-premium-header__utility">
              <div className="welcome-premium-header__account-entry">
                <span className="welcome-premium-header__account-copy">{accountPrompt}</span>
                <span className="welcome-premium-header__account-copy--compact">{accountPromptCompact}</span>
                <button
                  type="button"
                  onClick={onOpenSignIn}
                  className="welcome-premium-header__account-button"
                >
                  {continueWithAccount}
                </button>
              </div>

              <div className="welcome-premium-header__language-chip">
                {localeOptions.map((targetLocale) => (
                  <button
                    key={targetLocale.value}
                    type="button"
                    onClick={() => setLocale(targetLocale.value)}
                    className={cn(
                      "flex items-center gap-1.5 rounded-full px-3 py-1.5 text-[0.68rem] font-semibold uppercase tracking-[0.14em] transition-colors",
                      locale === targetLocale.value
                        ? "bg-white text-ink shadow-[0_8px_18px_rgba(29,42,56,0.08)]"
                        : "text-slate-500 hover:text-ink",
                    )}
                    aria-label={`${tr("Interface language")}: ${tr(targetLocale.label)}`}
                  >
                    <span className={cn("locale-flag", targetLocale.flagClass)} aria-hidden="true">
                      {targetLocale.value === "en" ? <span className="locale-flag__canton" /> : null}
                    </span>
                    <span>{tr(targetLocale.label)}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {navSlot ? <div className="welcome-premium-header__nav-slot">{navSlot}</div> : null}
        </header>
      </div>
    </div>
  );
}
