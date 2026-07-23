import { type NextRequest, NextResponse } from "next/server";
import { backendFetch } from "@/lib/backend-fetch";

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ readingId: string }> },
) {
  const { readingId } = await params;
  const res = await backendFetch(
    `/api/v1/readings/${encodeURIComponent(readingId)}/original-text`,
    { redirect: "manual" },
  );

  if (!res.ok) {
    const text = await res.text();
    return NextResponse.json({ error: text }, { status: res.status });
  }

  const headers = new Headers({
    "Content-Type":
      res.headers.get("content-type") || "text/plain; charset=utf-8",
  });
  const contentDisposition = res.headers.get("content-disposition");
  if (contentDisposition) {
    headers.set("Content-Disposition", contentDisposition);
  }

  return new NextResponse(await res.text(), { headers });
}
