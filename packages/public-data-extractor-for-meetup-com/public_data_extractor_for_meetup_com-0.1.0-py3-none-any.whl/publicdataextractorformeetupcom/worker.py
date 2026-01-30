import json
import os
import time

import jwt
import requests
from cryptography.hazmat.primitives import serialization


class Worker:

    def __init__(
        self,
        meetup_com_authorized_member_id,
        meetup_com_your_client_key,
        meetup_com_private_signing_key,
    ):
        self._meetup_com_authorized_member_id = meetup_com_authorized_member_id
        self._meetup_com_your_client_key = meetup_com_your_client_key
        self._meetup_com_private_signing_key = meetup_com_private_signing_key
        self._meetup_com_access_token = None

    def _get_meetup_com_access_token(self):
        if self._meetup_com_access_token:
            # TODO we assume it's still valid - it may not be. We could check here.
            return

        # Make JWT
        private_key = serialization.load_pem_private_key(
            self._meetup_com_private_signing_key.encode(), password=None
        )
        payload = {
            "sub": self._meetup_com_authorized_member_id,
            "iss": self._meetup_com_your_client_key,
            "aud": "api.meetup.com",
            "exp": int(time.time()) + 600,  # Expires in 10 minutes
        }
        signed_jwt = jwt.encode(payload, private_key, algorithm="RS256")

        # Get Access Token
        url = "https://secure.meetup.com/oauth2/access"
        headers = {
            "Content-Type": "application/json",
        }
        data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": signed_jwt,
        }
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        self._meetup_com_access_token = response.json().get("access_token")

    def _make_meetup_com_graphql_query(self, query, variables):
        graphql_url = "https://api.meetup.com/gql-ext"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(self._meetup_com_access_token),
        }
        response = requests.post(
            graphql_url, json={"query": query, "variables": variables}, headers=headers
        )
        response.raise_for_status()
        return response.json()

    def extract_group(self, group_url_name, out_directory):
        self._get_meetup_com_access_token()

        data = self._make_meetup_com_graphql_query(
            """
            query GetUpcomingEvents($groupURLName: String!) {
                groupByUrlname(urlname: $groupURLName) {
                    id
                    urlname
                    name
                    description
                    events {
                        edges {
                            node {
                                id
                                title
                                description
                                eventUrl
                                dateTime
                                duration
                                eventType
                                status
                                venues {
                                    name
                                    address
                                    postalCode
                                    country
                                    lat
                                    lon
                                }
                            }
                        }
                    }
                }
            }
            """,
            {"groupURLName": group_url_name},
        )

        if not os.path.exists(out_directory):
            os.makedirs(out_directory)

        with open(os.path.join(out_directory, "out.json"), "w") as fp:
            json.dump(data, fp, indent=4)
