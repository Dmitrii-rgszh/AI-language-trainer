import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import type { UserAccountDraft } from "../../entities/account/model";
import { routes } from "../../shared/constants/routes";
import { ApiError } from "../../shared/api/client";
import { useAppStore } from "../../shared/store/app-store";

type WelcomeSignInCopy = {
  accountPrompt: string;
  accountPromptCompact: string;
  continueWithAccount: string;
  title: string;
  description: string;
  close: string;
  loginLabel: string;
  emailLabel: string;
  loginPlaceholder: string;
  emailPlaceholder: string;
  submit: string;
  signingIn: string;
  accountMissing: string;
  genericError: string;
};

export function useWelcomeSignIn(
  locale: "ru" | "en",
) {
  const navigate = useNavigate();
  const signIn = useAppStore((state) => state.signIn);
  const [isOpen, setIsOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [account, setAccount] = useState<UserAccountDraft>({
    login: "",
    email: "",
  });

  const copy = useMemo<WelcomeSignInCopy>(
    () =>
      locale === "ru"
        ? {
            accountPrompt: "Уже есть аккаунт?",
            accountPromptCompact: "Есть аккаунт?",
            continueWithAccount: "Войти",
            title: "Войти в аккаунт",
            description: "Введи логин и email, чтобы восстановить своё учебное пространство на этом устройстве.",
            close: "Закрыть",
            loginLabel: "Логин",
            emailLabel: "Почта",
            loginPlaceholder: "Твой логин",
            emailPlaceholder: "name@example.com",
            submit: "Войти",
            signingIn: "Выполняю вход...",
            accountMissing: "Мы не нашли аккаунт с таким сочетанием логина и email.",
            genericError: "Не получилось выполнить вход. Попробуй ещё раз.",
          }
        : {
            accountPrompt: "Already have an account?",
            accountPromptCompact: "Have an account?",
            continueWithAccount: "Sign in",
            title: "Sign in",
            description: "Use your login and email to restore your learning workspace on this device.",
            close: "Close",
            loginLabel: "Login",
            emailLabel: "Email",
            loginPlaceholder: "Your login",
            emailPlaceholder: "name@example.com",
            submit: "Sign in",
            signingIn: "Signing in...",
            accountMissing: "We could not find an account with this login and email.",
            genericError: "We could not sign you in. Please try again.",
          },
    [locale],
  );

  const canSubmit = account.login.trim().length >= 3 && account.email.includes("@") && !isSubmitting;

  const open = () => {
    setError(null);
    setIsOpen(true);
  };

  const close = () => {
    if (isSubmitting) {
      return;
    }

    setIsOpen(false);
    setError(null);
  };

  const submit = async () => {
    if (!canSubmit) {
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const result = await signIn(account);
      setIsOpen(false);
      navigate(result.needsOnboarding ? routes.onboarding : routes.dashboard);
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) {
        setError(copy.accountMissing);
      } else {
        setError(copy.genericError);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return {
    account,
    canSubmit,
    close,
    copy,
    error,
    isOpen,
    isSubmitting,
    open,
    setAccount,
    submit,
  };
}
