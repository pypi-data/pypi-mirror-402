from shapediver.geometry_api_v2 import (
    ArSceneApi,
    Configuration,
    GltfApi,
    ModelStateApi,
    QueryGltfConversion,
    ReqCustomization,
    ReqModelState,
    SdClient,
    SessionApi,
)


def test_metadata_and_downloads(utils, host):
    client = SdClient(Configuration(host))

    # Initialize a new session.
    ticket = utils.create_ticket()
    session_id = SessionApi(client).create_session_by_ticket(ticket).session_id

    with open("tests/data/Box.glb", "rb") as f:
        s = f.read()

        # Create AR scene from glTF file.
        res_upload = GltfApi(client).upload_gltf(
            session_id, s, QueryGltfConversion.SCENE
        )
        assert res_upload.gltf.scene_id is not None

        scene_id = res_upload.gltf.scene_id

    # Get metadata of an existing AR scene.
    res_metadata = ArSceneApi(client).get_ar_scene_metadata_with_http_info(scene_id)
    assert res_metadata.status_code == 200

    # Download the created AR scene as glTF.
    res_gltf = ArSceneApi(client).download_ar_scene_gltf(scene_id)
    assert len(res_gltf) > 0

    # Download the created AR scene as USDZ.
    res_usdz = ArSceneApi(client).download_ar_scene_usdz(scene_id)
    assert len(res_usdz) > 0

    # Close the session.
    SessionApi(client).close_session(session_id)


def test_model_state_from_ar_scene(utils, host, jwt_backend):
    backend_client = SdClient(Configuration(host, access_token=jwt_backend))
    client = SdClient(Configuration(host))

    # Initialize a new session.
    ticket = utils.create_ticket()
    res_session = SessionApi(client).create_session_by_ticket(ticket)
    session_id = res_session.session_id

    with open("tests/data/Box.glb", "rb") as f:
        s = f.read()

        # Create AR scene from glTF file.
        res_upload = GltfApi(client).upload_gltf(
            session_id, s, QueryGltfConversion.SCENE
        )
        assert res_upload.gltf.scene_id is not None

    # Create minimal Model-State from AR scene.
    req_model_state = ReqModelState(
        parameters=ReqCustomization(),
        arSceneId=res_upload.gltf.scene_id,
    )
    res_model_state = ModelStateApi(client).create_model_state(
        session_id, req_model_state
    )
    model_state_id = res_model_state.model_state.id

    # Get metadata of the Model-State's AR scene.
    res_metadata = ArSceneApi(client).get_ar_scene_metadata_with_http_info(
        model_state_id
    )
    assert res_metadata.status_code == 200

    # Download the created Model-State's AR scene as glTF.
    res_gltf = ArSceneApi(client).download_ar_scene_gltf(model_state_id)
    assert len(res_gltf) > 0

    # Download the created Model-State's AR scene as USDZ.
    res_usdz = ArSceneApi(client).download_ar_scene_usdz(model_state_id)
    assert len(res_usdz) > 0

    # Delete the Model-State.
    ModelStateApi(backend_client).delete_model_state(model_state_id)

    # Close the session.
    SessionApi(client).close_session(session_id)
