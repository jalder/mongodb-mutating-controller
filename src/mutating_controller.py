import base64
import jsonpatch
from flask import Flask, request, jsonify

mutate_server = Flask(__name__)

@mutate_server.route('/mutate/shard-distribution', methods=['POST','GET'])
def mutator():
  print(request)
  if request.method == "POST":
    resource = request.get_json()
    ignore = jsonify({"response":{"allowed": True, "status": {"message":"Resource is not managed by MongoDB Enterperise Operator, ignoring."}}})
    ## Check if Pod label has "controller: mongodb-enterprise-operator"
    if "request" in resource:
      if "object" in resource["request"]:
        if "metadata" in resource["request"]["object"]:
          if "labels" in resource["request"]["object"]["metadata"]:
            if "controller" in resource["request"]["object"]["metadata"]["labels"]:
              if resource["request"]["object"]["metadata"]["labels"]["controller"] == "mongodb-enterprise-operator":
                ## If so, set pod antiAffinity for requiredDuringSchedulingIgnoreDuringExecution to value "pod-anti-affinity: affinity-0"
                if "pod-anti-affinity" in resource["request"]["object"]["metadata"]["labels"]:
                  antiAffinityRule = resource["request"]["object"]["metadata"]["labels"]["pod-anti-affinity"]
                  message = "Adjusted anti-affinity pod rules for "+antiAffinityRule
                  requestId = resource["request"]["uid"]
                  patch = jsonpatch.JsonPatch([{"op": "add", "path": "/spec/affinity/podAntiAffinity/requiredDuringSchedulingIgnoredDuringExecution", "value": [{"labelSelector":{"matchExpressions":[{"key":"pod-anti-affinity","operator":"In","values":[antiAffinityRule]}]},"topologyKey":"kubernetes.io/hostname"}] }])
                  encoded_patch = base64.b64encode(patch.to_string().encode("utf-8")).decode("utf-8")
                  response = jsonify({"apiVersion": "admission.k8s.io/v1","kind": "AdmissionReview","response":{"uid": requestId,"allowed": True, "status": {"message":message},"patchType":"JSONPatch","patch": encoded_patch}})
                  return response
    return ignore
  else:
    ## No request received
    return jsonify({"response":{"allowed": True, "status": {"message":"No request received by mutating webhook."}}})

@mutate_server.route('/', methods=['GET'])
def index():
  return 'This service modifies MongoDB Shard Pods to require that shard replica set members do not get scheduled to the same worker nodes.'

mutate_server.run(host='0.0.0.0', port=8443, ssl_context=('/security/tls.crt','/security/tls.key'))
