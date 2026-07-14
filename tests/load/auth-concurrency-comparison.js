import http from "k6/http";
import { check, sleep } from "k6";
import { Counter } from "k6/metrics";

const BASE_URL = __ENV.BASE_URL;
const EMAIL = __ENV.TEST_EMAIL;
const PASSWORD = __ENV.TEST_PASSWORD;

const status200 = new Counter("auth_status_200");
const status503 = new Counter("auth_status_503");
const statusOther = new Counter("auth_status_other");

if (!BASE_URL || !EMAIL || !PASSWORD) {
  throw new Error(
    "BASE_URL, TEST_EMAIL, TEST_PASSWORD environment variables are required."
  );
}

export const options = {
  scenarios: {
    auth_concurrency_comparison: {
      executor: "ramping-vus",
      startVUs: 0,
      stages: [
        { duration: "30s", target: 1 },
        { duration: "1m", target: 1 },

        { duration: "30s", target: 2 },
        { duration: "1m", target: 2 },

        { duration: "30s", target: 5 },
        { duration: "1m", target: 5 },

        { duration: "30s", target: 10 },
        { duration: "1m", target: 10 },

        { duration: "30s", target: 15 },
        { duration: "1m", target: 15 },

        { duration: "30s", target: 0 },
      ],
      gracefulRampDown: "30s",
    },
  },

  thresholds: {
    checks: ["rate>0.99"],
    auth_status_other: ["count==0"],
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
        scenario: "auth_concurrency_comparison",
        endpoint: "auth_login",
      },
    }
  );

  if (response.status === 200) {
    status200.add(1);
  } else if (response.status === 503) {
    status503.add(1);
  } else {
    statusOther.add(1);
  }

  check(response, {
    "status is 200 or 503": (r) =>
      r.status === 200 || r.status === 503,

    "no 500": (r) =>
      r.status !== 500,
  });

  sleep(1);
}