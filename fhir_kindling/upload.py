import pathlib
from typing import Union, Tuple
import requests
from fhir.resources import FHIRAbstractModel
from fhir.resources.bundle import Bundle, BundleEntry
from fhir.resources.fhirtypes import DomainResourceType
from fhir.resources.reference import Reference
from pathlib import Path
import json
from requests.auth import AuthBase
from pprint import pprint

from fhir_kindling.auth import generate_auth
from fhir_kindling.serde import validate_bundle, load_bundle
from dotenv import load_dotenv, find_dotenv


def upload_bundle(bundle: Union[Bundle, Path, str],
                  fhir_api_url: str,
                  validate: bool = True,
                  username: str = None,
                  password: str = None,
                  token: str = None,
                  fhir_server_type: str = "hapi",
                  references: bool = False) -> Union[dict, Tuple[dict, list]]:
    """Upload a bundle to a FHIR server.

    Args:
      bundle: Either a bundle object, the path to json file containing a bundle or to a directory containing multiple bundle json files
      fhir_api_url: base url of the FHIR servers api
      validate: flag indicating whether to validate bundles loaded from file
      username: username for basic auth authentication
      password: password for basic auth
      token: token for bearer token authentication
      fhir_server_type: FHIR server implementation defaults to HAPI
      references: indicates whether to return references to the generated resources

    Returns:
      The fhir server's response(s) and references to the uploaded resources if the flag is set.

    """
    auth = generate_auth(username=username, password=password, token=token, load_env=True)

    if isinstance(bundle, str) or isinstance(bundle, Path):

        if pathlib.Path.is_dir(Path(bundle)):
            p = pathlib.Path(bundle).glob("**/*")
            files = [x for x in p if x.is_file()]
            response_dict = {}
            for file in files:
                bundle_file = load_bundle(file)
                bundle_response = _upload_bundle(bundle_file, api_url=fhir_api_url, auth=auth,
                                                 fhir_server_type=fhir_server_type)
                response_dict[str(file)] = bundle_response

            response = response_dict
        else:
            loaded_bundle = load_bundle(bundle)
            response = _upload_bundle(loaded_bundle, api_url=fhir_api_url, auth=auth, fhir_server_type=fhir_server_type)

    else:

        response = _upload_bundle(bundle, api_url=fhir_api_url, auth=auth, fhir_server_type=fhir_server_type)
    if references:
        # TODO fix references for ibm fhir server
        resource_references = _get_references_from_bundle_response(response, fhir_server_type=fhir_server_type)
        return response, resource_references
    else:
        return response


def upload_resource(resource: FHIRAbstractModel,
                    fhir_api_url: str,
                    username: str = None,
                    password: str = None,
                    token: str = None,
                    fhir_server_type: str = "hapi",
                    reference: bool = True):
    """
    Upload a single resource to the server

    Args:
        resource: Resource to uplaod
        fhir_api_url: base url of the fhir rest api to use
        username: username for basic auth
        password: password for basic auth
        token: token to use for bearer auth
        fhir_server_type: type of the fhir server one of [ibm, hapi, blaze]
        reference: whether to return the resource reference separately

    Returns:
        the response to from the server or if reference is set (response, reference)
    """
    auth = generate_auth(username=username, password=password, token=token, load_env=True)
    url = fhir_api_url + f"/{resource.resource_type}"

    r = requests.post(url=url, json=resource.dict(), headers=generate_fhir_headers(fhir_server_type), auth=auth)
    print(r.text)

    if fhir_server_type == "ibm":
        if reference:
            location = r.headers["location"].split("/")
            print(location[-4:-2])
            resource_reference = Reference(
                **{"reference": f"{location[-4]}/{location[-3]}",
                   "type": location[-4]}
            )

            return r.headers, resource_reference
        return r.headers
    else:

        r.raise_for_status()
        response = r.json()
        if reference:
            resource_reference = Reference(
                **{"reference": f"{response['resourceType']}/{response['id']}",
                   "type": response['resourceType']}
            )
            return response, resource_reference

        return response


def _get_references_from_bundle_response(response, fhir_server_type: str = "hapi"):
    references = []

    if fhir_server_type == "ibm":
        print(response)


    else:

        for entry in response["entry"]:
            location = entry["response"]["location"]
            reference = "/".join(location.split("/")[:2])

            references.append(reference)
    return references


def _upload_bundle(bundle: Bundle, api_url: str, auth: AuthBase, fhir_server_type: str):
    headers = generate_fhir_headers(fhir_server_type)
    r = requests.post(api_url, auth=auth, data=bundle.json(), headers=headers)
    if fhir_server_type == "ibm":
        print(r.headers)
        return r.headers

    print(r.text)
    r.raise_for_status()

    return r.json()


def generate_fhir_headers(fhir_server_type: str):
    headers = {}
    if fhir_server_type == "blaze":
        headers["Content-Type"] = "application/fhir+json"

    else:
        headers["Content-Type"] = "application/fhir+json"

    return headers


if __name__ == '__main__':
    load_dotenv(find_dotenv())
    bundle_path = "../examples/polar/bundles/POLAR_Testdaten_UKB.json"
    bundle = load_bundle(bundle_path)
    # print(bundle)
    # hapi upload
    # gecco_path = "../examples/gecco/bundles"
    # response = upload_bundle(bundle=gecco_path, fhir_api_url=os.getenv("FHIR_API_URL"), username=os.getenv("FHIR_USER"),
    #                          password=os.getenv("FHIR_PW"), fhir_server_type=os.getenv("FHIR_SERVER_TYPE"))
    # blaze upload
    # response = upload_bundle(bundle=bundle, fhir_api_url=os.getenv("BLAZE_API_URL"), token=os.getenv("FHIR_TOKEN"),
    #                          fhir_server_type=os.getenv("FHIR_SERVER_TYPE"))
