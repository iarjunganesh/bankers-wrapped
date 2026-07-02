/**
 * k6 smoke/load test (WS-5) — run manually, NOT in CI.
 *
 * Verifies under concurrency:
 *   1. /api/v1/health p95 latency stays under 500 ms
 *   2. an unknown recap id returns a clean 404 (exercises the B2 fallback path)
 *   3. the rate limiter answers /generate abuse with 429s, never 5xx
 *
 * Usage:
 *   k6 run tests/load/k6_smoke.js                          # against localhost:8000
 *   k6 run -e BASE_URL=https://<railway-url> tests/load/k6_smoke.js
 *
 * Install k6: https://k6.io/docs/get-started/installation/ (winget install k6)
 */

import http from "k6/http";
import { check, group } from "k6";

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";

export const options = {
  scenarios: {
    health: {
      executor: "ramping-vus",
      exec: "health",
      startVUs: 0,
      stages: [
        { duration: "20s", target: 20 },
        { duration: "30s", target: 20 },
        { duration: "10s", target: 0 },
      ],
    },
    rate_limit: {
      executor: "constant-vus",
      exec: "rateLimit",
      vus: 3,
      duration: "30s",
      startTime: "10s",
    },
  },
  thresholds: {
    "http_req_duration{scenario:health}": ["p(95)<500"],
    // Rate-limited requests must be rejected gracefully, not crash the app
    "checks{scenario:rate_limit}": ["rate>0.99"],
  },
};

export function health() {
  group("health + recap 404", () => {
    const res = http.get(`${BASE_URL}/api/v1/health`);
    check(res, {
      "health is 200": (r) => r.status === 200,
      "health says ok": (r) => r.json("status") === "ok",
    });

    const missing = http.get(`${BASE_URL}/api/v1/recap/k6-smoke-nonexistent-id`);
    check(missing, { "unknown recap is 404 (not 5xx)": (r) => r.status === 404 });
  });
}

export function rateLimit() {
  // Tiny valid CSV upload; after 5/hr/IP the limiter must return 429
  const csv = "date,description,amount\n2026-01-01,Salary,1000.0\n";
  const res = http.post(`${BASE_URL}/api/v1/recap/generate`, {
    file: http.file(csv, "k6.csv", "text/csv"),
  });
  check(res, {
    "generate is 202 or 429, never 5xx": (r) => r.status === 202 || r.status === 429,
  });
}
