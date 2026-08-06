import type { RequestHandler } from "msw";

/**
 * Add development-only backend substitutes here when a frontend feature needs
 * a contract that is not available from the deployed API yet.
 *
 * All current /api/v1 contracts are implemented by the backend, so the worker
 * intentionally starts without active request handlers.
 */
export const handlers: RequestHandler[] = [];
