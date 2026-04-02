import { isRouteErrorResponse, useNavigate, useRouteError } from "react-router-dom";
import { routes } from "../shared/constants/routes";

function resolveErrorMessage(error: unknown) {
  if (isRouteErrorResponse(error)) {
    return error.data?.message ?? error.statusText ?? "The requested screen could not be loaded.";
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "The requested screen could not be loaded.";
}

export function RouteErrorScreen() {
  const error = useRouteError();
  const navigate = useNavigate();
  const message = resolveErrorMessage(error);

  return (
    <div className="living-depth-shell min-h-screen px-6 py-6 lg:px-8">
      <div className="mx-auto flex min-h-[calc(100vh-3rem)] max-w-[860px] items-center justify-center">
        <div className="glass-panel w-full rounded-[36px] border border-white/70 p-8 shadow-soft backdrop-blur md:p-10">
          <div className="text-[0.72rem] font-semibold uppercase tracking-[0.18em] text-coral">
            Route Error
          </div>
          <h1 className="mt-4 max-w-[28rem] text-3xl font-[700] leading-tight tracking-[-0.04em] text-ink md:text-4xl">
            This screen did not load correctly.
          </h1>
          <p className="mt-4 max-w-[34rem] text-base leading-7 text-slate-600">
            {message}
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="rounded-[22px] bg-ink px-5 py-3 text-sm font-[700] text-white shadow-[0_16px_34px_rgba(29,42,56,0.12)] transition-colors hover:bg-ink/92"
            >
              Reload page
            </button>
            <button
              type="button"
              onClick={() => navigate(routes.welcome, { replace: true })}
              className="rounded-[22px] border border-white/70 bg-white/76 px-5 py-3 text-sm font-[700] text-ink transition-colors hover:bg-white"
            >
              Go to welcome
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
