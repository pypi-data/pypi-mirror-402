from pytest import raises

from shapediver.geometry_api_v2 import (
    ApiException,
    Configuration,
    ModelApi,
    QueryComputationStatisticsStatus,
    QueryModelStatus,
    ReqConfigure,
    ReqCustomization,
    ReqModel,
    ReqModelBlockingReasons,
    ReqParameterDefinitions,
    SdClient,
    SessionApi,
)


def test_model_config(host, jwt_model, model_id):
    model_client = SdClient(Configuration(host, access_token=jwt_model))

    # Fetch the model configuration.
    res_config = ModelApi(model_client).get_model_config(model_id)
    assert len(res_config.viewer.config.keys()) > 0

    # Update the model configuration. However, for the sake of simplicity, we will re-use the
    # already existing configuration object.
    req_config = ReqConfigure(additional_properties=res_config.viewer.config)
    ModelApi(model_client).update_model_config(model_id, req_config)


def test_model(host, jwt_backend, jwt_model, model_id):
    backend_client = SdClient(Configuration(host, access_token=jwt_backend))
    model_client = SdClient(Configuration(host, access_token=jwt_model))

    # Fetch a model.
    res_get = ModelApi(model_client).get_model(model_id)
    assert res_get.model.id == model_id

    # Download the model's Grasshopper file.
    res_gh = ModelApi(model_client).download_model_file(model_id)
    assert len(res_gh) > 0

    # Get the model's computation statistics by status.
    res_comp = ModelApi(model_client).get_model_computations(
        model_id=model_id,
        status=QueryComputationStatisticsStatus.SUCCESS,
        timestamp_from="20240614155603054",
        timestamp_to="20240627072220908",
    )
    assert len(res_comp.computations) >= 0

    # Update a model.
    req_update = ReqModel(pub=True, backendaccess=True, use_cdn=True)
    res_update = ModelApi(backend_client).update_model(model_id, req_update)
    assert res_update.model.id == model_id

    # List all models with a specific status.
    res_list = ModelApi(backend_client).list_models(
        model_status=QueryModelStatus.DENIED
    )
    assert len(res_list.list.model) > 0


def test_cleanup(host, jwt_model, model_id):
    model_client = SdClient(Configuration(host, access_token=jwt_model))

    # Trigger an export cleanup.
    ModelApi(model_client).cleanup_exports(model_id, "2024")

    # Trigger an output cleanup.
    ModelApi(model_client).cleanup_outputs(model_id, "2024")

    # Trigger an texture cleanup.
    ModelApi(model_client).cleanup_textures(model_id, "2024")

    # Get the cleanup status.
    res_cleanup = ModelApi(model_client).get_cleanup_status(model_id)
    assert len(res_cleanup.cleanup) > 0


def test_parameters(utils, host, jwt_model, model_id):
    model_client = SdClient(Configuration(host, access_token=jwt_model))

    # Fetch a model.
    res_model = ModelApi(model_client).get_model(model_id)
    assert res_model.parameters
    assert len(res_model.parameters.keys()) > 0

    # Update the model's parameter default values. However, for the sake of simplicity, we are
    # going to reuse the currently set default values.
    req_defval = ReqCustomization(
        additional_properties={id: p.defval for id, p in res_model.parameters.items()}
    )
    ModelApi(model_client).update_parameter_default_values(model_id, req_defval)

    # Update the model's parameter definitions.
    tooltip = f"Updated via Python SDK, {utils.now()}"
    req_param = ReqParameterDefinitions(
        additional_properties={id: {"tooltip": tooltip} for id in res_model.parameters}
    )
    ModelApi(model_client).update_parameter_definitions(model_id, req_param)


def test_model_blocking(host, jwt_model, jwt_backend, model_id):
    model_client = SdClient(Configuration(host, access_token=jwt_model))
    backend_client = SdClient(Configuration(host, access_token=jwt_backend))

    # Fetch a model.
    res_model = ModelApi(backend_client).get_model(model_id)
    assert res_model.setting.model
    res_blocking_reasons = res_model.setting.model.blocking_reasons
    assert res_blocking_reasons
    assert res_blocking_reasons.owner == False
    assert res_blocking_reasons.credit_limit == False
    assert res_blocking_reasons.plugin_permission == False

    # Block the model.
    req_blocking = ReqModel(blockingReasons=ReqModelBlockingReasons(owner=True))
    ModelApi(backend_client).update_model(model_id, req_blocking)

    # Fetch a model.
    res_model = ModelApi(backend_client).get_model(model_id)
    assert res_model.setting.model
    res_blocking_reasons = res_model.setting.model.blocking_reasons
    assert res_blocking_reasons
    assert res_blocking_reasons.owner == True
    assert res_blocking_reasons.credit_limit == False
    assert res_blocking_reasons.plugin_permission == False

    # Init session should not work anymore.
    with raises(ApiException):
        SessionApi(model_client).create_session_by_model(model_id)

    # Unblock the model.
    req_blocking = ReqModel(blockingReasons=ReqModelBlockingReasons(owner=False))
    ModelApi(backend_client).update_model(model_id, req_blocking)

    # Session init should work again.
    session_id = SessionApi(model_client).create_session_by_model(model_id).session_id
    SessionApi(model_client).close_session(session_id)


def test_soft_delete_and_restore(host, jwt_model, jwt_backend, model_id):
    backend_client = SdClient(Configuration(host, access_token=jwt_backend))
    model_client = SdClient(Configuration(host, access_token=jwt_model))

    # Soft-delete a model.
    ModelApi(backend_client).delete_model(model_id)

    # Fetch the model should not work anymore.
    with raises(ApiException):
        ModelApi(model_client).get_model(model_id)

    # Restore the model.
    ModelApi(backend_client).restore_model(model_id)

    # Fetching the model should work again.
    ModelApi(model_client).get_model(model_id)
