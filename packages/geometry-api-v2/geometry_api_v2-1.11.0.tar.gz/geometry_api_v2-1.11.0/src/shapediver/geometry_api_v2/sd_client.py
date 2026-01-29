from time import sleep
from typing import Any, Optional

from shapediver.geometry_api_v2.client import ApiClient, ApiException, Configuration
from shapediver.geometry_api_v2.client import rest


class SdClient(ApiClient):
    """API Client for the ShapeDiver Geometry API v2.

    :param configuration: Configuration object for this client.
    :param headers: Additional headers to pass when making calls to
        the API.
    :param max_retries: Maximum number of retries per request. Only
        retries on '429' and '502' status codes.
    :param max_retry_wait: Maximum number of seconds to wait between
        retries.
    """

    _sdk_version = "1.11.0"  # WARNING: This value is updated automatically!

    def __init__(
        self,
        configuration: Optional[Configuration] = None,
        headers: Optional[dict[str, Any]] = None,
        *,
        max_retries: int = 5,
        max_retry_wait: Optional[int] = None,
    ):
        super().__init__(configuration, None, None, None)

        self.max_retries = max_retries
        self.max_retry_wait = max_retry_wait

        # Override default user agent header.
        self.set_default_header("User-Agent", "sd-sdk/python/" + self._sdk_version)

        # Set custom headers if specified.
        if headers is not None:
            for key, value in headers.items():
                self.set_default_header(key, value)

    # Wrapper around client/api_client.py
    def call_api(
        self,
        method,
        url,
        header_params=None,
        body=None,
        post_params=None,
        _request_timeout=None,
    ) -> rest.RESTResponse:
        """Makes the HTTP request (synchronous)
        :param method: Method to call.
        :param url: Path to method endpoint.
        :param header_params: Header parameters to be
            placed in the request header.
        :param body: Request body.
        :param post_params dict: Request post form parameters,
            for `application/x-www-form-urlencoded`, `multipart/form-data`.
        :param _request_timeout: timeout setting for this request.
        :return: RESTResponse
        """

        retry_counter = 0
        while True:
            response_data = super().call_api(
                method, url, header_params, body, post_params, _request_timeout
            )

            wait_sec = None

            # Check for special response statuses.
            if response_data.status == 429:
                # 429 Too Many Requests - Try to extract waiting time from Retry-After header.
                wait_sec = response_data.getheader("Retry-After")
                if wait_sec is None:
                    wait_sec = 60  # Default is 1 minute
            elif response_data.status == 502:
                # 502 Bad Gateway - Try again after short pause.
                wait_sec = 1

            # Retry or throw.
            if wait_sec is not None:
                if retry_counter < self.max_retries:
                    retry_counter += 1
                    wait_sec = int(wait_sec)

                    if self.max_retry_wait is not None:
                        wait_sec = min(wait_sec, self.max_retry_wait)

                    sleep(wait_sec)
                    continue
                else:
                    raise ApiException(
                        status=response_data.status, reason="Retry limit exceeded."
                    )
            else:
                return response_data
