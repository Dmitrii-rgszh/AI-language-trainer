export function resolutionTone(status: string) {
  if (status === "stabilizing") {
    return "bg-mint/40 text-ink";
  }
  if (status === "recovering") {
    return "bg-sand text-ink";
  }
  return "bg-rose-100 text-rose-700";
}
