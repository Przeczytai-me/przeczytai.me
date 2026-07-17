import { type NextRequest, NextResponse } from "next/server";
import { backendFetch } from "@/lib/backend-fetch";

export async function GET(req: NextRequest) {
  const res = await backendFetch("/api/v1/readings", {
    searchParams: req.nextUrl.searchParams,
  });
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}

export async function POST(req: NextRequest) {
  const body = await req.text();
  const res = await backendFetch("/api/v1/readings", {
    method: "POST",
    body,
  });
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}
