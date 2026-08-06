import { HttpResponse, http, type RequestHandler } from "msw";
import { createMockCostEstimate, mockCostSummary } from "./costs-data";

/**
 * Add development-only backend substitutes here when a frontend feature needs
 * a contract that is not available from the deployed API yet.
 *
 * Cost endpoints use deterministic fixtures until the deployed API is ready.
 */
export const handlers: RequestHandler[] = [
  http.get("/api/v1/costs", ({ request }) => {
    const requestedMonths = Number(
      new URL(request.url).searchParams.get("months") ?? 6,
    );
    const monthCount = Number.isFinite(requestedMonths)
      ? Math.max(1, Math.min(6, Math.trunc(requestedMonths)))
      : 6;
    return HttpResponse.json({
      ...mockCostSummary,
      months: mockCostSummary.months.slice(-monthCount),
    });
  }),
  http.post("/api/v1/costs/estimate", async ({ request }) => {
    const body: unknown = await request.json();
    const originalText =
      typeof body === "object" &&
      body !== null &&
      "original_text" in body &&
      typeof body.original_text === "string"
        ? body.original_text
        : "";
    return HttpResponse.json(createMockCostEstimate(originalText));
  }),
];
