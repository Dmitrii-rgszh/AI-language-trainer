import { useEffect, useState } from "react";
import type { UserAccountDraft } from "../../entities/account/model";
import { ApiError, apiClient } from "../../shared/api/client";

export type LoginCheckState = {
  status: "idle" | "checking" | "available" | "taken" | "existing_account" | "error";
  suggestions: string[];
};

export type EmailCheckState = {
  status: "idle" | "valid" | "invalid";
};

function isValidEmail(value: string) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}

export function useAccountAvailability(account: UserAccountDraft) {
  const [loginCheck, setLoginCheck] = useState<LoginCheckState>({
    status: "idle",
    suggestions: [],
  });
  const [emailCheck, setEmailCheck] = useState<EmailCheckState>({
    status: "idle",
  });

  useEffect(() => {
    const trimmedEmail = account.email.trim();

    if (trimmedEmail.length === 0) {
      setEmailCheck({ status: "idle" });
      return;
    }

    setEmailCheck({
      status: isValidEmail(trimmedEmail) ? "valid" : "invalid",
    });
  }, [account.email]);

  useEffect(() => {
    const trimmedLogin = account.login.trim();
    const trimmedEmail = account.email.trim();

    if (trimmedLogin.length === 0 || trimmedLogin.length < 3) {
      setLoginCheck({ status: "idle", suggestions: [] });
      return;
    }

    let cancelled = false;
    const timeoutId = window.setTimeout(async () => {
      setLoginCheck((current) => ({ ...current, status: "checking" }));

      try {
        const result = await apiClient.checkLoginAvailability({
          login: trimmedLogin,
          email: trimmedEmail.length >= 5 ? trimmedEmail : undefined,
        });

        if (cancelled) {
          return;
        }

        setLoginCheck({
          status: result.status,
          suggestions: result.suggestions,
        });
      } catch (error) {
        if (cancelled) {
          return;
        }

        if (error instanceof ApiError && error.status === 422) {
          setLoginCheck({ status: "idle", suggestions: [] });
          return;
        }

        setLoginCheck({ status: "error", suggestions: [] });
      }
    }, 320);

    return () => {
      cancelled = true;
      window.clearTimeout(timeoutId);
    };
  }, [account.email, account.login]);

  return {
    loginCheck,
    emailCheck,
    emailIsValid: isValidEmail(account.email.trim()),
  };
}
