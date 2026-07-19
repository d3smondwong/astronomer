/**
 * FastAPI transport errors + the sanitization boundary between them and the browser.
 *
 * Two jobs, deliberately in one file:
 *   1. `FastApiError` classifies *why* a backend call failed (refused / timed out /
 *      rejected our payload / 5xx) so callers can branch on something better than a
 *      string. Every field on it — including the raw upstream body in `detail` — is
 *      SERVER-ONLY.
 *   2. `toClientError` is the only sanctioned way to turn one of those into an HTTP
 *      response. Route handlers must never put `err.message` in a response body: it
 *      interpolates the raw FastAPI body, which can carry stack traces and internals.
 *
 * NOT unified with `ActionErrorCode` (app/actions/profiles.ts) on purpose. That union
 * describes the outcome of our own authorization logic and is returned as *data*
 * because Server Actions never throw across the boundary; this one describes a
 * transport failure of an external dependency and is *thrown*. Merging them yields a
 * union where half the members are unreachable in each context, which destroys the
 * exhaustive-switch benefit that is the whole point of having a union.
 */

export type FastApiErrorCode =
  /** fetch threw a TypeError — connection refused, DNS failure, no route. */
  | 'upstream_unavailable'
  /** AbortSignal.timeout() fired. */
  | 'upstream_timeout'
  /** 401/403 — our bearer token is wrong. A config bug, never the user's fault. */
  | 'upstream_unauthorized'
  /** Other 4xx — we sent a payload FastAPI rejected. */
  | 'upstream_invalid'
  /** 5xx — the backend broke while handling a request it accepted. */
  | 'upstream_error';

/** Cap on the upstream body kept in `detail`, so a stray HTML error page can't flood logs. */
const MAX_DETAIL_LEN = 500;

export class FastApiError extends Error {
  readonly name = 'FastApiError';

  constructor(
    readonly code: FastApiErrorCode,
    /** e.g. '/v1/chart/natal' — also selects the user-facing noun in toClientError. */
    readonly endpoint: string,
    /** Absent for timeout / network failures, which never got a response. */
    readonly status?: number,
    /** Raw upstream response body. SERVER-ONLY — never send this to a client. */
    readonly detail?: string,
  ) {
    // detail is interpolated into `message` too, so an existing `console.error(err)`
    // keeps printing everything it printed before this class existed.
    super(
      `FastAPI ${endpoint} failed [${code}]` +
        (status !== undefined ? ` status=${status}` : '') +
        (detail ? `: ${detail.slice(0, MAX_DETAIL_LEN)}` : ''),
    );
  }

  /** Classify a non-ok Response. Consumes the body, so call this only when !res.ok. */
  static async fromResponse(endpoint: string, res: Response): Promise<FastApiError> {
    const detail = await res.text().catch(() => '');
    const code: FastApiErrorCode =
      res.status === 401 || res.status === 403
        ? 'upstream_unauthorized'
        : res.status >= 500
          ? 'upstream_error'
          : 'upstream_invalid';
    return new FastApiError(code, endpoint, res.status, detail);
  }

  /** Classify a throw from fetch() itself — no response was ever received. */
  static fromThrown(endpoint: string, err: unknown): FastApiError {
    if (err instanceof FastApiError) return err;

    // AbortSignal.timeout() rejects with a DOMException named 'TimeoutError', NOT
    // 'AbortError'. Matching only on AbortError would misfile every timeout as
    // 'upstream_unavailable' and report the wrong thing to the user.
    const name = err instanceof Error ? err.name : '';
    if (name === 'TimeoutError' || name === 'AbortError') {
      return new FastApiError('upstream_timeout', endpoint);
    }

    // fetch() reports every network failure as a bare TypeError('fetch failed'); the
    // diagnosis lives on err.cause. Verified shapes:
    //   refused host  -> cause.message 'connect ECONNREFUSED 127.0.0.1:8000' (+ cause.code)
    //   blocked port  -> cause.message 'bad port', no cause.code
    // cause.message already embeds the code AND the address, so prefer it whole rather
    // than concatenating cause.code onto it and repeating the code twice.
    const cause = (err as { cause?: { code?: string; message?: string } } | undefined)?.cause;
    const detail =
      cause?.message ?? (err instanceof Error ? err.message : String(err));
    return new FastApiError('upstream_unavailable', endpoint, undefined, detail);
  }
}

