from shapediver.geometry_api_v2 import (
    AnalyticsApi,
    Configuration,
    ReqAnyCreditMetricId,
    ReqCreditMetric,
    ReqCreditMetrics,
    ReqModelCreditMetricId,
    ReqModelStatistic,
    ReqModelStatistics,
    SdClient,
    SessionApi,
)


def test_model_session_statistics(utils, host, jwt_model, model_id):
    model_client = SdClient(Configuration(host, access_token=jwt_model))

    # Initialize a new session.
    ticket = utils.create_ticket()
    session_id = SessionApi(model_client).create_session_by_ticket(ticket).session_id

    # Fetch model statistics within a specific time range.
    req_stats = ReqModelStatistics(
        parameters=[
            ReqModelStatistic(
                modelid=[model_id],
                timestamp_from="2024",
                timestamp_to="2025",
            )
        ]
    )
    res_stats = AnalyticsApi(model_client).get_model_statistics(req_stats)
    assert len(res_stats.analytics.models) > 0

    # Close the session.
    SessionApi(model_client).close_session(session_id)


def test_credit_metrics(utils, host, jwt_model, model_id):
    model_client = SdClient(Configuration(host, access_token=jwt_model))

    # Initialize a new session.
    ticket = utils.create_ticket()
    session_id = SessionApi(model_client).create_session_by_ticket(ticket).session_id

    # Fetch credit metrics within a specific time range.
    req_credits = ReqCreditMetrics(
        parameters=[
            ReqCreditMetric(
                id=ReqAnyCreditMetricId(ReqModelCreditMetricId(modelIds=[model_id])),
                timestamp_from="2024",
                timestamp_to="2025",
            )
        ]
    )
    res_credits = AnalyticsApi(model_client).get_credit_metrics(req_credits)
    assert len(res_credits.analytics.credit_metrics) > 0

    # Close the session.
    SessionApi(model_client).close_session(session_id)


def test_user_credit_metrics(host, jwt_backend):
    backend_client = SdClient(Configuration(host, access_token=jwt_backend))

    res_credits = AnalyticsApi(backend_client).get_user_credit_metrics("202407")
    assert len(res_credits.analytics.credit_metrics) > 0


def test_organization_credit_metrics(host, jwt_backend):
    backend_client = SdClient(Configuration(host, access_token=jwt_backend))

    res_credits = AnalyticsApi(backend_client).get_organization_credit_metrics("202407")
    assert len(res_credits.analytics.credit_metrics) > 0


def test_model_user_credit_metrics(host, jwt_backend):
    backend_client = SdClient(Configuration(host, access_token=jwt_backend))

    user_id = "92a8410b-6496-4b86-8c3f-1014d59f7fa3"
    res_credits = AnalyticsApi(backend_client).get_model_user_credit_metrics(
        "202407", user_id
    )
    assert len(res_credits.analytics.credit_metrics) > 0


def test_model_organization_credit_metrics(host, jwt_backend):
    backend_client = SdClient(Configuration(host, access_token=jwt_backend))

    org_id = "a785380e-183d-11ef-926a-f3f7d2b9f407"
    res_credits = AnalyticsApi(backend_client).get_model_organization_credit_metrics(
        "202407", org_id
    )
    assert len(res_credits.analytics.credit_metrics) > 0
