import http from "k6/http";
import { check } from "k6";

const BASE_URL = __ENV.BASE_URL;
const EMAIL = __ENV.TEST_EMAIL;
const PASSWORD = __ENV.TEST_PASSWORD;

if (!BASE_URL || !EMAIL || !PASSWORD) {
  throw new Error(
    "BASE_URL, TEST_EMAIL, TEST_PASSWORD environment variables are required."
  );
}

export const options = {
  vus: 1,
  iterations: 1,
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
        scenario: "smoke",
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

  if (response.status !== 200) {
    console.error(`status=${response.status}, body=${response.body}`);
  }
}