import { useEffect, useMemo, useState } from "react";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";

export type LizaExplainAction = {
  id: string;
  label: string;
  text: string;
};

type LizaExplainActionsProps = {
  actions: LizaExplainAction[];
  title: string;
};

export function LizaExplainActions({
  actions,
  title,
}: LizaExplainActionsProps) {
  const firstActionId = actions[0]?.id ?? null;
  const [activeActionId, setActiveActionId] = useState<string | null>(firstActionId);

  useEffect(() => {
    if (!actions.some((action) => action.id === activeActionId)) {
      setActiveActionId(actions[0]?.id ?? null);
    }
  }, [actions, activeActionId]);

  const activeAction = useMemo(
    () => actions.find((action) => action.id === activeActionId) ?? actions[0] ?? null,
    [actions, activeActionId],
  );

  if (actions.length === 0 || !activeAction) {
    return null;
  }

  return (
    <Card className="space-y-4">
      <div className="text-sm font-semibold text-ink">{title}</div>
      <div className="flex flex-wrap gap-2">
        {actions.map((action) => (
          <Button
            key={action.id}
            type="button"
            variant={action.id === activeAction.id ? "primary" : "secondary"}
            onClick={() => setActiveActionId(action.id)}
            className="rounded-full px-4 py-2 text-xs"
          >
            {action.label}
          </Button>
        ))}
      </div>
      <div className="rounded-[22px] border border-white/70 bg-white/76 p-4 text-sm leading-6 text-slate-700">
        {activeAction.text}
      </div>
    </Card>
  );
}
