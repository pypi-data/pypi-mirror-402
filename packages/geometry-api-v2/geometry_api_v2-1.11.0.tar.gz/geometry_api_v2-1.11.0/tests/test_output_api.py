from shapediver.geometry_api_v2 import (
    Configuration,
    OutputApi,
    ReqCache,
    ReqCustomization,
    ReqCustomizationOrCache,
    ReqOutputDefinition,
    ReqOutputDefinitions,
    ResOutput,
    SdClient,
    SessionApi,
    sd_utils,
)


def test_outputs(utils, host, jwt_model, model_id):
    model_client = SdClient(Configuration(host, access_token=jwt_model))
    client = SdClient(Configuration(host))

    # Initialize a new session.
    ticket = utils.create_ticket()
    res_session = SessionApi(client).create_session_by_ticket(ticket)
    session_id = res_session.session_id
    assert res_session.outputs and res_session.parameters
    assert len(res_session.outputs.keys()) > 0

    # Get first output.
    output = next(iter(res_session.outputs.values())).actual_instance
    assert output

    # Compute a new output version and wait until the computation has been finished. For the sake
    # of simplicity, we use the default values of all parameters that the output depends on.
    req_comp = ReqCustomization(
        additional_properties={
            param_id: res_session.parameters[param_id].defval
            for param_id in output.dependency
        }
    )
    res_comp = sd_utils.submit_and_wait_for_output(client, session_id, req_comp, -1)
    assert res_comp.outputs and res_comp.outputs[output.id]

    # Alternatively, we can trigger the output computation without waiting for the result.
    res_comp = OutputApi(client).compute_outputs(session_id, req_comp)
    assert res_comp.outputs and res_comp.outputs[output.id]

    output_comp = res_comp.outputs[output.id].actual_instance
    assert isinstance(output_comp, ResOutput)

    # Get the already computed output from cache.
    res_cached = OutputApi(client).get_cached_outputs(
        session_id,
        ReqCustomizationOrCache(
            ReqCache(additional_properties={output.id: output_comp.version})
        ),
    )
    assert res_cached.outputs and res_cached.outputs[output.id]

    # Update the output definition.
    OutputApi(model_client).update_output_definitions(
        model_id,
        ReqOutputDefinitions(
            additional_properties={
                output.id: ReqOutputDefinition(
                    tooltip=f"Updated via Python SDK, {utils.now()}"
                ),
            }
        ),
    )

    # List versions of an output.
    res_list = OutputApi(model_client).list_output_versions(session_id, output.id)
    assert len(res_list.list.output) > 0

    # Close the session.
    SessionApi(client).close_session(session_id)
