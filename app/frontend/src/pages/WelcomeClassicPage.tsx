import { Navigate } from "react-router-dom";
import { routes } from "../shared/constants/routes";

export function WelcomeClassicPage() {
  return <Navigate to={routes.welcome} replace />;
}
