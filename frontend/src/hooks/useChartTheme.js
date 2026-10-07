import { useTheme } from "../context/ThemeContext";

export function useChartTheme() {
  const { theme } = useTheme();
  const isDark = theme === "dark";

  return {
    isDark,
    axisText:        isDark ? "#94a3b8" : "#64748b",
    axisTextStrong:  isDark ? "#cbd5e1" : "#334155",
    grid:            isDark ? "#1e293b" : "#e2e8f0",
    tooltipBg:       isDark ? "#0f172a" : "#ffffff",
    tooltipBorder:   isDark ? "#1e293b" : "#e2e8f0",
    tooltipText:     isDark ? "#e2e8f0" : "#0f172a",
    sky:             isDark ? "#38bdf8" : "#0ea5e9",
    purple:          isDark ? "#a78bfa" : "#8b5cf6",
    teal:            isDark ? "#2dd4bf" : "#14b8a6",
    amber:           isDark ? "#fbbf24" : "#f59e0b",
    emerald:         isDark ? "#34d399" : "#10b981",
    rose:            isDark ? "#fb7185" : "#ef4444",
  };
}
