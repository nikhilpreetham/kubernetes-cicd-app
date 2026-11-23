# Troubleshooting

Problems met while building and testing the project, and how they were resolved. The run history is in the repository's **Actions** tab.

## 1. Deploy job failed: broken Service template

| | |
|---|---|
| Run | Push of commit `65dd64a` |
| Failed step | **Deploy application using Helm** (test and docker jobs passed) |
| Cause | `helm/devops-demo/templates/service.yaml` contained the contents of a `.gitignore` file instead of a Service manifest, so Helm could not render a valid Kubernetes object |
| Fix | Restored the real Service template in commit `0e0932f`; the next pipeline run passed all three jobs |

**Lesson:** run `helm lint` and `helm template` before pushing chart changes. Both catch a template that does not render to valid YAML.

## 2. Liveness probe failure simulation

**Change:** the liveness probe path was changed from `/health` to `/invalid-health`. The application returns HTTP 404 for that path.

**What happened:**

1. The kubelet's liveness checks failed repeatedly.
2. Kubernetes restarted the containers. All 3 Pods showed 2 restarts during the exercise.
3. Restoring `/health` and reconciling the Deployment with Helm stopped the restarts.

**Commands used to observe it:**

```powershell
kubectl get pods -n devops-demo -w
kubectl describe pod <POD_NAME> -n devops-demo    # Events: "Liveness probe failed: HTTP probe failed with statuscode: 404"
```

**Readiness vs liveness:** if only the readiness path had been wrong, the Pods would have been removed from the Service endpoints and stopped receiving traffic, but they would not have been restarted.

## 3. Helm field ownership conflict

**Cause:** during the exercise the Deployment was changed directly with `kubectl patch`. Kubernetes records which tool manages each field, so the patched fields became owned by `kubectl-patch` instead of Helm. When Helm then tried to set those fields back, the upgrade failed with a conflict.

**Fix:** the upgrade was re-run with `--force-conflicts`, which tells Helm (using server-side apply, available in Helm 4) to take ownership of the conflicting fields:

```powershell
helm upgrade --install devops-demo ./helm/devops-demo `
  --namespace devops-demo `
  --set image.repository=nikhilpreetham/devops-demo `
  --set image.tag=<IMAGE_TAG> `
  --force-conflicts `
  --wait `
  --timeout 5m
```

**Lesson:** when Helm manages a resource, change it through the chart and `helm upgrade`, not with `kubectl patch` or `kubectl edit`.

**Verified after recovery:** 3/3 replicas available, 3 Pods running, 0 restarts, both probes on `/health`, Helm release revision 8, status `deployed`.

## 4. Rollback

```powershell
helm history devops-demo -n devops-demo
helm rollback devops-demo <REVISION> -n devops-demo --wait
kubectl rollout status deployment/devops-demo -n devops-demo
```

A rollback creates a new Helm revision with the old configuration; it does not delete history.

## Common issues

| Symptom | Likely cause | Check |
|---|---|---|
| Deploy job stays queued | Self-hosted runner offline (this happened after the cluster and runner were removed, and led to making deploy manual-only) | `Settings > Actions > Runners`; start the runner (`run.cmd` or its service), or cancel the run |
| `kubectl cluster-info` fails in the deploy job | Kind cluster stopped, or the runner's kubeconfig points to another context | `kind get clusters`; `kubectl config current-context` should be `kind-devops-lab` |
| Pods in `ImagePullBackOff` | Tag not in Docker Hub, or wrong repository | `kubectl describe pod`; check the tag exists at `hub.docker.com/r/nikhilpreetham/devops-demo/tags` |
| Pods in `CrashLoopBackOff` | Application error or failing liveness probe | `kubectl logs <POD_NAME> -n devops-demo --previous` |
| Helm `--wait` times out | Pods never become ready | `kubectl get pods`, `kubectl describe pod`, readiness probe events |
| Docker login fails | Secret missing or token revoked | Repository secrets `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN` |
| `another operation is in progress` from Helm | A previous Helm command was interrupted | `helm history`; roll back to the last `deployed` revision |