export interface ClientError {
  /** Safe, user-facing prose. Never derived from `err.message` or `err.detail`. */
  message: string;
  status: number;
  /** Stable machine-readable code so clients branch without string-matching prose. */
  code: string;
}

/**
 * User-facing vocabulary per endpoint.
 *
 * Copy rules these encode (all three are easy to violate):
 *   1. Never name infrastructure — no "service", "backend", "engine", "server". The
 *      user has no model of a separate FastAPI process and doesn't need one.
 *   2. Keep 命盘 and 解读 distinct. This app uses "chart" for the computed BaZi chart
 *      and "reading" for the LLM insights. Saying "reading" on a chart failure tells
 *      the user their insights broke when their chart broke.
 *   3. Name the recovery action — never a bare "Please try again."
 *
 * `action` is accurate because each endpoint has exactly one caller today:
 * /natal from BaziProfileForm (submit button still on screen), /cycles from the
 * profile timeline (loads on page load, so refresh IS the whole recovery). If an
 * endpoint gains a second caller with a different affordance, make `action` a
 * parameter rather than letting the copy go stale.
 */
const SUBJECT: Record<string, { noun: string; ing: string; inf: string; action: string }> = {
  '/v1/chart/natal': {
    noun: 'chart',
    ing: 'generating',
    inf: 'generate',
    action: 'Please refresh the page and generate it again.',
  },
  '/v1/chart/full': {
    noun: 'chart',
    ing: 'generating',
    inf: 'generate',
    action: 'Please refresh the page and generate it again.',
  },
  '/v1/chart/cycles': {
    noun: 'timeline',
    ing: 'loading',
    inf: 'load',
    // No generate button on the timeline — a refresh is the entire recovery.
    action: 'Please refresh the page.',
  },
  '/v1/chart/insights': {
    noun: 'reading',
    ing: 'generating',
    inf: 'generate',
    action: 'Please refresh the page and generate it again.',
  },
  '/v1/chart/insights/stream': {
    noun: 'reading',
    ing: 'generating',
    inf: 'generate',
    action: 'Please refresh the page and generate it again.',
  },
};

const FALLBACK_SUBJECT = {
  noun: 'request',
  ing: 'completing',
  inf: 'complete',
  action: 'Please refresh the page and try once more.',
};

/**
 * Map any thrown value to a safe HTTP response body.
 *
 * The reason clause varies by status; the action clause stays constant per endpoint.
 * Callers pair this with `console.error(err)` — the log keeps everything, the client
 * gets only this.
 */
export function toClientError(err: unknown): ClientError {
  if (!(err instanceof FastApiError)) {
    return {
      message: 'There is an error generating your chart. Please refresh the page and generate it again.',
      status: 500,
      code: 'internal_error',
    };
  }

  const s = SUBJECT[err.endpoint] ?? FALLBACK_SUBJECT;

  switch (err.code) {
    case 'upstream_timeout':
      return {
        message: `It is taking too long to ${s.inf} your ${s.noun}. ${s.action}`,
        status: 504,
        code: err.code,
      };
    case 'upstream_unavailable':
      return {
        message: `We are not able to ${s.inf} your ${s.noun}. ${s.action}`,
        status: 503,
        code: err.code,
      };
    case 'upstream_invalid':
      // The only case where the user can actually fix the input, so it names the
      // fields rather than the generic action.
      return {
        message:
          'We are not able to process the birth data. Please check the information entered and generate your chart again.',
        status: 400,
        code: err.code,
      };
    case 'upstream_unauthorized':
    // Collapses into the generic 502: a misconfigured FASTAPI_BEARER_TOKEN must never
    // surface as "unauthorized" to a user who IS authorized. Falls through.
    case 'upstream_error':
    default:
      return {
        message: `There is an error ${s.ing} your ${s.noun}. ${s.action}`,
        status: 502,
        code: err.code,
      };
  }
}
