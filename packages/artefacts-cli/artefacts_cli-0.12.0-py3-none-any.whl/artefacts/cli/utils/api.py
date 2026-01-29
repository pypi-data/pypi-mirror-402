import os

import requests


def get_artefacts_api_url(project_profile):
    return os.environ.get(
        "ARTEFACTS_API_URL",
        project_profile.get(
            "ApiUrl",
            "https://app.artefacts.com/api",
        ),
    )


def endpoint_exists(url: str) -> tuple:
    """
    Simplistic confirmation of the existance of an endpoint.

    Under discussion: Use of HEAD verbs, etc.
    """
    try:
        access_test = requests.get(url)
        exists = access_test.status_code < 400
        error_code = None
        if not exists:
            error_code = access_test.status_code
    except Exception:
        exists = False
        error_code = 500
    return exists, error_code
