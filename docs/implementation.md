# Implementation Details

How the files in this repository connect, and what each pipeline step does.

## Build timeline

| Commit | Change |
|---|---|
| `0734fd6` | Flask application, Dockerfile, Helm chart and plain Kubernetes manifest |
| `078e90f` | GitHub Actions workflow with the test job, and Pytest tests |
| `c91a2d0` | Docker build and Docker Hub publishing job |
| `65dd64a` | Deploy job on the self-hosted Windows runner (this run failed at the Helm step) |
| `0e0932f` | Fixed the Helm Service template; the full pipeline passed |

## How the pieces connect

```text
tests/test_app.py ──imports──> app/app.py
app/Dockerfile    ──copies───> app/app.py, app/requirements.txt
ci-cd.yml (docker job) ──builds──> app/Dockerfile ──pushes──> nikhilpreetham/devops-demo:<sha>
ci-cd.yml (deploy job) ──runs──> helm upgrade --install ./helm/devops-demo --set image.tag=<sha>
helm/devops-demo/templates/* ──read──> values.yaml (replicas, image, service, resources)
```

| Value | Defined in | Must match |
|---|---|---|
| Container port `8080` | `app/Dockerfile` (`EXPOSE`, Gunicorn `--bind`) | `containerPort` in `templates/deployment.yaml` (named `http`) |
| Health path `/health` | `app/app.py` | Both probes in `templates/deployment.yaml` |
| Image repository | Docker Hub `nikhilpreetham/devops-demo` | `image.repository` in `values.yaml` and the deploy step |
| Image tag | `${{ github.sha }}` in the docker job | `--set image.tag` in the deploy job |
| Release name `devops-demo` | Deploy step | `deployment/devops-demo` in the rollout check (Deployment and Service are named after the release) |
| Namespace `devops-demo` | Deploy step `--namespace` | Rollout check `-n devops-demo` |

## Pipeline jobs

### `test` (ubuntu-latest)

1. `actions/checkout@v4`
2. `actions/setup-python@v5` with Python 3.13 (same version as the Docker base image `python:3.13-slim`)
3. `pip install -r app/requirements.txt` and `pytest`
4. `python -m pytest tests/ -v`

If tests fail, the `docker` and `deploy` jobs do not run (`needs:`).

### `docker` (ubuntu-latest)

1. `docker/setup-buildx-action@v3`
2. `docker/login-action@v3` with `DOCKERHUB_USERNAME` / `DOCKERHUB_TOKEN`, only on a push to `main`
3. `docker/build-push-action@v6`: builds `./app`; pushes `:latest` and `:<commit-sha>` only on a push to `main`

On pull requests the image is built but not pushed, which checks that the Dockerfile still builds without publishing anything.

### `deploy` (self-hosted Windows runner)

Runs only on a push to `main`, after `docker` succeeds.

1. `kubectl cluster-info`: confirms the runner can reach the Kind cluster
2. `helm version`
3. `helm upgrade --install devops-demo ./helm/devops-demo --namespace devops-demo --set image.repository=nikhilpreetham/devops-demo --set image.tag=<sha> --wait --timeout 5m`
4. `kubectl rollout status deployment/devops-demo -n devops-demo --timeout=180s`

`--wait` makes Helm wait until the Pods are ready before reporting success, so a broken image or failing readiness probe fails the job instead of passing silently.

## Helm chart vs plain manifest

| | `helm/devops-demo` | `k8s/application.yaml` |
|---|---|---|
| Used by the pipeline | Yes | No |
| Namespace | Created by `--create-namespace` or beforehand | Included as a resource |
| Replicas | 3 (`values.yaml`) | 2 |
| Image | `nikhilpreetham/devops-demo:<sha>` | `devops-demo:1.0.0` (built locally and loaded into Kind) |
| Labels | `app.kubernetes.io/name`, `app.kubernetes.io/instance` | `app` |

The plain manifest is kept as a record of the manual stage before Helm.
