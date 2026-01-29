from shapediver.geometry_api_v2 import (
    Configuration,
    FileApi,
    ReqFileDefinition,
    ReqFileUpload,
    ResParameterType,
    SdClient,
    SessionApi,
    sd_utils,
)


def test_file_parameter(utils, host, jwt_model):
    model_client = SdClient(Configuration(host, access_token=jwt_model))
    client = SdClient(Configuration(host))

    # Initialize a new session.
    ticket = utils.create_ticket()
    res_session = SessionApi(model_client).create_session_by_ticket(ticket)
    session_id = res_session.session_id
    assert res_session.parameters

    # Search for a file-parameter.
    file_params = [
        param
        for param in res_session.parameters.values()
        if param.type == ResParameterType.FILE
    ]
    assert len(file_params) > 0

    # File upload.
    with open("tests/data/logo.jpg", "rb") as f:
        s = f.read()

        filename = "ShapeDiver_Logo.jpg"
        format = "image/jpeg"

        # Request a file upload for a specific file-parameter.
        res_upload = FileApi(client).upload_file(
            session_id,
            ReqFileUpload(
                additional_properties={
                    file_params[0].id: ReqFileDefinition(
                        filename=filename,
                        format=format,
                        size=len(s),
                    )
                }
            ),
        )
        file = res_upload.asset.file[file_params[0].id]
        assert file

        # Upload the file.
        res_upload = sd_utils.upload_asset(file.href, s, file.headers)
        assert res_upload.status == 200

    # Download the uploaded file.
    res_data = FileApi(model_client).download_file(
        session_id, file_params[0].id, file.id
    )
    assert len(res_data) > 0

    # Get metadata of an existing file.
    res_metadata = FileApi(client).get_file_metadata_with_http_info(
        session_id, file_params[0].id, file.id
    )
    assert res_metadata.status_code == 200
    file_info = sd_utils.extract_file_info(res_metadata.headers)
    assert file_info.filename == filename
    assert file_info.size == len(s)

    # List all files of a specific file-parameter.
    res_list = FileApi(model_client).list_files(session_id, file_params[0].id)
    assert len(res_list.list.file) > 0

    # Delete the uploaded file.
    FileApi(model_client).delete_file(session_id, file_params[0].id, file.id)

    # Close the session.
    SessionApi(client).close_session(session_id)
