from datetime import datetime, timedelta
from typing import Optional, Union

import pytest

from shapediver.geometry_api_v2 import (
    Configuration,
    ReqTicket,
    ReqTicketType,
    SdClient,
    SessionApi,
)

_host = "https://sddev2.eu-central-1.shapediver.com"
_jwt_backend = ""
_jwt_model = ""
_model_id = "1393fc7c-7e9c-488a-99a9-6df70dad17c8"


@pytest.fixture
def host() -> str:
    return _get_required_env(_host, "ShapeDiver host")


@pytest.fixture
def jwt_backend() -> str:
    return _get_required_env(_jwt_backend, "JWT-Backend")


@pytest.fixture
def jwt_model() -> str:
    return _get_required_env(_jwt_model, "JWT-Model")


@pytest.fixture
def model_id() -> str:
    return _get_required_env(_model_id, "Model ID")


def _get_required_env(var: Union[str, None], var_name: str) -> str:
    """Retrieve the required environment variable or raise an error if not set."""
    if var is not None:
        return var
    else:
        raise ValueError(f"{var_name} is not set!")


class Utils:
    @staticmethod
    def create_ticket() -> str:
        req_ticket = ReqTicket(
            pub=True,
            author=True,
            type=ReqTicketType.BACKEND,
            until=Utils.now(timedelta(minutes=2)),
        )
        backend_client = SdClient(Configuration(_host, access_token=_jwt_backend))
        res_ticket = SessionApi(backend_client).create_ticket(_model_id, req_ticket)
        return res_ticket.ticket

    @staticmethod
    def now(diff: Optional[timedelta] = None) -> str:
        """Return the date time in numeric ISO-8601 format."""
        current_time = datetime.now()
        if diff:
            current_time += diff

        return current_time.replace(microsecond=0).strftime("%Y%m%d%H%M%S")


@pytest.fixture
def utils() -> type[Utils]:
    return Utils
