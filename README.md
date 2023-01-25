# Custom Kubernetes Mutating Webhook Configuration

### Concept

This example deploys a mutating admissions controller in your kubernetes cluster.  The controller looks for pods created by the MongoDB Enterprise Operator.  The controller will enforce a requiredDuringSchedulingIgnoredDuringExecution scheduling rule on each member of a statefulset.  The end result is that a MongoDB shard's replica set members will never coexist on the same worker node.  However, different shard members can share a common worker node.

### Deployment

1. Create the configmap that holds the python script responsible for the webhook logic and responses.

```
kubectl create configmap -n mongodb mongodb-shard-mutator --from-file=mutating_controller.py
```

2. Deploy the server (Flask), service, TLS certificates (cert-manager), and admissions rules/mutators

Adjust the Certificate Authority (base64 encoded) string to your CA bundle (same CA that has signed the TLS certificates mounted in the python applications container)

```
kubectl apply -f deploy/deployment.yaml
```

3. Deploy a MongoDB resource and confirm the requiredDuringSchedulingIgnoredDuringExecution rules are in place

You may consider deploying draining a node and review the pending pod states to check that they are unscheduable.


### Room for Improvement

- Create a custom image with the python application instead of using the base image `python:3` directly and installing pip packages at run time.
- Place a proper web server in front of Flask.
- Test thoroughly, do not use in production

