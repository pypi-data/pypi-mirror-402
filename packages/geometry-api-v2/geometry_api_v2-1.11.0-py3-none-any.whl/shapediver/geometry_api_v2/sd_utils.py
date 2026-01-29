import re
import time
import unicodedata
import urllib.parse
from typing import Any, Mapping, Optional, Union

from shapediver.geometry_api_v2 import (
    ApiException,
    Configuration,
    ExportApi,
    OutputApi,
    ReqCache,
    ReqCustomization,
    ReqCustomizationOrCache,
    ReqExport,
    ReqExportOrCache,
    ResAssetUploadHeaders,
    ResComputeExports,
    ResComputeOutputs,
    ResExport,
    ResGetCachedExports,
    ResGetCachedOutputs,
    ResOutput,
    SdClient,
    rest,
)


def upload(
    url: str,
    data: Union[bytes, bytearray, dict[str, Any], str],
    content_type: str,
    filename: Optional[str] = None,
) -> rest.RESTResponseType:
    """Upload the given file to the specified URL.

    :param url: The target URL of the upload request.
    :param data: The data that should be uploaded.
    :param contentType: Indicate the original media type of the resource.
    :param filename: The name of the file to be uploaded. When a filename
        has been specified in the request-upload call, then the same
        filename has to be specified for the upload as well.
    """

    # Prepare headers for the upload.
    headers = {"Content-Type": content_type}
    if filename:
        headers["Content-Disposition"] = _content_disposition_from_filename(filename)

    # Create new client instance to remove authorization and custom headers.
    client = SdClient(Configuration(host=url))

    response_data = client.call_api("PUT", url, headers, data)
    return response_data.response


def upload_asset(
    url: str,
    data: Union[bytes, bytearray, dict[str, Any], str],
    headers: ResAssetUploadHeaders,
) -> rest.RESTResponseType:
    """Upload the given asset to the specified ShapeDiver URL.

    :param url: The target URL of the upload request.
    :param data: The data that should be uploaded.
    :param headers: The headers object that was returned from the request-upload call.
    """

    # Prepare headers for the upload.
    resHeaders = {"Content-Type": headers.content_type}
    if headers.content_disposition:
        resHeaders["Content-Disposition"] = headers.content_disposition

    # Create new client instance to remove authorization and custom headers.
    client = SdClient(Configuration(host=url))

    response_data = client.call_api("PUT", url, resHeaders, data)
    return response_data.response


def download(url: str) -> rest.RESTResponseType:
    """Download from the specified URL.

    :param url: The target URL of the download request.
    """

    # Create new client instance to remove authorization and custom headers.
    client = SdClient(Configuration(host=url))

    response_data = client.call_api("GET", url)
    return response_data.response


class FileInfo:
    def __init__(self, size: Optional[int], filename: Optional[str]):
        self.size = size
        self.filename = filename


def extract_file_info(headers: Optional[Mapping[str, str]]) -> FileInfo:
    """
    Parse HTTP headers to extract size and filename information.

    :param headers: The HTTP headers of a file-metadata response.
    """
    if headers is None:
        return FileInfo(size=None, filename=None)

    # Extract size from Content-Length header
    size = (
        int(str(headers.get("Content-Length"))) if "Content-Length" in headers else None
    )

    # Extract filename from Content-Disposition header
    filename = (
        _filename_from_content_disposition(str(headers.get("Content-Disposition")))
        if "Content-Disposition" in headers
        else None
    )

    return FileInfo(size=size, filename=filename)


def _content_disposition_from_filename(filename: str) -> str:
    """
    Set content headers according to RFC 5987

    :param filename: The file name to use.
    """
    ascii_name = (
        unicodedata.normalize("NFKD", filename).encode("ascii", "ignore").decode()
    )
    header = '{}; filename="{}"'.format("attachment", ascii_name)
    if ascii_name != filename:
        quoted_name = urllib.parse.quote(filename)
        header += "; filename*=UTF-8''{}".format(quoted_name)

    return header


def _filename_from_content_disposition(content_disposition: str) -> Optional[str]:
    """
    Extract and return the filename from a content-disposition HTTP header.
    Decodes the filename* property if set.

    :param content_disposition: Content-Disposition header value
    :return: Extracted filename
    """
    filename = None
    filename_star = None

    # Search for filename
    match = re.search(r'filename="([^"]+)"', content_disposition)
    if match:
        filename = match.group(1)

    # Search for filename*
    match_star = re.search(r"filename\*=([^\'\']+\'\')?(.+)", content_disposition)
    if match_star:
        encoding = match_star.group(1)[:-2] if match_star.group(1) else "utf-8"
        encoded_filename = match_star.group(2)
        filename_star = urllib.parse.unquote(encoded_filename, encoding=encoding)

    # Prefer filename* over filename
    return filename_star if filename_star else filename


def submit_and_wait_for_output(
    client: SdClient,
    session_id: str,
    body: ReqCustomization,
    max_wait_ms: int,
    ignoreUnknownParams: Optional[bool] = False,
) -> Union[ResComputeOutputs, ResGetCachedOutputs]:
    """Submit a customization request and wait for the result to be finished.

    :param client: The client instance to be used.
    :param session_id: The session ID of the model.
    :param body: The customization request to be submitted.
    :param max_wait_ms: The maximum time to wait for results, in milliseconds.
        Pass a value smaller than zero to disable this limit.
    :param ignoreUnknownParams: Allow relaxed validation of parameter identifiers.
        When set to `true`, unrecognized parameters will be ignored rather than causing an error.
        Defaults to `false`.
    """
    start_time = time.time()
    res = OutputApi(client).compute_outputs(session_id, body, ignoreUnknownParams)
    elapsed_time_ms = (time.time() - start_time) * 1000

    remaining_max_wait = (
        max_wait_ms if max_wait_ms < 0 else max(0, max_wait_ms - elapsed_time_ms)
    )

    return _wait_for_output_result(client, session_id, res, remaining_max_wait)


