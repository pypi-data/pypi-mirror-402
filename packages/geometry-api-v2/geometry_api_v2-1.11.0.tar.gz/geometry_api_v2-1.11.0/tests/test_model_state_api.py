from shapediver.geometry_api_v2 import (
    Configuration,
    ModelStateApi,
    ReqCustomization,
    ReqFileDefinition,
    ReqModelState,
    ResBasicParameter,
    ResParameterType,
    SdClient,
    SessionApi,
    sd_utils,
)
from shapediver.geometry_api_v2.client.exceptions import NotFoundException


def test_basic_model_state(utils, host, jwt_backend):
    backend_client = SdClient(Configuration(host, access_token=jwt_backend))
    client = SdClient(Configuration(host))

    # Initialize a new session.
    ticket = utils.create_ticket()
    res_session = SessionApi(client).create_session_by_ticket(ticket)
    assert res_session.parameters
    session_id = res_session.session_id

    # The value of the first string parameter will be overwritten by the Model-State.
    str_params = [
        param
        for param in res_session.parameters.values()
        if param.type == ResParameterType.STRING
    ]
    assert len(str_params) > 0

    custom_param_id = str_params[0].id
    custom_param_value = utils.now()
    custom_data = {"foo": "bar"}

    # Create a new Model-State.
    req_model_state = ReqModelState(
        parameters=ReqCustomization(
            additional_properties={custom_param_id: custom_param_value}
        ),
        data=custom_data,
    )
    res_model_state = ModelStateApi(client).create_model_state(
        session_id, req_model_state
    )
    model_state_id = res_model_state.model_state.id

    # Check if the Model-State was created successfully.
    res_metadata = ModelStateApi(client).get_model_state_metadata_with_http_info(
        model_state_id
    )
    assert res_metadata.status_code == 200

    # Fetch all available information of the Model-State.
    res_model_state_info = ModelStateApi(client).get_model_state(model_state_id)
    parameter = res_model_state_info.model_state.parameters[
        custom_param_id
    ].actual_instance
    assert isinstance(parameter, ResBasicParameter)
    assert parameter.actual_instance == custom_param_value
    assert res_model_state_info.model_state.data == custom_data
    assert res_model_state_info.model_state.image_url is None

    # Fetch only parameters and data of the Model-State.
    res_model_state_data = ModelStateApi(client).get_model_state_data(model_state_id)
    parameter = res_model_state_data.model_state.parameters[
        custom_param_id
    ].actual_instance
    assert isinstance(parameter, ResBasicParameter)
    assert parameter.actual_instance == custom_param_value
    assert res_model_state_data.model_state.data == custom_data

    # Check if the Model-State has an image.
    try:
        ModelStateApi(client).get_model_state_image_metadata_with_http_info(
            model_state_id
        )
    except NotFoundException:
        pass  # That's what we except
    else:
        assert False, "Expected NotFoundException not raised"

    # Fetch all Model-States of a model.
    res_list = ModelStateApi(backend_client).list_model_states(
        res_model_state.model_state.model_id
    )
    assert len(res_list.list.model_state) > 0

    # Delete the Model-State.
    ModelStateApi(backend_client).delete_model_state(model_state_id)

    # Close the session.
    SessionApi(client).close_session(session_id)


def test_model_state_with_image(utils, host, jwt_backend):
    backend_client = SdClient(Configuration(host, access_token=jwt_backend))
    client = SdClient(Configuration(host))

    # Initialize a new session.
    ticket = utils.create_ticket()
    res_session = SessionApi(client).create_session_by_ticket(ticket)
    session_id = res_session.session_id

    # Create a new Model-State and request an image upload.
    with open("tests/data/logo.jpg", "rb") as f:
        s = f.read()

        req_model_state = ReqModelState(
            parameters=ReqCustomization(),
            image=ReqFileDefinition(
                filename="ShapeDiver_Logo.jpg", format="image/jpeg", size=len(s)
            ),
        )
        res_model_state = ModelStateApi(client).create_model_state(
            session_id, req_model_state
        )
        assert res_model_state.asset and res_model_state.asset.model_state is not None
        model_state_id = res_model_state.model_state.id
        image = res_model_state.asset.model_state

        # Upload the image.
        res_upload = sd_utils.upload_asset(image.href, s, image.headers)
        assert res_upload.status == 200

    # Check if the Model-State has an image.
    res_image_metadata = ModelStateApi(
        client
    ).get_model_state_image_metadata_with_http_info(model_state_id)
    assert res_image_metadata.status_code == 200

    # Download the uploaded image.
    res_image = ModelStateApi(client).download_model_state_image(model_state_id)
    assert len(res_image) > 0

    # Fetch all available information of the Model-State.
    res_model_state_info = ModelStateApi(client).get_model_state(model_state_id)
    assert res_model_state_info.model_state.parameters is not None
    assert res_model_state_info.model_state.data is None
    assert res_model_state_info.model_state.image_url is not None

    # Delete the Model-State.
    ModelStateApi(backend_client).delete_model_state(model_state_id)

    # Close the session.
    SessionApi(client).close_session(session_id)
