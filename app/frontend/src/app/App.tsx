import { RouterProvider } from "react-router-dom";
import { router } from "./router";

export function App() {
  return (
    <RouterProvider
      router={router}
      fallbackElement={
        <div className="flex min-h-screen items-center justify-center px-6 text-sm text-slate-600">
          Loading route...
        </div>
      }
    />
  );
}
