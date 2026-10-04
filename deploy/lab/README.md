# Hosted Lab readiness package

Start with the [architecture, cost boundary and release gates](README.md#serving-architecture-and-limits).
This package prepares a public synthetic demo; **nothing is deployed**. The local
`lab_api:app` remains available. Hosted serving uses `lab_hosted:app`, one process,
4 KiB scenario bodies / five-second read deadline, a global burst-20 / 2-per-second
API allowance and four active API requests. Admission limits return 429/503 and
do not change inventory arithmetic or create writes.

## Local HTTP entry point

In the existing Python 3.12 environment with `.[lab]` installed:

```sh
python -m uvicorn inventory_intelligence.lab_hosted:app --host 127.0.0.1 --port 8000 \
  --workers 1 --limit-concurrency 16 --backlog 32 --timeout-keep-alive 5 \
  --no-access-log --no-proxy-headers
python -m scripts.check_hosted_lab --base-url http://127.0.0.1:8000
```

The HTTP checker verifies 13 responses against independently stated baseline,
spike, hidden-delay, incomplete-evidence and zero-demand expectations, plus source
archive identity, strict type rejection, oversized-body rejection, restricted docs
and browser headers. It performs bounded synthetic POSTs, not inventory actions.
For a real release use HTTPS; `--ca-file` is only for an explicit test/private CA.

API and index responses use `no-store`; exact asset paths may cache for one hour.
No API documentation, arbitrary static paths or uploads are exposed. CSP permits
same-origin scripts and same-origin/inline styles because charts set CSS custom
properties; it does not permit inline scripts. Reverse-proxy errors receive the
same browser headers, including the body-limit 413 response. Caddy adds a one-day
HSTS policy; longer policy should follow a successful real HTTPS release.

## Container preparation on a Docker-capable machine

The repository-root build context uses `Dockerfile.dockerignore` beside the chosen
Dockerfile. It includes only package sources/assets, pyproject/README, the two
packaged SQL files and the deployment-only dependency constraints. Raw caches,
.env files, credentials, Git history, tests, other deployment files and local
Python environments are excluded. No broad host bind mount is used by the app.

```sh
docker build -f deploy/lab/Dockerfile -t inventory-lab:local .
LAB_DOMAIN=demo.example.com docker compose -f deploy/lab/compose.yaml config
LAB_DOMAIN=demo.example.com docker compose -f deploy/lab/compose.yaml run --rm --no-deps \
  --entrypoint caddy proxy validate --config /etc/caddy/Caddyfile --adapter caddyfile
```

`demo.example.com` is a documentation placeholder; config validation is not a
public deployment. Python 3.12.14 and Caddy 2.10.2 manifest digests are pinned and
[registry bytes were independently hashed](../../docs/review/hosted-lab-image-manifests.json).
All 18 runtime dependency versions are frozen to the accepted local environment
in `requirements.txt`; Linux availability/build remains to be checked. The built
app image digest is still unknown until a container build succeeds. Record it,
the release commit and synthetic evidence digest in a release manifest. Rebuilds
should update the recorded result rather than claim byte-identical wheels/images.

After the reviewed host/domain/cost decision and actual container acceptance:

```sh
export LAB_DOMAIN=your-reviewed-domain.example
export LAB_IMAGE=your-registry/inventory-lab@sha256:your-validated-image-digest
docker compose -f deploy/lab/compose.yaml up -d --no-build --wait
python -m scripts.check_hosted_lab --base-url "https://$LAB_DOMAIN" \
  --output /tmp/inventory-lab-public-acceptance.json
```

The examples above require real reviewed values. Only Caddy publishes 80/443;
Uvicorn has no host port. Caddy certificate/config volumes persist. App filesystem
is read-only and runs as UID/GID 10001 with capabilities dropped and no secrets.
The health check reads and validates the packaged synthetic evidence endpoint.
`depends_on: service_healthy` gates proxy startup; it does not implement continuing
health-driven recovery. Restart policy restarts exited containers, not merely
unhealthy live processes. Rate/concurrency saturation may temporarily fail a
health probe; investigate before claiming evidence corruption.

Resource caps are app 0.5 CPU / 256 MiB / 64 PIDs and proxy 0.25 CPU / 128 MiB /
64 PIDs; swap limits equal memory caps. Actual enforcement requires Linux runtime
acceptance. App/proxy logs rotate at 5 MiB × 2 each; access logging is disabled.
Process admission is global, resets on restart and must remain single-worker.
It is not a distributed limiter, fair per-user allowance, network DoS defense or
a timeout that kills synchronous calculation. No autoscaling is configured.

## Rollback and validation status

Retain the previous validated app image digest. Restore `LAB_IMAGE` to that digest,
run the same `up -d --no-build --wait` command, then verify public baseline and
blocked controls. To stop this demo only:

```sh
docker compose -f deploy/lab/compose.yaml down
```

Do not pass `--volumes` if preserving certificate material. Stop/terminate the
selected host separately to stop hosting cost; no host has been selected here.

Local acceptance: **34 focused tests** (11 new hosted-boundary tests + existing
23 Lab/API tests), an installed wheel served outside the checkout, and **13 live
HTTPS responses through Caddy 2.10.2** with an explicitly trusted localhost
private CA. No trust-store certificate was installed. The local proxy variant
uses loopback binding/upstream, internal TLS and disables automatic redirects.
The original Caddyfile also passes native validation with a loopback HTTP site.
See [receipt](../../docs/review/hosted-lab-acceptance.json).

The retained receipt did not verify Docker/Compose or Linux enforcement. Container
caps/read-only identity, crash recovery, public DNS/ACME TLS, HTTP redirect and
external uptime remain release gaps. Private-CA HTTPS does not establish public
trusted TLS. Accessibility and hosted serving are integrated; the combined installed
wheel's browser check under actual CSP passed Enter-to-run/focus/chart rendering
and 320px blocked reflow ([receipt](../../docs/review/research-integration-browser.json)).
See [remaining engineering checks](../../docs/KB.md#engineering-gaps-and-hypotheses)
and [manual accessibility limits](../../docs/RESULTS.md#browser-and-accessibility-results).

## Serving architecture and limits

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

## Release ownership and cost

The recorded proposed infrastructure ceiling is USD 10/month, excluding an already
owned domain. It is neither a current quote nor spending authorization. Before
provisioning, review provider/region, current tax/egress/storage/log/domain costs,
monthly total and shutdown steps. If the approved envelope cannot be met, retain
the local demo until a different budget is approved. AUTO merge mode does not
approve paid deployment. One shared admission bucket is a portfolio tradeoff;
TLS/bandwidth abuse requires host/provider controls beyond calculation admission.

The subsequent [native engineering pilot](../../docs/RESULTS.md#local-engineering-pilot)
adds short open-arrival HTTP/admission/body recovery and separate small PostgreSQL
fault/restore evidence. It does not verify container/Linux enforcement, hosted
application crash recovery, public release or the confirmation sample/duration floor.

The [October 4 continuation](../../docs/RESULTS.md#engineering-continuation) builds
this maintained pinned image and measures its actual ARM64 Linux Lab controls:
UID10001, read-only filesystem, capability/no-new-privileges restrictions,
0.5 CPU/256 MiB/64 PID enforcement, internal app network and missing/corrupt
archive HTTP503. Its proxy is root as configured and bound only to loopback HTTP,
with an additional bridge for local ingress. Runtime/load/fault receipts are
separate from x86/two-date reference confirmation, public TLS and independent
human release acceptance; the slow-body proxy outcome remains a release gap.