def submit_and_wait_for_export(
    client: SdClient,
    session_id: str,
    body: ReqExport,
    max_wait_ms: int,
    ignoreUnknownParams: Optional[bool] = False,
) -> Union[ResComputeExports, ResGetCachedExports]:
    """Submit an export request and wait for the result to be finished.

    :param client: The client instance to be used.
    :param session_id: The session ID of the model.
    :param body: The export request to be submitted.
    :param max_wait_ms: The maximum time to wait for results, in milliseconds.
        Pass a value smaller than zero to disable this limit.
    :param ignoreUnknownParams: Allow relaxed validation of parameter identifiers.
        When set to `true`, unrecognized parameters will be ignored rather than causing an error.
        Defaults to `false`.
    """
    start_time = time.time()
    res = ExportApi(client).compute_exports(session_id, body, ignoreUnknownParams)
    elapsed_time_ms = (time.time() - start_time) * 1000

    remaining_max_wait = (
        max_wait_ms if max_wait_ms < 0 else max(0, max_wait_ms - elapsed_time_ms)
    )

    return _wait_for_export_result(client, session_id, body, res, remaining_max_wait)


def _wait_for_output_result(
    client: SdClient,
    session_id: str,
    res_compute: ResComputeOutputs,
    max_wait_ms: float,
) -> Union[ResComputeOutputs, ResGetCachedOutputs]:
    """Wait for the result of a customization request to be finished.

    :param client: The client instance to be used.
    :param session_id: The session ID of the model.
    :param res_compute: The customization request result to be waited for.
    :param max_wait_ms: The maximum time to wait for results, in milliseconds.
        Pass a value smaller than zero to disable this limit.
    """

    if res_compute.outputs is None:
        return res_compute

    # Build new cache request
    req_cache = ReqCache(
        additional_properties={
            output.actual_instance.id: output.actual_instance.version
            for output in res_compute.outputs.values()
            if isinstance(output.actual_instance, ResOutput)
        }
    )

    delay = _get_max_output_delay(res_compute)
    start_time = time.time()

    res_cache: Union[ResGetCachedOutputs, None] = None
    while delay > 0:
        # Check whether the maximum waiting time has been reached.
        if max_wait_ms >= 0:
            elapsed_time_ms = (time.time() - start_time) * 1000
            if elapsed_time_ms > max_wait_ms:
                raise ApiException(
                    f"Maximum waiting time of {max_wait_ms} ms exceeded."
                )
            if elapsed_time_ms + delay > max_wait_ms:
                delay = max(0, max_wait_ms - elapsed_time_ms)

        time.sleep(delay / 1000)

        res_cache = OutputApi(client).get_cached_outputs(
            session_id, ReqCustomizationOrCache(req_cache)
        )
        delay = _get_max_output_delay(res_cache)

    return res_cache or res_compute


def _wait_for_export_result(
    client: SdClient,
    session_id: str,
    req_body: ReqExport,
    res_compute: ResComputeExports,
    max_wait_ms: float,
) -> Union[ResComputeExports, ResGetCachedExports]:
    """Wait for the result of an export request to be finished.

    :param client: The client instance to be used.
    :param session_id: The session ID of the model.
    :param req_body: The request body containing export details.
    :param res_compute: The export request result to be waited for.
    :param max_wait_ms: The maximum time to wait for results, in milliseconds.
        Pass a value smaller than zero to disable this limit.
    """

    delay = _get_max_export_delay(req_body, res_compute)
    start_time = time.time()

    res_cache: Union[ResGetCachedExports, None] = None
    while delay > 0:
        # Check whether the maximum waiting time has been reached.
        if max_wait_ms >= 0:
            elapsed_time_ms = (time.time() - start_time) * 1000
            if elapsed_time_ms > max_wait_ms:
                raise ApiException(
                    f"Maximum waiting time of {max_wait_ms} ms exceeded."
                )
            if elapsed_time_ms + delay > max_wait_ms:
                delay = max(0, max_wait_ms - elapsed_time_ms)

        time.sleep(delay / 1000)

        res_cache = ExportApi(client).get_cached_exports(
            session_id, ReqExportOrCache(req_body)
        )
        delay = _get_max_export_delay(req_body, res_cache)

    return res_cache or res_compute


def _get_max_output_delay(dto: Union[ResComputeOutputs, ResGetCachedOutputs]) -> int:
    """Get the maximum delay of all outputs in the given result.

    Returns `-1` in case no delay was reported.
    """

    delays = [
        output.actual_instance.delay
        for output in (dto.outputs or {}).values()
        if isinstance(output.actual_instance, ResOutput)
        and output.actual_instance.delay is not None
    ]

    return max(delays, default=-1)


def _get_max_export_delay(
    body: ReqExport,
    dto: Union[ResComputeExports, ResGetCachedExports],
) -> int:
    """Get the maximum delay of all exports and outputs in the given result.

    Returns `-1` in case no delay was reported.
    """

    exports = body.exports
    outputs = body.outputs or []

    delays = [
        export.actual_instance.delay
        for export in (dto.exports or {}).values()
        if isinstance(export.actual_instance, ResExport)
        and export.actual_instance.id in exports
        and export.actual_instance.delay is not None
    ] + [
        output.actual_instance.delay
        for output in (dto.outputs or {}).values()
        if isinstance(output.actual_instance, ResOutput)
        and output.actual_instance.id in outputs
        and output.actual_instance.delay is not None
    ]

    return max(delays, default=-1)
