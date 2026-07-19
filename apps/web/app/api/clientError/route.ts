/**
 * Next.js Route Handler: POST /api/clientError
 *
 * Receives a structured client-side error report (from lib/errorReporter.ts) and writes
 * one structured JSON line to stdout. On Cloud Run that lands in Cloud Logging alongside
 * the backend logs, queryable by field (e.g. jsonPayload.chartKey="…").
 *
 * Intentionally UNAUTHENTICATED so guests' failures (e.g. chart generation) are captured
 * too — the whole point is the full picture. Abuse-hardening (rate limiting) is deferred.
 * Always returns 204 and never throws; a failing reporter must not surface to the user.
 */

import { NextRequest, NextResponse } from 'next/server';

// Defensive cap so an oversized/malformed payload can't bloat the logs.
const MAX_LEN = 2000;

function clip(value: unknown): string | undefined {
  if (typeof value !== 'string') return undefined;
  return value.length > MAX_LEN ? value.slice(0, MAX_LEN) : value;
}

export async function POST(request: NextRequest): Promise<NextResponse> {
  try {
    const body = await request.json();

    // GCP structured-logging convention: top-level `severity` + `message`, with the rest
    // becoming jsonPayload fields you can filter on in Cloud Logging.
    console.error(
      JSON.stringify({
        severity: 'ERROR',
        message: `[client] ${clip(body?.context) ?? 'unknown'}: ${clip(body?.message) ?? ''}`,
        source: 'client',
        context: clip(body?.context),
        requestId: clip(body?.requestId),
        chartKey: clip(body?.chartKey),
        uid: clip(body?.uid),
        profileId: clip(body?.profileId),
        section: clip(body?.section),
        status: typeof body?.status === 'number' ? body.status : undefined,
        // This handler reads a FIXED field list — anything not named here is dropped.
        // digest is the join key from a boundary report to Next's own masked server-side
        // error log; boundary says which error.tsx caught it.
        digest: clip(body?.digest),
        boundary: clip(body?.boundary),
        url: clip(body?.url),
        userAgent: clip(request.headers.get('user-agent') ?? undefined),
        ts: typeof body?.ts === 'number' ? body.ts : Date.now(),
      }),
    );
  } catch {
    /* malformed body / parse error — drop it silently, never fail the report */
  }

  return new NextResponse(null, { status: 204 });
}
