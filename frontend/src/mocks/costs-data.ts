import type {
  CostComponents,
  CostEstimate,
  CostEstimateRejection,
  CostMonth,
  CostRun,
  CostSummary,
} from "@/lib/costs-api";

const PRICE_BOOK_VERSION = "2026-08-05";
const MAX_TEXT_CHARS = 100_000;
const MAX_RUN_COST_USD = 0.25;
const MONTHLY_BUDGET_USD = 25;
const MICRO_USD = 1_000_000;

type ComponentMicros = Record<keyof CostComponents, number>;
type FixtureRun = {
  run: CostRun;
  totalMicros: number;
  componentMicros: ComponentMicros;
  voice: string;
  userRef: string;
};

const usd = (micros: number) => micros / MICRO_USD;
const round = (value: number, digits = 6) => Number(value.toFixed(digits));

const toComponents = (components: ComponentMicros): CostComponents => ({
  tts: usd(components.tts),
  llm: usd(components.llm),
  compute: usd(components.compute),
  storage: usd(components.storage),
  platform: usd(components.platform),
});

const splitCost = (totalMicros: number, paidTts: boolean): ComponentMicros => {
  if (totalMicros === 0) {
    return { tts: 0, llm: 0, compute: 0, storage: 0, platform: 0 };
  }

  const tts = paidTts ? Math.floor(totalMicros * 0.94) : 0;
  const compute = Math.floor(totalMicros * (paidTts ? 0.035 : 0.65));
  const storage = Math.floor(totalMicros * (paidTts ? 0.02 : 0.25));
  return {
    tts,
    llm: 0,
    compute,
    storage,
    platform: totalMicros - tts - compute - storage,
  };
};

const addComponents = (
  left: ComponentMicros,
  right: ComponentMicros,
): ComponentMicros => ({
  tts: left.tts + right.tts,
  llm: left.llm + right.llm,
  compute: left.compute + right.compute,
  storage: left.storage + right.storage,
  platform: left.platform + right.platform,
});

const currentDate = new Date();
const currentYear = currentDate.getFullYear();
const currentMonthIndex = currentDate.getMonth();
const currentDay = currentDate.getDate();

const monthKey = (offset: number) => {
  const date = new Date(currentYear, currentMonthIndex + offset, 1);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
};

const isoForDay = (day: number, index: number) =>
  new Date(
    Date.UTC(
      currentYear,
      currentMonthIndex,
      day,
      7 + ((index * 7) % 14),
      (index * 13) % 60,
    ),
  ).toISOString();

const activeDays = Array.from(
  new Set([
    1,
    Math.max(1, currentDay - 3),
    Math.max(1, currentDay - 1),
    currentDay,
  ]),
);
const dayPattern = [0, 1, 1, 2, 3, 3, 3, 3, 1, 3];
const userRefs = [
  "u_4f2a",
  "u_8c11",
  "u_b307",
  "u_19de",
  "u_72aa",
  "u_c548",
  "u_e903",
];

const fixtureRuns: FixtureRun[] = Array.from({ length: 60 }, (_, index) => {
  const vendorSlot = index % 5;
  const vendor =
    vendorSlot <= 2 ? "edge-tts" : vendorSlot === 3 ? "openai" : "elevenlabs";
  const voice =
    vendor === "edge-tts"
      ? index % 2 === 0
        ? "pl-PL-ZofiaNeural"
        : "pl-PL-MarekNeural"
      : vendor === "openai"
        ? index % 2 === 0
          ? "alloy"
          : "nova"
        : index % 2 === 0
          ? "Antoni"
          : "Matilda";
  const charCount =
    index === 58
      ? 96_000
      : vendor === "edge-tts"
        ? 6_000 + ((index * 7_919) % 50_000)
        : vendor === "openai"
          ? 8_000 + ((index * 11_537) % 60_000)
          : 12_000 + ((index * 13_829) % 70_000);
  const totalMicros =
    vendor === "edge-tts"
      ? index % 11 === 0
        ? 0
        : 800 + (index % 5) * 350
      : index === 58
        ? 4_860_000
        : vendor === "openai"
          ? 60_000 + (index % 7) * 34_000
          : 110_000 + (index % 6) * 55_000;
  const componentMicros = splitCost(totalMicros, vendor !== "edge-tts");
  const audioMs = Math.round((charCount * 200) / 3);
  const requestedDay = activeDays[dayPattern[index % dayPattern.length]];
  const day = requestedDay ?? activeDays[activeDays.length - 1];
  const userRef =
    index === 58 ? userRefs[0] : (userRefs[index % 10] ?? userRefs[0]);

  return {
    totalMicros,
    componentMicros,
    voice,
    userRef,
    run: {
      reading_id: `01JMOCKCOST${String(index + 1).padStart(4, "0")}`,
      created_at: isoForDay(day, index),
      vendor,
      char_count: charCount,
      total_usd: usd(totalMicros),
      components: toComponents(componentMicros),
      usage: {
        chars_synthesized: charCount,
        chunks: Math.ceil(charCount / 3_000),
        audio_ms: audioMs,
        stored_bytes: audioMs * 6,
        lambda_memory_mb: index % 4 === 0 ? 512 : 256,
        compute_ms_by_stage: {
          normalize: 25 + (index % 9) * 7,
          synthesize: Math.round(audioMs * 0.015),
          merge: 180 + (index % 8) * 95,
        },
      },
    },
  };
}).sort((left, right) =>
  right.run.created_at.localeCompare(left.run.created_at),
);

