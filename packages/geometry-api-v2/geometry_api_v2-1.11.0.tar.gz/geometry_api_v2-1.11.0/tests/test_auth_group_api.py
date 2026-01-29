from uuid import uuid4

from shapediver.geometry_api_v2 import (
    AuthGroupApi,
    Configuration,
    ReqAuthorizationGroup,
    SdClient,
)


def test_create(host, jwt_backend, model_id):
    backend_client = SdClient(Configuration(host, access_token=jwt_backend))

    # Create a new authorization group.
    res_auth_group = AuthGroupApi(backend_client).create_authorization_group(
        ReqAuthorizationGroup(
            models=[model_id], users=[str(uuid4())], organizations=[str(uuid4())]
        )
    )
    assert res_auth_group.auth_group is not None
