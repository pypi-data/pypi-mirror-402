from shapediver.geometry_api_v2 import (
    Configuration,
    GltfApi,
    QueryGltfConversion,
    SdClient,
    SessionApi,
    sd_utils,
)


def test_upload_gltf(utils, host):
    client = SdClient(Configuration(host))

    # Initialize a new session.
    ticket = utils.create_ticket()
    session_id = SessionApi(client).create_session_by_ticket(ticket).session_id

    with open("tests/data/Box.glb", "rb") as f:
        s = f.read()

        # Upload a new glTF.
        res_upload = GltfApi(client).upload_gltf(session_id, s)
        assert res_upload.gltf.href is not None

        # Download the uploaded glTF.
        res_gltf = sd_utils.download(res_upload.gltf.href).read()
        assert len(res_gltf) == len(s)

    # Close the session.
    SessionApi(client).close_session(session_id)


def test_upload_gltf_and_convert_to_usdz(utils, host):
    client = SdClient(Configuration(host))

    # Initialize a new session.
    ticket = utils.create_ticket()
    session = SessionApi(client).create_session_by_ticket(ticket).session_id

    with open("tests/data/Box.glb", "rb") as f:
        s = f.read()

        # Upload a new glTF and convert to USDZ.
        res_upload = GltfApi(client).upload_gltf(session, s, QueryGltfConversion.USDZ)
        assert res_upload.gltf.href is not None

        # Download the created USDZ.
        res_usdz = sd_utils.download(res_upload.gltf.href).read()
        assert len(res_usdz) != len(s)

    # Close the session.
    SessionApi(client).close_session(session)
