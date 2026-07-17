import { type NextRequest, NextResponse } from "next/server";
import { backendFetch } from "@/lib/backend-fetch";

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ readingId: string }> },
) {
  const { readingId } = await params;
  const res = await backendFetch(
    `/api/v1/readings/${readingId}/corrected-text.md`,
    { redirect: "manual" },
  );

  if (res.status >= 300 && res.status < 400) {
    const location = res.headers.get("location");
    if (location) return NextResponse.json({ url: location });
  }

  if (!res.ok) {
    const text = await res.text();
    return NextResponse.json({ error: text }, { status: res.status });
  }

  const contentType = res.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    return NextResponse.json(await res.json());
  }

  return new NextResponse(await res.text(), {
    headers: { "Content-Type": contentType || "text/markdown" },
  });
}