const currentComponentMicros = fixtureRuns.reduce(
  (total, item) => addComponents(total, item.componentMicros),
  { tts: 0, llm: 0, compute: 0, storage: 0, platform: 0 },
);
const currentTotalMicros = fixtureRuns.reduce(
  (total, item) => total + item.totalMicros,
  0,
);
const currentChars = fixtureRuns.reduce(
  (total, item) => total + item.run.char_count,
  0,
);
const currentAudioMs = fixtureRuns.reduce(
  (total, item) => total + item.run.usage.audio_ms,
  0,
);

const historicalMonths: Array<Omit<CostMonth, "month">> = [
  {
    total_usd: 3.84,
    components: {
      tts: 3.25,
      llm: 0,
      compute: 0.42,
      storage: 0.11,
      platform: 0.06,
    },
    runs: 92,
    chars: 1_108_420,
    audio_ms: 73_894_667,
  },
  {
    total_usd: 5.2,
    components: {
      tts: 4.5,
      llm: 0,
      compute: 0.51,
      storage: 0.12,
      platform: 0.07,
    },
    runs: 118,
    chars: 1_489_032,
    audio_ms: 99_268_800,
  },
  {
    total_usd: 6.75,
    components: {
      tts: 5.93,
      llm: 0,
      compute: 0.59,
      storage: 0.15,
      platform: 0.08,
    },
    runs: 141,
    chars: 1_781_460,
    audio_ms: 118_764_000,
  },
  {
    total_usd: 5.96,
    components: {
      tts: 5.15,
      llm: 0,
      compute: 0.58,
      storage: 0.15,
      platform: 0.08,
    },
    runs: 129,
    chars: 1_622_755,
    audio_ms: 108_183_667,
  },
  {
    total_usd: 8.41,
    components: {
      tts: 7.43,
      llm: 0,
      compute: 0.7,
      storage: 0.18,
      platform: 0.1,
    },
    runs: 176,
    chars: 2_214_903,
    audio_ms: 147_660_200,
  },
];

const months: CostMonth[] = [
  ...historicalMonths.map((month, index) => ({
    month: monthKey(index - 5),
    ...month,
  })),
  {
    month: monthKey(0),
    total_usd: usd(currentTotalMicros),
    components: toComponents(currentComponentMicros),
    runs: fixtureRuns.length,
    chars: currentChars,
    audio_ms: currentAudioMs,
  },
];

const days = Array.from({ length: currentDay }, (_, index) => {
  const day = index + 1;
  const items = fixtureRuns.filter(
    (item) => new Date(item.run.created_at).getUTCDate() === day,
  );
  return {
    date: isoForDay(day, 0).slice(0, 10),
    total_usd: usd(items.reduce((total, item) => total + item.totalMicros, 0)),
    runs: items.length,
  };
});

const vendorVoices = [
  ["edge-tts", "pl-PL-ZofiaNeural"],
  ["edge-tts", "pl-PL-MarekNeural"],
  ["openai", "alloy"],
  ["openai", "nova"],
  ["elevenlabs", "Antoni"],
  ["elevenlabs", "Matilda"],
] as const;

const vendors = vendorVoices.map(([vendor, voice]) => {
  const items = fixtureRuns.filter(
    (item) => item.run.vendor === vendor && item.voice === voice,
  );
  return {
    vendor,
    voice,
    total_usd: usd(items.reduce((total, item) => total + item.totalMicros, 0)),
    runs: items.length,
    chars: items.reduce((total, item) => total + item.run.char_count, 0),
  };
});

