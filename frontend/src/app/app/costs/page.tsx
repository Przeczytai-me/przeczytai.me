import { notFound } from "next/navigation";
import { backendFetch } from "@/lib/backend-fetch";
import type { CostSummary } from "@/lib/costs-api";
import { CostsDashboard } from "./costs-dashboard";

const MONTHS = 6;

/**
 * Internal cost dashboard. Deliberately absent from appNavigationItems: the
 * route is reachable only by typing the URL.
 *
 * Authorisation happens on the server, before anything renders. Fetching from
 * the client would have served the page shell - heading, description, skeletons -
 * to any signed-in non-admin before the 403 came back, which is itself new
 * information about a feature they cannot use. A non-admin gets the ordinary
 * not-found page instead.
 */
const CostsPage = async () => {
  const response = await backendFetch("/api/v1/costs", {
    searchParams: new URLSearchParams({ months: String(MONTHS) }),
  });
  if (!response.ok) notFound();
  const summary: CostSummary = await response.json();
  return <CostsDashboard summary={summary} months={MONTHS} />;
};

export default CostsPage;
