# Render Free synthetic demo

The root [Blueprint](../../render.yaml) deploys BOSS as one Free Python web service
in Oregon. The existing bounded `lab_hosted:app` serves the committed React build,
original Lab, saved evidence, scenario/feasibility comparisons, execution history,
feedback example and Evaluation. No database, disk, worker, secret, model call or
public write endpoint is configured. Local journal actions stay disabled; the
allowed POST routes calculate transient comparisons only. Browser-local saved views
and exports remain available.

## Deploy from GitHub

1. Open the [Render Dashboard](https://dashboard.render.com), then **New → Blueprint**.
2. Select **GitHub / Connect GitHub**. In GitHub's authorization/install screen,
   select **Only select repositories → daniel-li2021/inventory-intelligence**, then
   **Install / Authorize**. Return to Render and click **Connect** beside that repo.
   Use the connected GitHub repository, rather than the public-URL option, so
   automatic deployment works.
3. Name the Blueprint `inventory-intelligence-boss`, choose branch **main**, and
   leave **Blueprint Path** as `render.yaml`. Leave Root Directory empty if shown.
4. Review the proposed resources: exactly **one Web Service**, **Free** instance,
   **Oregon**, Python **3.12.14**, health path **/health/ready**. No environment
   secrets or additional resources are needed. Click **Deploy Blueprint**.
5. Open the created service and wait for **Live**, then open its `https://…onrender.com`
   URL. Check **Settings → Build & Deploy → Auto-Deploy → After CI Checks Pass**
   (the Blueprint sets this already). Send the public URL for actual acceptance.

Ordinary `main` commits deploy only after all detected GitHub checks pass. Existing
CI rebuilds the locked React frontend and rejects asset drift, runs the same build
script, tests hosted boundaries and the browser journey, and checks PostgreSQL
correctness separately. No CI deployment secret or deploy hook is needed. Render
does not auto-deploy when no checks are detected or any check fails. Initial manual
deployment and Blueprint configuration sync are separate from that commit gate;
review green CI before the initial deployment or a manual configuration sync.
[Render CI behavior](https://render.com/docs/deploys#integrating-with-ci),
[Blueprint setup](https://render.com/docs/infrastructure-as-code#setup).

## Build and serving boundary

`bash deploy/render/build.sh` pins build tooling and all existing runtime
dependencies, builds a clean wheel, verifies exact current assets/evidence, installs
it and runs the installed-package offline acceptance. No Node build is needed on
Render: CI checks the committed React assets against their locked sources. The
runtime imports the installed wheel, with no source checkout added to PYTHONPATH.

The Blueprint binds Uvicorn to `0.0.0.0:$PORT` with one worker, concurrency16,
backlog32 and five-second keep-alive. One worker preserves the global API admission
limits (2/s, burst20, four active requests, 4KiB bodies, five-second body deadline).
Render terminates public TLS; no Caddy, Docker or custom domain is required.
The [existing security envelope](../lab/README.md#local-http-entry-point) provides
CSP, no-store API responses, exact asset/path allowlists and disabled API docs.
`/health/ready` validates product/execution archives without spending API allowance;
`/health/live` tests liveness. This native deployment does not inherit Compose's
read-only filesystem, UID or cgroup controls.

From a disposable Python 3.12.14 environment at the repo root:

```sh
bash deploy/render/build.sh
PORT=10000 sh -c 'python -m uvicorn inventory_intelligence.lab_hosted:app --host 0.0.0.0 --port "$PORT" --workers 1 --limit-concurrency 16 --backlog 32 --timeout-keep-alive 5 --no-access-log --no-proxy-headers'
```

In another terminal with the same environment:

```sh
python -m scripts.check_hosted_lab --base-url http://127.0.0.1:10000
python scripts/check_product_browser.py --base-url http://127.0.0.1:10000
```

For public acceptance, substitute the actual HTTPS URL. Allow the initial cold
start to finish before running checks. Verify trusted TLS, readiness, current
assets, all eight screens and major APIs, blocked calculations, disabled writes,
security headers and deploy logs. Never point a local journal-enabled app at Render.

## Free limits, rollback and status

Free instances sleep after 15 minutes idle; a new request can take about one minute
to wake them. The workspace shares 750 Free instance hours per month. Bandwidth and
build minutes have separate quotas; overages can incur charges when a payment
method is present. To keep the demo within free usage, use the Hobby workspace,
do not upgrade resources, and keep the workspace spend limit at $0 where available;
without a payment method, quota exhaustion suspends services/builds instead.
No keep-alive automation is configured. [Current Free limits](https://render.com/docs/free).

For rollback use the service's **Events/Deploys → previous successful deploy →
Rollback** (Free retains only the two most recent previous deploys). A failed build
does not replace the previous live version. To retire the demo, delete the Blueprint first, then delete its service: removing
a Blueprint alone does not delete its resources. [Resource deletion](https://render.com/docs/infrastructure-as-code#deleting-resources).

[Local validation receipt](../../docs/review/render-free-v1.json) records repository
readiness only. Actual Render build/runtime, public TLS, cold starts and serving
capacity remain unverified until the public URL is supplied. No production SLA,
independent human acceptance or real operational readiness follows.
