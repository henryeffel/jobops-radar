import http from "k6/http";
import { check, sleep } from "k6";

const BASE_URL = __ENV.BASE_URL;
const EMAIL = __ENV.TEST_EMAIL;
const PASSWORD = __ENV.TEST_PASSWORD;

if (!BASE_URL || !EMAIL || !PASSWORD) {
  throw new Error(
    "BASE_URL, TEST_EMAIL, TEST_PASSWORD environment variables are required."
  );
}

export const options = {
  scenarios: {
    normal_login_baseline: {
      executor: "ramping-vus",
      startVUs: 0,
      stages: [
        { duration: "1m", target: 10 },
        { duration: "2m", target: 10 },

        { duration: "1m", target: 30 },
        { duration: "2m", target: 30 },

        { duration: "1m", target: 50 },
        { duration: "2m", target: 50 },

        { duration: "1m", target: 0 },
      ],
      gracefulRampDown: "30s",
    },
  },

  thresholds: {
    checks: ["rate>0.99"],
    http_req_failed: ["rate<0.01"],
  },
};

export default function () {
  const response = http.post(
    `${BASE_URL}/auth/login`,
    JSON.stringify({
      email: EMAIL,
      password: PASSWORD,
    }),
    {
      headers: {
        "Content-Type": "application/json",
      },
      timeout: "10s",
      tags: {
        scenario: "normal_login",
        endpoint: "auth_login",
      },
    }
  );

  check(response, {
    "status is 200": (r) => r.status === 200,
    "access token exists": (r) => {
      try {
        return Boolean(r.json("access_token"));
      } catch {
        return false;
      }
    },
  });

  sleep(1);
}