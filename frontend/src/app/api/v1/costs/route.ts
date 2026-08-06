import { type NextRequest, NextResponse } from "next/server";
import { backendFetch } from "@/lib/backend-fetch";

export async function GET(req: NextRequest) {
  const res = await backendFetch("/api/v1/costs", {
    searchParams: req.nextUrl.searchParams,
  });
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}
