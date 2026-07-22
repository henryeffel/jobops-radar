# Normal-login baseline observation

## Environment and scope

The baseline used the normal-login k6 scenario against a single small EC2
instance. The raw client output is retained in
`artifacts/baseline/a1-normal-login-run1.txt`.

## Observed results

- Linux repeatedly OOM-killed the JobOps Python process.
- Kernel logs showed approximately 685 MB RSS for the Python process before it
  was killed.
- The k6 client reported EOF errors.
- systemd repeatedly restarted the process while sustained login traffic
  continued.

No p95 latency, RPS, or post-change improvement value is claimed here.
