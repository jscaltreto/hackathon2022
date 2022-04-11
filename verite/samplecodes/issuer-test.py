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

credential_offer_endpoint =  "/api/v1/issuance/manifest/kyc/test-string"

conn = http.client.HTTPSConnection("issuer-sandbox.circle.com")
conn.request("GET", credential_offer_endpoint)
res = conn.getresponse()
if res.status != 200:
  print("Failed to get CredentialOffer", res.status, res.reason)
  sys.exit(1)

data = res.read().decode('utf-8')
credential_offer = json.loads(data)
print("\n\n============= credential_offer ==========");
print(json.dumps(credential_offer, indent=2))

challenge = credential_offer["body"]["challenge"]
credential_application_id = credential_offer["id"]
reply_url = credential_offer['reply_url']

# note: "holder" is the wallet's did
credential_application = json.loads("""
{
  "sub": "did:key:zQ3shv378PvkMuRrYMGFV9a3MtKpJkteqb2dUbQMEMvtWc2tE",
  "iss": "did:key:zQ3shv378PvkMuRrYMGFV9a3MtKpJkteqb2dUbQMEMvtWc2tE",
  "credential_application": {
    "id": "2ce196be-fcda-4054-9eeb-8e4c5ef771e5",
    "manifest_id": "KYCAMLAttestation",
    "format": {
      "jwt_vp": {
        "alg": ["ES256K"]
      }
    }
  },
  "presentation_submission": {
    "id": "b4f43310-1d6b-425d-84c6-f8afac3fe244",
    "definition_id": "ProofOfControlPresentationDefinition",
    "descriptor_map": [
      {
        "id": "proofOfIdentifierControlVP",
        "format": "jwt_vp",
        "path": "$.presentation"
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
    ],
    "holder": "did:web:circle.com",
    "verifiableCredential": [
      "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9....7wwi-YRX"
    ]
  }
}
""")

credential_application['credential_application']['id'] = credential_application_id
jwt_string = jwt.encode(credential_application, challenge, algorithm="HS256")
credential_application['vp']['verifiableCredential'] = [jwt_string]

print("\n\n============= jwt_string in credential_application ==========");
print(jwt_string)
print("\n\n============= credential_application ==========");
print(json.dumps(credential_application, indent=2))

headers = {'Content-type': 'text/plain'}
conn.request('POST', reply_url, jwt_string, headers)
res = conn.getresponse()
if res.status != 200:
  print("Failed to get CredentialOffer", res.status, res.reason)
  sys.exit(1)

jwt_string = res.read().decode('utf-8')
print("\n\n============= response in jwt ==========");
print(jwt_string)

public_key_file = './issuer-public-key.pem'
with open(public_key_file) as f:
    public_key = f.read()
decoded_payload = jwt.decode(jwt_string, public_key, algorithms=["ES256K"])
print("\n\n============= decoded jwt_string ==========");
print(json.dumps(decoded_payload, indent=2))

vc_jwt_string = decoded_payload['vp']['verifiableCredential'][0]
print("\n\n============= vc_jwt_string ==========");
print(vc_jwt_string)
decoded_vc_jwt_string = jwt.decode(vc_jwt_string, public_key, algorithms=["ES256K"])
print("\n\n============= decoded vc_jwt_string ==========");
print(json.dumps(decoded_vc_jwt_string, indent=2))


conn.close()
