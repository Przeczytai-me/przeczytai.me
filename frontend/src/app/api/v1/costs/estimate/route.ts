import { type NextRequest, NextResponse } from "next/server";
import { backendFetch } from "@/lib/backend-fetch";

export async function POST(req: NextRequest) {
  const body = await req.text();
  const res = await backendFetch("/api/v1/costs/estimate", {
    method: "POST",
    body,
  });
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}
