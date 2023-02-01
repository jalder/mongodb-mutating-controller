import base64
import jsonpatch
from flask import Flask, request, jsonify

mutate_server = Flask(__name__)

@mutate_server.route('/mutate/sts-bond-distribution', methods=['POST','GET'])
def mutator():
  print(request)
  if request.method == "POST":
    resource = request.get_json()
    requestId = resource["request"]["uid"]
    ignore = jsonify({"apiVersion": "admission.k8s.io/v1","kind": "AdmissionReview","response":{"uid": requestId, "allowed": True, "status": {"message":"Resource is not managed by MongoDB Enterperise Operator, ignoring."}}})

    ## Check if Pod label has "controller: mongodb-enterprise-operator"
    if "request" in resource:
      if "object" in resource["request"]:
        if "metadata" in resource["request"]["object"]:
          if "labels" in resource["request"]["object"]["metadata"]:
            if "sts-bond-with-prefix" in resource["request"]["object"]["metadata"]["labels"]:
              if resource["request"]["object"]["metadata"]["labels"]["sts-bond-with-prefix"] != "":
                ## If so, set pod affinity for preferredDuringSchedulingIgnoreDuringExecution to value "sts-bond-with: {prefix}-#
                ## And add new label for association
                prefix = resource["request"]["object"]["metadata"]["labels"]["sts-bond-with-prefix"]
                ordinal = resource["request"]["object"]["metadata"]["name"].split("-")[-1]
                message = "Adding pod label and affinity for "+prefix+"-"+ordinal
                label = {"op": "add", "path": "/metadata/labels/sts-bond-with", "value": prefix+"-"+ordinal }
                affinity = {"op": "add", "path": "/spec/affinity/podAffinity", "value": 
                    {"preferredDuringSchedulingIgnoredDuringExecution":[
                      {"weight": 100, "podAffinityTerm":{"labelSelector":{"matchExpressions":[
                        {"key":"sts-bond-with","operator":"In","values":[prefix+"-"+ordinal]}
                        ]}
                        ,"topologyKey":"kubernetes.io/hostname"} }
                      ]}
                    }
                patch = jsonpatch.JsonPatch([label,affinity])
                encoded_patch = base64.b64encode(patch.to_string().encode("utf-8")).decode("utf-8")
                response = jsonify({"apiVersion": "admission.k8s.io/v1","kind": "AdmissionReview","response":{"uid": requestId,"allowed": True, "status": {"message":message},"patchType":"JSONPatch","patch": encoded_patch}})
                return response
    return ignore
  else:
    ## No request received
    return jsonify({"response":{"allowed": True, "status": {"message":"No request received by mutating webhook."}}})

@mutate_server.route('/', methods=['GET'])
def index():
  return "This service modifies Pods to associate Pods from different StatefulSets with one another and set affinity for colocation."

mutate_server.run(host='0.0.0.0', port=8443, ssl_context=('/security/tls.crt','/security/tls.key'))
