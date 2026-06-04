import { NextRequest } from "next/server";

const BACKEND = process.env.API_URL ?? "http://localhost:8000";

export async function POST(request: NextRequest) {
  const body = await request.json();

  const upstream = await fetch(`${BACKEND}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  return new Response(upstream.body, {
    status: upstream.status,
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      "Connection": "keep-alive",
      "X-Accel-Buffering": "no",
    },
  });
}
