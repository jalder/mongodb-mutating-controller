# Custom Kubernetes Mutating Webhook Configuration

## STS Pod AntiAffinity Required

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

You may consider draining a node and review the pending pod states to check that they are unscheduable.

Example sharded cluster manifest:
```
---
apiVersion: mongodb.com/v1
kind: MongoDB
metadata:
  name: affinity
  namespace: mongodb
spec:
  configServerCount: 3
  credentials: my-credentials
  mongodsPerShardCount: 3
  mongosCount: 2
  opsManager:
    configMapRef:
      name: my-project
  persistent: false
  shardCount: 3
  type: ShardedCluster
  version: 4.4.11-ent
```


## STS Pod Bonding

### Concept

This second example also deploys a mutating admissions controller in your kubernetes cluster.  The controller looks for pods with label `sts-bond` and `sts-bond-with-prefix`.  The controller will create a preferredDuringSchedulingIgnoredDuringExecution scheduling rule on each member of a statefulset to align their ordered number suffix on the same worker nodes.

|Worker|STS-A|STS-B|STS-C|
|-|-|-|-|
|Node-X|STS-A-0|STS-B-0|STS-C-0|
|Node-Y|STS-A-1|STS-B-1|STS-C-1|
|Node-Z|STS-A-2|STS-B-2|STS-C-2|

### Deployment
1. Create the configmap that holds the python script responsible for the webhook logic and responses.

```
kubectl create configmap -n mongodb sts-bond-mutator --from-file=mutating_controller_sts_bonding.py
```

2. Deploy the server (Flask), service, TLS certificates (cert-manager), and admissions rules/mutators

Adjust the Certificate Authority (base64 encoded) string to your CA bundle (same CA that has signed the TLS certificates mounted in the python applications container)

```
kubectl apply -f deploy/deployment_sts_bonding.yaml
```

Example sharded cluster manifest with required labels:
```
---
apiVersion: mongodb.com/v1
kind: MongoDB
metadata:
  name: affinity
  namespace: mongodb
spec:
  configServerCount: 3
  credentials: my-credentials
  mongodsPerShardCount: 3
  mongosCount: 2
  opsManager:
    configMapRef:
      name: my-project
  persistent: false
  shardCount: 3
  type: ShardedCluster
  version: 4.4.11-ent
  shardPodSpec:
    podTemplate:
      metadata:
        labels:
          sts-bond: "true"
          sts-bond-with-prefix: shardzone
```

### Room for Improvement

- Create a custom image with the python application instead of using the base image `python:3` directly and installing pip packages at run time.
- Place a proper web server in front of Flask.
- Test thoroughly, do not use in production

