export const PROJECT_GOAL_KM = 9000;
export function projectProgress(total) {
  const parsed = Number(total);
  const confirmed = Number.isFinite(parsed) ? Math.max(0, Math.round(parsed * 100)) : 0;
  const target = PROJECT_GOAL_KM * 100;
  return {remaining: Math.max(0, target - confirmed) / 100, completed: Math.min(confirmed, target) / 100};
}
export const distanceLabel = value => value.toLocaleString('ru-RU', {maximumFractionDigits: 2});
