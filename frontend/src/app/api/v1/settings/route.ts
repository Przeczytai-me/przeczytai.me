import { type NextRequest, NextResponse } from "next/server";
import { backendFetch } from "@/lib/backend-fetch";

export async function GET() {
  return proxySettingsRequest();
}

export async function PUT(req: NextRequest) {
  return proxySettingsRequest(await req.text());
}

async function proxySettingsRequest(body?: string) {
  const res = await backendFetch("/api/v1/settings", {
    method: body === undefined ? "GET" : "PUT",
    body,
  });
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}
