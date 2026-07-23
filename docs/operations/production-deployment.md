# JobOps Radar 운영 배포 현황

기준일: 2026-07-23

## 공개 서비스

- 기본 주소: `https://jobjobs.shop`
- 보조 주소: `https://www.jobjobs.shop`
- readiness: `https://jobjobs.shop/health/ready`
- OpenAPI: `https://jobjobs.shop/docs`
- HTTP 요청은 동일 host의 HTTPS 주소로 `301` redirect됩니다.

## 배포 구조

```text
Gabia DNS A record
  -> AWS Elastic IP
  -> EC2 Security Group: 22, 80, 443
  -> Nginx :80/:443
       -> React 정적 파일
       -> FastAPI reverse proxy 127.0.0.1:8000
            -> PostgreSQL Unix socket/127.0.0.1:5432
            -> 외부 LLM provider 또는 deterministic fallback
```

FastAPI 8000과 PostgreSQL 5432는 외부에 공개하지 않습니다. Nginx만 사용자 HTTP 요청을 받습니다.

## 서버 구성

| 항목 | 현재 구성 |
| --- | --- |
| OS | Ubuntu 26.04 LTS |
| application | FastAPI modular monolith |
| process 관리 | `jobops.service` systemd unit |
| reverse proxy | Nginx 1.28 |
| database | PostgreSQL 18.4 |
| frontend | React/Vite production build |
| TLS | Let's Encrypt ECDSA certificate, Certbot |
| 인증서 자동 갱신 | `certbot.timer` enabled·active |

운영 설정 원본은 `deploy/systemd/jobops.service`와 `deploy/nginx/jobops-radar.conf`에 있습니다. 실제 credential과 `.env`는 저장소에 포함하지 않습니다.

## 데이터베이스 전환

- 기존 SQLite DB는 전환 전에 권한 제한 백업으로 보존했습니다.
- 기존 데이터는 개발·시험 데이터로 판단해 PostgreSQL로 이전하지 않았습니다.
- PostgreSQL은 신규 운영 시작점으로 사용합니다.
- application은 로컬 peer 인증과 `postgresql+psycopg:///jobops` 연결을 사용합니다.
- Alembic은 `7a4c92e81f6d`까지 적용됐으며 PostgreSQL `alembic check`에서 model drift가 없습니다.
- PostgreSQL 5432는 `localhost`에서만 listen합니다.

## Query plan 검증

실제 공고 목록 statement와 5만 건의 격리된 benchmark row로 측정했습니다.

| 항목 | index 적용 전 | index 적용 후 |
| --- | ---: | ---: |
| 실행 시간 | 10.480ms | 0.148ms |
| scan | Seq Scan | Index Scan |
| 별도 sort | top-N heapsort | 없음 |

적용 index는 `ix_job_postings_company_active_expiration_id`이며 `(company_name, is_active, expiration_date ASC, id DESC)` 순서입니다. 실험 후 benchmark row 5만 건만 삭제하고 `VACUUM (ANALYZE)`를 실행했습니다. 이 수치는 해당 서버·데이터 분포의 실험 결과이며 일반적인 production latency 보장은 아닙니다.

## 검증 근거

- EC2 `pytest`: 103 passed, upstream deprecation warning 1건
- 빈 SQLite와 PostgreSQL Alembic upgrade: 통과
- PostgreSQL `alembic check`: drift 없음
- `jobops.service`, `nginx`, `postgresql`: active
- 외부 apex·www HTTPS UI: 200
- 외부 HTTPS readiness: 200
- 외부 8000 직접 연결: 차단 확인
- `certbot renew --dry-run`: 성공
- 현재 인증서 만료일: 2026-10-21, 자동 갱신 대상

## 배포 및 점검 명령

서버 application 배포의 기본 순서는 다음과 같습니다.

```bash
cd /home/ubuntu/jobops-radar
git switch main
git pull --ff-only origin main
.venv/bin/python -m pip install -e .
.venv/bin/python -m alembic upgrade head
.venv/bin/python -m alembic check
sudo install -m 644 deploy/systemd/jobops.service /etc/systemd/system/jobops.service
sudo install -m 644 deploy/nginx/jobops-radar.conf /etc/nginx/sites-available/jobops-radar
sudo nginx -t
sudo systemctl daemon-reload
sudo systemctl restart jobops.service
sudo systemctl reload nginx
```

배포 후 최소 점검은 다음과 같습니다.

```bash
systemctl is-active jobops.service nginx postgresql
curl -fsS https://jobjobs.shop/health/live
curl -fsS https://jobjobs.shop/health/ready
sudo certbot renew --dry-run
```

Frontend는 `frontend/`에서 `npm ci`와 `npm run build`로 생성한 `dist/`를 `/var/www/jobops-radar/releases/<release-id>`에 배치하고 `/var/www/jobops-radar/current` symlink를 새 release로 전환합니다. 정적 directory는 755, file은 644 권한을 사용합니다.

## 백업과 복구 지점

- 전환 전 `.env`, systemd unit과 SQLite DB는 EC2의 `/home/ubuntu/jobops-backups/20260723-0030`에 권한 제한 상태로 보존했습니다.
- PostgreSQL 자동 backup과 보존 주기는 아직 구성하지 않았습니다.
- 장애 시 먼저 `/health/live`와 `/health/ready`를 구분하고 `systemctl status`, application log, PostgreSQL log 순서로 확인합니다.
- 인증서 private key, SSH private key, DB credential과 LLM API key는 문서나 Git에 기록하지 않습니다.

## 남은 운영 과제

1. PostgreSQL 정기 backup, 복구 연습과 보존 기간을 정합니다.
2. application secret과 LLM API key의 교체 절차를 정의합니다.
3. 로그인·분석 endpoint의 rate limit과 abuse 방어를 추가합니다.
4. structured log의 fallback reason·latency를 집계하고 disk log rotation을 확인합니다.
5. EC2 메모리 약 1GiB와 swap 0B 조건에서 장기 resource 사용량을 관찰합니다.
6. 실제 사용자 데이터가 생기기 전에 개인정보 보존·삭제 운영 절차를 확정합니다.
