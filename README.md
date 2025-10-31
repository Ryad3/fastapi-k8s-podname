# fastapi-k8s-podname

Small FastAPI example showing how Kubernetes replicas can return their pod name so you can observe load-balancing across replicas.

The app exposes a single endpoint that returns the pod name injected into the container via the Kubernetes Downward API. Deploy multiple replicas and repeatedly call the endpoint to see the response switch between different pod names.

## What this repository contains

- `app/main.py` - tiny FastAPI app. Endpoint: `GET /get-podname` returns `{ "pod_name": "<name>" }` where `POD_NAME` is read from the environment.
- `Dockerfile` - builds the container image for the app.
- `kube_manifests/deployment.yml` - Deployment (replicas, downward API env var POD_NAME).
- `kube_manifests/service.yml` - ClusterIP Service to expose the pods inside the cluster.

## Contract

- Input: HTTP GET to `/get-podname`.
- Output: JSON object { "pod_name": string }.
- Error modes: If `POD_NAME` is not set, the app returns `{"pod_name": "Pod name not set"}`.

## Prerequisites

- Docker (for building the image)
- A Kubernetes cluster (minikube, kind, or a remote cluster) and `kubectl` configured to use it
- (Optional) `kind` or `minikube` if you want to run locally without pushing to a remote registry the docker image

## Build the Docker image

From the repository root:

```bash
# tag the image
docker build -t fastapi-k8s-podname:1.0 .
```

Notes:
- The `kube_manifests/deployment.yml` uses `imagePullPolicy: Never` for local testing convenience. That means Kubernetes will try to use the image available in the cluster's node Docker daemon. If you use `kind` or `minikube`, load the image into the cluster as shown below.

## Deploy to Kubernetes (local cluster)

If you're using `kind` (recommended for local testing):

```bash
# build image locally
docker build -t fastapi-k8s-podname:1.0 .
# load the image into the kind cluster
kind load docker-image fastapi-k8s-podname:1.0
# apply manifests
kubectl apply -f kube_manifests/deployment.yml
kubectl apply -f kube_manifests/service.yml
```

If you're using `minikube`:

```bash
minikube image load fastapi-k8s-podname:1.0
kubectl apply -f kube_manifests/deployment.yml
kubectl apply -f kube_manifests/service.yml
```

If you're deploying to a remote cluster, tag and push the image to a registry, then edit `kube_manifests/deployment.yml` to use that registry image and set `imagePullPolicy: IfNotPresent` or remove the `Never` policy.

## What the manifest does

- `kube_manifests/deployment.yml` creates a Deployment with `replicas: 3` and sets an environment variable `POD_NAME` from the pod metadata name using the Downward API:

```yaml
env:
	- name: POD_NAME
		valueFrom:
			fieldRef:
				fieldPath: metadata.name
```

- `kube_manifests/service.yml` exposes the pods as a ClusterIP service on port 80 -> containerPort 8000.

## Test and observe replicas

Port-forward the service to your machine and then call the endpoint repeatedly to see the pod name change as requests are routed to different replicas:

```bash
# forward service port 80 to local 8080
kubectl port-forward svc/fastapi-k8s-podname-service 8080:80

# in another terminal, run repeated requests
for i in {1..10}; do curl -s http://localhost:8080/get-podname; echo; sleep 0.2; done
```

You should see responses like:

```json
{"pod_name":"fastapi-k8s-podname-deployment-6d4b8f7c9-abcde"}
{"pod_name":"fastapi-k8s-podname-deployment-6d4b8f7c9-fghij"}
{"pod_name":"fastapi-k8s-podname-deployment-6d4b8f7c9-klmno"}
```

This demonstrates Kubernetes load-balancing across the replicas.

## Notes & troubleshooting

- If you see `ImagePullBackOff` on your cluster, either push the image to a registry or load the image into your local cluster (see `kind load docker-image` / `minikube image load`).
- If `POD_NAME` is not set, the app will return the default string. The manifest included already wires `POD_NAME` via the Downward API.

## License

MIT
