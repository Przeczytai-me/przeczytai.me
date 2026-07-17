import { auth } from "@clerk/nextjs/server";

const BACKEND_API_URL =
  process.env.BACKEND_API_URL ??
  "https://ub4r9j3fl2.execute-api.eu-west-1.amazonaws.com";
const CLERK_API_JWT_TEMPLATE =
  process.env.CLERK_API_JWT_TEMPLATE ?? "przeczytai-api";

type BackendFetchInit = {
  method?: string;
  body?: string;
  redirect?: RequestRedirect;
  searchParams?: URLSearchParams;
  auth?: boolean;
};

/**
 * Server-side fetch helper for the backend API.
 * Automatically injects the Clerk JWT expected by protected backend endpoints.
 * Must only be called from Route Handlers or Server Components.
 */
export async function backendFetch(
  path: string,
  init: BackendFetchInit = {},
): Promise<Response> {
  const headers: Record<string, string> = {};
  if (init.auth !== false) {
    const { getToken } = await auth();
    const token = await getToken({ template: CLERK_API_JWT_TEMPLATE });
    if (token) headers.Authorization = `Bearer ${token}`;
  }
  if (init.body !== undefined) headers["Content-Type"] = "application/json";

  const url =
    init.searchParams && init.searchParams.size > 0
      ? `${BACKEND_API_URL}${path}?${init.searchParams.toString()}`
      : `${BACKEND_API_URL}${path}`;

  return fetch(url, {
    method: init.method ?? "GET",
    body: init.body,
    headers,
    redirect: init.redirect ?? "follow",
  });
}