const users = userRefs
  .map((userRef) => {
    const items = fixtureRuns.filter((item) => item.userRef === userRef);
    return {
      user_ref: userRef,
      total_usd: usd(
        items.reduce((total, item) => total + item.totalMicros, 0),
      ),
      runs: items.length,
    };
  })
  .sort((left, right) => right.total_usd - left.total_usd);

const allTimeUsd = round(
  months.reduce((total, month) => total + month.total_usd, 0),
);
const allTimeRuns = months.reduce((total, month) => total + month.runs, 0);
const monthUsd = usd(currentTotalMicros);

export const mockCostSummary: CostSummary = {
  currency: "USD",
  price_book_version: PRICE_BOOK_VERSION,
  budget: {
    monthly_limit_usd: MONTHLY_BUDGET_USD,
    month_spent_usd: monthUsd,
    utilization: round((monthUsd / MONTHLY_BUDGET_USD) * 100, 2),
    thresholds: [50, 80, 95],
    projected_month_usd: round(
      (monthUsd / currentDay) *
        new Date(currentYear, currentMonthIndex + 1, 0).getDate(),
      2,
    ),
  },
  totals: {
    all_time_usd: allTimeUsd,
    month_usd: monthUsd,
    previous_month_usd: months[months.length - 2].total_usd,
    runs_all_time: allTimeRuns,
    runs_month: fixtureRuns.length,
    chars_month: currentChars,
    audio_ms_month: currentAudioMs,
    avg_run_usd: round(allTimeUsd / allTimeRuns),
    usd_per_1k_chars: round((monthUsd / currentChars) * 1_000),
    usd_per_audio_minute: round((monthUsd / currentAudioMs) * 60_000),
    retained_storage_usd_per_month: 0.42,
    active_users_month: users.length,
  },
  months,
  days,
  components: toComponents(currentComponentMicros),
  vendors,
  users,
  runs: fixtureRuns.map((item) => item.run),
  limits: {
    max_text_chars: MAX_TEXT_CHARS,
    max_run_cost_usd: MAX_RUN_COST_USD,
    monthly_budget_usd: MONTHLY_BUDGET_USD,
  },
};

const estimateRejection = (
  charCount: number,
  totalMicros: number,
  vendorMaxChars: number,
): CostEstimateRejection | null => {
  if (charCount > MAX_TEXT_CHARS) {
    return {
      code: "payload_too_large",
      message: `Text must be ${MAX_TEXT_CHARS} characters or fewer`,
    };
  }
  if (charCount > vendorMaxChars) {
    return {
      code: "payload_too_large",
      message: `openai TTS input must be ${vendorMaxChars} characters or fewer`,
    };
  }
  if (usd(totalMicros) > MAX_RUN_COST_USD) {
    return {
      code: "cost_limit_exceeded",
      message: `Estimated cost exceeds the $${MAX_RUN_COST_USD} run limit`,
    };
  }
  return null;
};

export const createMockCostEstimate = (originalText: string): CostEstimate => {
  const charCount = originalText.length;
  const estimatedAudioMs = Math.round((charCount * 200) / 3);
  const estimates = [
    {
      vendor: "edge-tts",
      voice: "pl-PL-ZofiaNeural",
      totalMicros: Math.ceil(charCount * 0.048),
      vendorMaxChars: MAX_TEXT_CHARS,
      paidTts: false,
    },
    {
      vendor: "openai",
      voice: "alloy",
      totalMicros: Math.ceil(charCount * 15.216),
      vendorMaxChars: 4_096,
      paidTts: true,
    },
    {
      vendor: "elevenlabs",
      voice: "Antoni",
      totalMicros: Math.ceil(charCount * 30.5),
      vendorMaxChars: MAX_TEXT_CHARS,
      paidTts: true,
    },
  ];

  return {
    char_count: charCount,
    chunk_count: Math.ceil(charCount / 3_000),
    price_book_version: PRICE_BOOK_VERSION,
    limits: {
      max_text_chars: MAX_TEXT_CHARS,
      max_run_cost_usd: MAX_RUN_COST_USD,
    },
    vendors: estimates.map((estimate) => {
      const rejection = estimateRejection(
        charCount,
        estimate.totalMicros,
        estimate.vendorMaxChars,
      );
      return {
        vendor: estimate.vendor,
        voice: estimate.voice,
        estimated_audio_ms: estimatedAudioMs,
        allowed: rejection === null,
        rejection,
        cost: {
          total_usd: usd(estimate.totalMicros),
          components: toComponents(
            splitCost(estimate.totalMicros, estimate.paidTts),
          ),
        },
      };
    }),
  };
};
