# ADR-004: SSRF Defense, Concurrency Locking & Atomic File Storage

## Status
Accepted (2026-11-07)

## Context
InternReach allows users to import external job offers by submitting target URLs (`POST /api/search/import-offer`). The application fetches the external web page and extracts structured job descriptions using either local DOM parsing or LLM extraction.

During security audits, three critical vulnerabilities were uncovered:
1. **Server-Side Request Forgery (SSRF):** An attacker or malicious URL could trigger requests to internal cloud metadata endpoints (`169.254.169.254`), local services (`127.0.0.1:8008/api/settings`), loopback ranges, or private networks (RFC 1918). Standard URL scheme checks were insufficient because attackers could leverage DNS rebinding, IPv4-mapped IPv6 addresses (`::ffff:127.0.0.1`), integer/decimal IP notations, or HTTP 3xx redirect hops pointing to internal destinations.
2. **File Corruption under Concurrent Writes:** The background ingestion worker and user requests concurrently read and write to local JSON files (`jobs.json`, `profile.json`, `history.json`, `settings.json`). Unsynchronized file operations created TOCTOU (Time-of-Check to Time-of-Use) race conditions and partial file writes.
3. **Test Suite Data Mutation:** Running unit tests (`pytest`) directly modified live user files in `backend/app/data/`, erasing candidate resumes and application histories during CI/CD or local test runs.

## Decision

### 1. Multi-Hop SSRF Defense Mechanism
We implemented a strict, multi-layered validation routine in `app/services/job_extractor.py`:
- **Protocol & Port Whitelist:** Only `http` and `https` schemes on standard ports (`80`, `443`) are permitted. Credentials in URLs (`user:pass@host`) are explicitly rejected.
- **DNS Multi-IP Resolution:** Every hostname is resolved via `socket.getaddrinfo`. **All** returned IP addresses are converted into `ipaddress.ip_address` objects and checked against:
  - `is_loopback` (`127.0.0.0/8`, `::1`)
  - `is_private` (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`)
  - `is_link_local` (`169.254.0.0/16`, `fe80::/10`)
  - `is_reserved`, `is_multicast`, `is_unspecified`
  - IPv4-mapped IPv6 representations (`::ffff:127.0.0.1`)
  - Internal domains (`.local`, `.internal`, `.localhost`)
- **Manual Redirect Inspection:** The HTTP client disables automatic redirects (`follow_redirects=False`). Redirect targets (`Location` header) are resolved against the current URL and iteratively re-validated against the SSRF guard for up to 3 hops before the request proceeds.
- **Fail-Fast Error Propagation:** Blocked or invalid URLs immediately raise `ExtractionError` (HTTP 400/422/502). Fake error records are never persisted into `jobs.json`.

### 2. Concurrency Locking & Atomic File Writing
In `app/services/storage.py`:
- We introduced a process-wide reentrant lock (`STORE_LOCK = threading.RLock()`) guarding all read-modify-write operations across stored files.
- Replaced direct `open(..., "w")` with `atomic_write_json()`, which writes data to a temporary file in the same directory using `tempfile.NamedTemporaryFile` and atomically swaps it into place using `os.replace`. This guarantees that crashes never leave half-written or corrupted JSON files.

### 3. Isolated Test Storage Environment
- Added support for the `INTERN_REACH_DATA_DIR` environment variable in `storage.py`.
- Configured an autouse fixture in `tests/conftest.py` that redirects all storage operations to a fresh `tempfile.TemporaryDirectory` during test execution, fully isolating test runs from production data.

## Consequences

### Positive
- **Guaranteed SSRF Immunity:** Internal infrastructure, metadata endpoints, and local microservices are fully protected against direct and redirected SSRF attacks.
- **Zero Data Corruption:** Atomic writes eliminate corrupt JSON files even if the server process terminates abruptly.
- **Zero Test Side Effects:** Developers and CI systems can execute tests at any time without backing up or restoring `backend/app/data/`.
- **Deterministic Job Identity:** Using SHA-1 hashes of canonical URLs for job IDs eliminates ID collision and duplicate React key warnings.

### Trade-offs
- Manual redirect following requires sequential HTTP round-trips (up to 3 hops), adding ~100–300 ms of latency per import request. This is acceptable for user-initiated single-offer imports.
