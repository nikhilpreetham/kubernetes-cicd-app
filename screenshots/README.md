# Screenshots

This folder is for **genuine screenshots captured from this project**. No screenshots have been added yet.

Before adding an image, crop out tokens, secrets, email addresses and personal paths.

| # | Suggested file name | What it should show |
|---|---|---|
| 1 | `01-pipeline-success.png` | A workflow run with test, docker and deploy jobs all green |
| 2 | `02-deploy-job-steps.png` | Deploy job steps on the self-hosted runner, including the Helm upgrade and rollout status |
| 3 | `03-docker-hub-tags.png` | Docker Hub repository showing commit-SHA tags |
| 4 | `04-pods-running.png` | `kubectl get pods -n devops-demo` with 3 Pods running |
| 5 | `05-helm-history.png` | `helm history devops-demo -n devops-demo` showing revisions and a rollback |
| 6 | `06-liveness-failure.png` | Pods restarting during the `/invalid-health` liveness exercise |
| 7 | `07-describe-pod-events.png` | `kubectl describe pod` events showing the failed liveness probe |
| 8 | `08-app-response.png` | Browser or `curl` showing the `/` and `/health` responses through port-forward |

After adding images, link them from the README.
