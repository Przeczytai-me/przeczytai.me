import { setupWorker } from "msw/browser";
import { handlers } from "./handlers";

const worker = setupWorker(...handlers);
let startPromise: ReturnType<typeof worker.start> | undefined;

export const startMockWorker = () => {
  if (!startPromise) {
    startPromise = worker
      .start({ onUnhandledRequest })
      .catch((error: unknown) => {
        startPromise = undefined;
        throw error;
      });
  }
  return startPromise;
};

const realApiRoutes = [
  { method: "GET", path: /^\/api\/v1\/health$/ },
  { method: "GET", path: /^\/api\/v1\/readings$/ },
  { method: "POST", path: /^\/api\/v1\/readings$/ },
  { method: "GET", path: /^\/api\/v1\/jobs$/ },
  { method: "GET", path: /^\/api\/v1\/readings\/[^/]+$/ },
  { method: "DELETE", path: /^\/api\/v1\/readings\/[^/]+$/ },
  {
    method: "POST",
    path: /^\/api\/v1\/readings\/[^/]+\/retry$/,
  },
  {
    method: "GET",
    path: /^\/api\/v1\/readings\/[^/]+\/original-text$/,
  },
  {
    method: "GET",
    path: /^\/api\/v1\/readings\/[^/]+\/timing-map$/,
  },
  { method: "GET", path: /^\/api\/v1\/readings\/[^/]+\/recording$/ },
  {
    method: "GET",
    path: /^\/api\/v1\/readings\/[^/]+\/corrected-text$/,
  },
  { method: "GET", path: /^\/api\/v1\/settings$/ },
  { method: "PUT", path: /^\/api\/v1\/settings$/ },
  { method: "GET", path: /^\/api\/v1\/tts-options$/ },
];

function onUnhandledRequest(request: Request, print: { warning: () => void }) {
  const url = new URL(request.url);
  if (url.origin !== window.location.origin) return;

  const isRealEndpoint = realApiRoutes.some(
    (route) => route.method === request.method && route.path.test(url.pathname),
  );
  if (isRealEndpoint) return;
  if (url.pathname.startsWith("/api/v1/")) print.warning();
}
