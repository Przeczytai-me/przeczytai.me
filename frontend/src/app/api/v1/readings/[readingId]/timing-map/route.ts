import { type NextRequest, NextResponse } from "next/server";
import { backendFetch } from "@/lib/backend-fetch";

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ readingId: string }> },
) {
  const { readingId } = await params;
  const res = await backendFetch(
    `/api/v1/readings/${encodeURIComponent(readingId)}/timing-map`,
  );
  const text = await res.text();

  if (!text) {
    return new NextResponse(null, { status: res.status });
  }

  try {
    return NextResponse.json(JSON.parse(text), { status: res.status });
  } catch {
    return NextResponse.json({ error: text }, { status: res.status });
  }
}
