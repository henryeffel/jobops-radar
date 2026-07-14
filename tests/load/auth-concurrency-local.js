import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  vus: 5,
  duration: "30s",
};

export default function () {
  const response = http.post(
    "http://127.0.0.1:8000/auth/login",
    JSON.stringify({
      email: "loadtest@example.com",
      password: "LoadTest123!",
    }),
    {
      headers: {
        "Content-Type": "application/json",
      },
      timeout: "10s",
    }
  );

  check(response, {
    "status is 200 or 503": (r) => r.status === 200 || r.status === 503,
    "no 500": (r) => r.status !== 500,
  });

  sleep(1);
}