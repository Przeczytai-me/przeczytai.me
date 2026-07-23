import { NextResponse } from "next/server";
import { backendFetch } from "@/lib/backend-fetch";

export async function GET() {
  const res = await backendFetch("/api/v1/tts-options");
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}
