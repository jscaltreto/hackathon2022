# Copyright (c) 2022 Circle Internet Financial Trading Company Limited.
# All rights reserved.
#
# Circle Internet Financial Trading Company Limited CONFIDENTIAL
# This file includes unpublished proprietary source code of Circle Internet
# Financial Trading Company Limited, Inc. The copyright notice above does not
# evidence any actual or intended publication of such source code. Disclosure
# of this source code or any related proprietary information is strictly
# prohibited without the express written permission of Circle Internet Financial
# Trading Company Limited.

# need to install PyJwt: pip install pyjwt

import http.client
import json
import jwt
import ssl
import sys

with open('params.json') as reader:
    params_data = reader.read()
params = json.loads(params_data)
did = params['did']
vc_jwt = params['vc_jwt']
host_port = params['host_port']

verification_endpoint =  "/verifications"

# host_port = "ded3-131-226-33-187.ngrok.io"
host_port = "verifier-sandbox.circle.com"
# conn = http.client.HTTPConnection(host_port)
conn = http.client.HTTPSConnection(host_port)

data = json.loads("""
{
   "network": "ethereum",
   "subject": "0xf39fd6e51aad88f6f4ce6ab8827279cfffb92266",
   "chainId": 1337
}
""")
headers = {'Content-type': 'application/json'}
print("======================= Step 0 ====================")
conn.request("POST", verification_endpoint, json.dumps(data), headers)
res = conn.getresponse()
if res.status >= 300:
  print("Failed to get CredentialOffer", res.status, res.reason)
  sys.exit(1)
res_data = res.read().decode('utf-8')
credential_application = json.loads(res_data)
challenge_url = credential_application['challengeTokenUrl']
print("challeng_url: " + challenge_url)


print("======================= Step 1 ====================")
conn.request("GET", challenge_url)
res = conn.getresponse()
if res.status >= 300:
  print("Failed to get Credential verification", res.status, res.reason)
  sys.exit(1)
res_data = res.read().decode('utf-8')
verification_offer = json.loads(res_data)
print(json.dumps(verification_offer, indent=2))

data = json.loads("""
{
  "credential_fulfillment": {
    "descriptor_map": [
      {
        "format": "jwt_vc",
        "id": "proofOfIdentifierControlVP",
        "path": "$.presentation.credential[0]"
      }
    ],
    "id": "e921d5b2-5293-4297-a467-907f9d565e4e",
    "manifest_id": "KYCAMLAttestation"
  },
  "presentation_submission": {
      "id": "b68fda51-21aa-4cdf-84b7-d452b1c9c3cc",
      "descriptor_map": [
          {
              "format": "jwt_vc",
              "id": "kycaml_input",
              "path": "$.verifiableCredential[0]"
          }
      ]
  },
  "vp": {
    "@context": [
      "https://www.w3.org/2018/credentials/v1"
    ],
    "type": [
      "VerifiablePresentation",
      "CredentialFulfillment"
    ]
  }
}
""")

# set correct fields
data['nonce'] = verification_offer['body']['challenge']
data['presentation_submission']['definition_id'] = verification_offer['body']['presentation_definition']['id']
data['sub'] = did
data['iss'] = did
data['vp']['verifiableCredential'] = [vc_jwt]
data['vp']['holder'] = did

print("==================== vp ====================")
print(json.dumps(data, indent=2))

with open('private-key.pkcs1.pem') as reader:
    private_key = reader.read()

headers = {'Content-type': 'text/plain'}
jwt_string = jwt.encode(data, private_key, algorithm="ES256K")
print("======================= jwt_string ================")
print(jwt_string)

print("======================= Step 2 ====================")
conn.request("POST", verification_offer['reply_url'], jwt_string, headers)
res = conn.getresponse()
if res.status >= 300:
  print("Failed to do verification", res.status, res.reason)
  sys.exit(1)

res_data = res.read().decode('utf-8')
verification_confirmation = json.loads(res_data)
print(json.dumps(verification_confirmation, indent=2))
