/**
 * Cost figures span five orders of magnitude: a free edge-tts run costs a
 * fraction of a cent, a month of paid narration costs tens of dollars. Fixed
 * two-decimal formatting would render most real runs as "$0.00", which is a lie
 * rather than a rounding. Precision therefore follows magnitude.
 */
export const formatUsd = (usd: number): string => {
  if (usd === 0) return "$0";
  if (Math.abs(usd) < 0.0001) return "<$0.0001";
  if (Math.abs(usd) < 0.01) return `$${usd.toFixed(4)}`;
  if (Math.abs(usd) < 1) return `$${usd.toFixed(3)}`;
  return `$${usd.toFixed(2)}`;
};

/** Compact form for axis ticks and dense labels, where width is scarce. */
export const formatUsdShort = (usd: number): string => {
  if (usd === 0) return "0";
  if (Math.abs(usd) < 0.01) return usd.toExponential(0).replace("e-", "e-");
  if (Math.abs(usd) < 1) return `$${usd.toFixed(2)}`;
  return `$${Math.round(usd)}`;
};

export const formatCount = (value: number): string =>
  new Intl.NumberFormat("en-US").format(Math.round(value));

export const formatChars = (chars: number): string => {
  if (chars >= 1_000_000) return `${(chars / 1_000_000).toFixed(1)}M`;
  if (chars >= 1_000) return `${(chars / 1_000).toFixed(1)}k`;
  return String(chars);
};

export const formatDurationMs = (ms: number): string => {
  const totalSeconds = Math.round(ms / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  if (hours > 0) return `${hours}h ${minutes}m`;
  if (minutes > 0) return `${minutes}m ${seconds}s`;
  return `${seconds}s`;
};

export const formatBytes = (bytes: number): string => {
  if (bytes >= 1_000_000_000) return `${(bytes / 1_000_000_000).toFixed(2)} GB`;
  if (bytes >= 1_000_000) return `${(bytes / 1_000_000).toFixed(1)} MB`;
  if (bytes >= 1_000) return `${(bytes / 1_000).toFixed(1)} kB`;
  return `${bytes} B`;
};

export const formatMonth = (month: string): string => {
  const [year, monthIndex] = month.split("-");
  const date = new Date(Number(year), Number(monthIndex) - 1, 1);
  return date.toLocaleDateString("en-US", { month: "short", year: "2-digit" });
};

export const formatPercent = (value: number, digits = 0): string =>
  `${value.toFixed(digits)}%`;

export const COST_COMPONENTS = [
  "tts",
  "llm",
  "compute",
  "storage",
  "platform",
] as const;

export type CostComponentKey = (typeof COST_COMPONENTS)[number];

/**
 * Slot order is the validated palette order - see the note in globals.css.
 * Stacks and legends must iterate COST_COMPONENTS so adjacency never drifts.
 */
export const COST_COMPONENT_COLOR: Record<CostComponentKey, string> = {
  tts: "var(--cost-tts)",
  llm: "var(--cost-llm)",
  compute: "var(--cost-compute)",
  storage: "var(--cost-storage)",
  platform: "var(--cost-platform)",
};

export const COST_COMPONENT_LABEL: Record<CostComponentKey, string> = {
  tts: "TTS",
  llm: "LLM",
  compute: "Compute",
  storage: "Storage",
  platform: "Platform",
};

/** Vendors are coloured from the first three slots, which validate all-pairs. */
const VENDOR_SLOTS = [
  "var(--cost-tts)",
  "var(--cost-llm)",
  "var(--cost-compute)",
];

export const vendorColor = (vendor: string, allVendors: string[]): string => {
  const index = allVendors.indexOf(vendor);
  return index >= 0 && index < VENDOR_SLOTS.length
    ? VENDOR_SLOTS[index]
    : "var(--muted-foreground)";
};
