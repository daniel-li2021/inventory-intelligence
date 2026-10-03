# Hosted synthetic Decision Lab plan

Status: executable readiness work; no cloud resource, domain, deployment, paid
subscription or public availability has been created. Implementation starts from
`origin/main` at `f6d3d16`; the accessibility changes in PR 18 remain an unmerged
prerequisite for the eventual public release. This is a portfolio demo, not an
operational inventory service.

## Architecture and reusable boundaries

Use the existing packaged Lab UI, synthetic archive and same-origin FastAPI API.
A separate hosted ASGI entry point adds bounded anonymous API admission and body
reading, restricts exposed paths, and attaches browser security headers. The
local entry point and all inventory/planner/simulator contracts remain unchanged.
No database, model API, upload, source correction or order execution is added.

A single Linux host runs two containers with Compose: Caddy serves HTTPS and
proxies to one Uvicorn process on a private Docker network. Only ports 80/443 are
published. This keeps one instance's admission state explicit and avoids a new
cloud SDK, orchestrator, database or autoscaling architecture.

| Boundary | Initial configuration / rationale |
|---|---|
| Scenario payload | 4,096 bytes, including chunked reads; 5-second total body deadline |
| Expensive API admission | One process-wide token bucket, 2 requests/second, burst 20; no stored IP identities |
| Active API requests | At most 4; excess returns 503 immediately |
| Uvicorn | One worker, concurrency limit 16, backlog 32, keep-alive 5 seconds |
| App container | Non-root; read-only filesystem; 0.5 CPU, 256 MiB RAM, 64 PIDs; no secrets/host mounts |
| Proxy | 0.25 CPU, 128 MiB RAM; persistent certificate storage; bounded log rotation |
| Restart | `unless-stopped`; readiness checks identify invalid evidence, but Docker health alone does not restart unhealthy processes |
| Access | Same-origin public synthetic GET/POST only; no API docs, source upload, arbitrary files or external evidence import |

Limits are initial operating choices, not demonstrated production capacity.
Global rate limiting can let one abusive visitor consume the shared allowance;
it bounds admitted calculation work, not bandwidth/TLS attack traffic. Host or
provider controls are still required for sustained abuse. One process is a
portfolio availability tradeoff, not high availability. CPU/RAM enforcement and
restart behavior must be tested on the actual container runtime.

Caddy's [automatic HTTPS](https://caddyserver.com/docs/automatic-https) needs a
real domain pointing at the host, reachable ports 80/443 and persistent writable
certificate storage. [Body limits](https://caddyserver.com/docs/caddyfile/directives/request_body)
are also applied at the proxy. Uvicorn's
[concurrency settings](https://www.uvicorn.org/settings/) reject excess connections
with 503; they do not impose a hard deadline on synchronous calculation.
[Compose service controls](https://docs.docker.com/reference/compose-file/services/)
configure the containers. The
[Docker build context allowlist](https://docs.docker.com/build/concepts/context/)
keeps raw public-sales caches, credentials, Git history and local environments out
of the build context.

## Cost and release decision

Do not choose a provider from an unverified old price. Before provisioning,
record the selected region/provider, current host quote, tax/egress/storage/log
charges, domain cost, monthly total and shutdown steps. Proposed budget ceiling:
**USD 10/month recurring infrastructure**, excluding an already owned domain;
this is a proposed limit, not an observed quote or authorization to spend.
If a suitable host is unavailable within that ceiling, retain the local demo and
publish the case study/video or select a separately approved budget.

No deployment is needed to finish the local readiness package. A concrete host,
domain and reviewed cost must be selected before provisioning; automatic merge
approval is currently a separate unresolved gate. The project owner should
approve the prepared host/cost/deployment result as the final external action.

## Implementation and acceptance sequence

1. Commit this architecture/boundary before implementing the hosted entry point.
2. Exercise normal, invalid, incomplete and zero-demand scenarios through the
   hosted entry point. Confirm exact baseline/scenario JSON equals the existing
   local app for valid requests; preserve null blocked business quantities.
3. Independently exercise declared and chunked oversized bodies, slow-body
   deadline, rate replenishment, concurrent saturation/recovery, disconnects,
   restricted paths and browser headers. No database or model API call occurs.
4. Build the container from the allowlisted context. Record Git commit, pinned
   base-image digests, installed dependency versions, artifact/evidence hashes
   and image digest. Verify non-root identity, read-only writes failing, no raw
   cache/credential inclusion, health check and actual CPU/RAM/PID limits.
5. Validate Compose and Caddy configurations on the chosen runtime; verify only
   proxy ports are exposed. Confirm unhealthy status versus crash/restart
   behavior separately. Stop/start preserves the certificate volume.
6. After host/domain/cost approval, deploy the pinned image. Verify trusted HTTPS,
   HTTP redirect, baseline + spike + delay + blocked + zero cases, downloads,
   keyboard/mobile access, and error/recovery through the public URL. Integrate
   and recheck PR 18 before release. Record response status/bytes and archived
   build/evidence identities, not just a successful deployment command.
7. Recreate the app and kill its process; demonstrate recovery. Test overload
   behavior and bounded logs. Observe one day of actual external uptime before
   claiming availability. Keep the last validated image digest for rollback.

## Operations and rollback

The demo has no operational data backups. Preserve Caddy certificate/config
volumes and the exact release/image/evidence manifest. Logs rotate locally;
access logging is disabled initially so IPs and query strings are not retained.
Owner checks aggregate errors/health when the demo is actually operated; no
monitor/recurring automation is created by this package. A broken evidence
archive must yield blocked output or 503, never a synthetic successful fallback.

Rollback uses the previously recorded app image digest with the same proxy
configuration, then repeats the public baseline and blocked checks. Shutdown
stops Compose, closes ingress and terminates the selected host after preserving
release metadata and certificate material as needed. Avoid deleting unrelated
resources or changing the core PostgreSQL demo.

## Known gates

The current macOS workspace has no Docker command/runtime. Local ASGI/live HTTP
acceptance can proceed; container build, Compose/Caddy runtime validation,
Linux resource enforcement and restart tests remain **unverified** until a
runtime is available. No host, domain or paid budget has been selected. Public
TLS, public uptime, release integration and production-scale capacity remain
unverified. Those gates do not block the other independent research packages.
