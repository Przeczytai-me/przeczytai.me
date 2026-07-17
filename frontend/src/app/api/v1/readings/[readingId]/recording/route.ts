import { type NextRequest, NextResponse } from "next/server";
import { backendFetch } from "@/lib/backend-fetch";

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ readingId: string }> },
) {
  const { readingId } = await params;
  const res = await backendFetch(`/api/v1/readings/${readingId}/recording`, {
    redirect: "manual",
  });

  // Backend redirects (307) to a presigned S3 URL. Fetch it server-side so the
  // browser receives a same-origin audio response with stable download headers.
  if (res.status >= 300 && res.status < 400) {
    const location = res.headers.get("location");
    if (location) return audioResponse(await fetch(location), readingId);
  }

  if (!res.ok) {
    const text = await res.text();
    return NextResponse.json({ error: text }, { status: res.status });
  }

  const contentType = res.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    const data = await res.json();
    const location = data?.url ?? data?.download_url ?? data?.presigned_url;
    if (location) return audioResponse(await fetch(location), readingId);
    return NextResponse.json(data);
  }

  return audioResponse(res, readingId);
}

async function audioResponse(res: Response, readingId: string) {
  if (!res.ok) {
    const text = await res.text();
    return NextResponse.json({ error: text }, { status: res.status });
  }

  const headers = new Headers({
    "Content-Type": res.headers.get("content-type") || "audio/mpeg",
    "Content-Disposition": `attachment; filename="${readingId}-recording.mp3"`,
  });
  const contentLength = res.headers.get("content-length");
  if (contentLength) headers.set("Content-Length", contentLength);

  return new NextResponse(res.body, { headers });
}
