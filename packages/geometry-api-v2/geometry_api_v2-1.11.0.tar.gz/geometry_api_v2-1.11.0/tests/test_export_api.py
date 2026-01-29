from shapediver.geometry_api_v2 import (
    Configuration,
    ExportApi,
    ReqCache,
    ReqCustomization,
    ReqExport,
    ReqExportDefinition,
    ReqExportDefinitions,
    ReqExportOrCache,
    ResExport,
    SdClient,
    SessionApi,
    sd_utils,
)


def test_exports(utils, host, jwt_model, model_id):
    model_client = SdClient(Configuration(host, access_token=jwt_model))
    client = SdClient(Configuration(host))

    # Initialize a new session.
    ticket = utils.create_ticket()
    res_session = SessionApi(client).create_session_by_ticket(ticket)
    session_id = res_session.session_id
    assert res_session.exports and res_session.parameters
    assert len(res_session.exports.keys()) > 0

    # Get first export.
    export = next(iter(res_session.exports.values())).actual_instance
    assert export

    # Compute a new export version and wait until the computation has been finished. For the sake
    # of simplicity, we use the default values of all parameters that the export depends on.
    req_comp = ReqExport(
        parameters=ReqCustomization(
            additional_properties={
                param_id: res_session.parameters[param_id].defval
                for param_id in export.dependency
            }
        ),
        exports=[export.id],
    )
    res_comp = sd_utils.submit_and_wait_for_export(client, session_id, req_comp, -1)
    assert res_comp.exports and res_comp.exports[export.id]

    # Alternatively, we can trigger the export computation without waiting for the result.
    res_comp = ExportApi(client).compute_exports(session_id, req_comp)
    assert res_comp.exports and res_comp.exports[export.id]

    export_comp = res_comp.exports[export.id].actual_instance
    assert isinstance(export_comp, ResExport)

    # Get the already computed export from cache.
    res_cached = ExportApi(client).get_cached_exports(
        session_id,
        ReqExportOrCache(
            ReqCache(additional_properties={export.id: export_comp.version})
        ),
    )
    assert res_cached.exports and res_cached.exports[export.id]

    # Update the export definition.
    ExportApi(model_client).update_export_definitions(
        model_id,
        ReqExportDefinitions(
            additional_properties={
                export.id: ReqExportDefinition(
                    tooltip=f"Updated via Python SDK, {utils.now()}"
                ),
            }
        ),
    )

    # List versions of an export.
    res_list = ExportApi(model_client).list_export_versions(session_id, export.id)
    assert len(res_list.list.export) > 0

    # Close the session.
    SessionApi(client).close_session(session_id)
