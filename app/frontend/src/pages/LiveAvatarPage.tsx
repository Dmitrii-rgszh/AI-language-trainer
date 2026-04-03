import { Link } from "react-router-dom";
import { LiveAvatarScreen } from "../features/live-avatar/LiveAvatarScreen";
import { routes } from "../shared/constants/routes";
import { Card } from "../shared/ui/Card";
import { SectionHeading } from "../shared/ui/SectionHeading";

export function LiveAvatarPage() {
  return (
    <div className="space-y-4">
      <Card className="space-y-3">
        <SectionHeading
          eyebrow="Live Avatar Test Mode"
          title="Streaming avatar test screen"
          description="Это отдельный тестовый экран live WebRTC режима с потоковым audio/video и lip sync. Основной вход для гостя остаётся через welcome-страницу."
        />
        <div className="flex flex-wrap gap-3 text-sm font-[700]">
          <Link
            to={routes.welcome}
            className="rounded-2xl border border-white/70 bg-white/76 px-4 py-2.5 text-ink transition-colors hover:bg-white"
          >
            Open welcome funnel
          </Link>
          <Link
            to={routes.onboarding}
            className="rounded-2xl bg-accent px-4 py-2.5 text-white transition-colors hover:bg-teal-700"
          >
            Go to onboarding
          </Link>
        </div>
      </Card>
      <LiveAvatarScreen />
    </div>
  );
}
