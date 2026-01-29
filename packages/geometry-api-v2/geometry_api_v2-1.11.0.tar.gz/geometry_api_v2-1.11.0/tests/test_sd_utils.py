from unittest import TestCase
from unittest.mock import patch

from shapediver.geometry_api_v2 import (
    ApiException,
    ReqCache,
    ReqCustomization,
    ReqCustomizationOrCache,
    ReqExport,
    ResComputeExports,
    ResComputeOutputs,
    ResExport,
    ResExportDefinition,
    ResExportDefinitionType,
    ResExportOrDefinition,
    ResGetCachedExports,
    ResGetCachedOutputs,
    ResOutput,
    ResOutputDefinition,
    ResOutputOrDefinition,
    SdClient,
    sd_utils,
)


class Test_extract_file_info(TestCase):

    def test_no_header(self):
        res = sd_utils.extract_file_info(None)
        assert res.filename is None
        assert res.size is None

    def test_full_header(self):
        res = sd_utils.extract_file_info(
            {
                "Content-Length": "165030",
                "Content-Disposition": 'attachment ; filename="foobar.txt"',
            }
        )
        assert res.filename == "foobar.txt"
        assert res.size == 165030


class Test_content_disposition_from_filename(TestCase):

    def test_ascii_characters(self):
        res = sd_utils._content_disposition_from_filename("foobar.txt")
        assert res == 'attachment; filename="foobar.txt"'

    def test_non_ascii_characters(self):
        res = sd_utils._content_disposition_from_filename("ä€öü.jpg")
        assert (
            res
            == 'attachment; filename="aou.jpg"; '
            + "filename*=UTF-8''a%CC%88%E2%82%ACo%CC%88u%CC%88.jpg"
        )


class Test_filename_from_content_disposition(TestCase):

    def test_invalid_format(self):
        res = sd_utils._filename_from_content_disposition(
            'attachment; somethign="else"'
        )
        assert res is None

    def test_ascii_characters(self):
        res = sd_utils._filename_from_content_disposition(
            'attachment; filename="foobar.txt"'
        )
        assert res == "foobar.txt"

    def test_non_ascii_characters_with_encoding(self):
        res = sd_utils._filename_from_content_disposition(
            "attachment; filename=\"aou.jpg\"; filename*=UTF-8''a%CC%88%E2%82%ACo%CC%88u%CC%88.jpg"
        )
        assert res == "ä€öü.jpg"

    def test_non_ascii_characters_without_encoding(self):
        res = sd_utils._filename_from_content_disposition(
            'attachment; filename="aou.jpg"; filename*=a%CC%88%E2%82%ACo%CC%88u%CC%88.jpg'
        )
        assert res == "ä€öü.jpg"


class Test_wait_for_output_result(TestCase):

    client = SdClient()
    session_id = "12a210fa-2804-11ef-b7a5-1bc3e7751d5d"

    @patch("shapediver.geometry_api_v2.sd_utils._get_max_output_delay")
    def test_no_outputs(self, mock_get_max_output_delay):
        res_compute = ResComputeOutputs(version="1")
        res = sd_utils._wait_for_output_result(
            self.client,
            self.session_id,
            res_compute,
            123.4,
        )

        assert res is res_compute
        mock_get_max_output_delay.assert_not_called()

    @patch("shapediver.geometry_api_v2.client.OutputApi")
    def test_negative_delay(self, mock_OutputApi):
        res_compute = ResComputeOutputs(
            version="1",
            outputs={
                "33c694f3a090a06560777870d3d1d317": ResOutputOrDefinition(
                    ResOutput(
                        id="33c694f3a090a06560777870d3d1d317",
                        version="c8b8874fda26cee295faf97d22dcbb5b",
                        name="some-name",
                        hidden=False,
                        dependency=[],
                    )
                ),
            },
        )
        res = sd_utils._wait_for_output_result(
            self.client, self.session_id, res_compute, -1
        )

        assert res is res_compute
        mock_OutputApi.get_cached_outputs.assert_not_called()

    @patch("shapediver.geometry_api_v2.client.OutputApi.get_cached_outputs")
    def test_positive_delay_and_no_timeout(self, mock_get_cached_outputs):
        res_cache = ResGetCachedOutputs(
            version="1",
            outputs={
                "33c694f3a090a06560777870d3d1d317": ResOutputOrDefinition(
                    ResOutput(
                        id="33c694f3a090a06560777870d3d1d317",
                        version="22e93a3339da89bd6d4e027614c8f644",
                        name="some-name",
                        hidden=False,
                        dependency=[],
                        content=[],
                    )
                ),
                "6298d3d386252e6c0d2a0606fa17b470": ResOutputOrDefinition(
                    ResOutput(
                        id="6298d3d386252e6c0d2a0606fa17b470",
                        version="526d24be587bbd8ad9ef09c19295d5e1",
                        name="some-name",
                        hidden=False,
                        dependency=[],
                        content=[],
                    )
                ),
            },
        )

        # Mock
        mock_get_cached_outputs.return_value = res_cache

        res = sd_utils._wait_for_output_result(
            self.client,
            self.session_id,
            ResComputeOutputs(
                version="1",
                outputs={
                    "0ca411fecc995160971ed9d965acd218": ResOutputOrDefinition(
                        ResOutputDefinition(
                            id="0ca411fecc995160971ed9d965acd218",
                            name="some-name",
                            hidden=False,
                            dependency=[],
                        )
                    ),
                    "33c694f3a090a06560777870d3d1d317": ResOutputOrDefinition(
                        ResOutput(
                            id="33c694f3a090a06560777870d3d1d317",
                            version="22e93a3339da89bd6d4e027614c8f644",
                            name="some-name",
                            hidden=False,
                            dependency=[],
                        )
                    ),
                    "6298d3d386252e6c0d2a0606fa17b470": ResOutputOrDefinition(
                        ResOutput(
                            id="6298d3d386252e6c0d2a0606fa17b470",
                            version="526d24be587bbd8ad9ef09c19295d5e1",
                            name="some-name",
                            hidden=False,
                            dependency=[],
                            delay=100,
                        )
                    ),
                },
            ),
            123.4,
        )

        assert res is res_cache
        mock_get_cached_outputs.assert_called_once_with(
            self.session_id,
            ReqCustomizationOrCache(
                ReqCache(
                    additional_properties={
                        "33c694f3a090a06560777870d3d1d317": "22e93a3339da89bd6d4e027614c8f644",
                        "6298d3d386252e6c0d2a0606fa17b470": "526d24be587bbd8ad9ef09c19295d5e1",
                    }
                )
            ),
        )

    @patch("shapediver.geometry_api_v2.client.OutputApi.get_cached_outputs")
    def test_positive_delay_and_timeout(self, mock_get_cached_outputs):
        res_cache = ResGetCachedOutputs(
            version="1",
            outputs={
                "33c694f3a090a06560777870d3d1d317": ResOutputOrDefinition(
                    ResOutput(
                        id="33c694f3a090a06560777870d3d1d317",
                        version="22e93a3339da89bd6d4e027614c8f644",
                        name="some-name",
                        hidden=False,
                        dependency=[],
                        delay=250,
                    )
                ),
            },
        )

        # Mock
        mock_get_cached_outputs.return_value = res_cache

        with self.assertRaises(ApiException):
            sd_utils._wait_for_output_result(
                self.client,
                self.session_id,
                ResComputeOutputs(
                    version="1",
                    outputs={
                        "33c694f3a090a06560777870d3d1d317": ResOutputOrDefinition(
                            ResOutput(
                                id="33c694f3a090a06560777870d3d1d317",
                                version="22e93a3339da89bd6d4e027614c8f644",
                                name="some-name",
                                hidden=False,
                                dependency=[],
                                delay=100,
                            )
                        ),
                    },
                ),
                500,
            )

        assert mock_get_cached_outputs.call_count == 3


class Test_wait_for_export_result(TestCase):

    client = SdClient()
    session_id = "12a210fa-2804-11ef-b7a5-1bc3e7751d5d"

    @patch("shapediver.geometry_api_v2.client.ExportApi")
    def test_negative_delay(self, mock_ExportApi):
        res_compute = ResComputeExports(
            version="1",
            exports={
                "4c77e42cee6f1be8afacffd4806cfdc3": ResExportOrDefinition(
                    ResExport(
                        id="4c77e42cee6f1be8afacffd4806cfdc3",
                        version="3faf86a8467e83f0ac969bf03bece264",
                        name="some-name",
                        type=ResExportDefinitionType.DOWNLOAD,
                        hidden=False,
                        dependency=[],
                    )
                ),
            },
        )
        res = sd_utils._wait_for_export_result(
            self.client,
            self.session_id,
            ReqExport(
                parameters=ReqCustomization(),
                exports=["4c77e42cee6f1be8afacffd4806cfdc3"],
            ),
            res_compute,
            -1,
        )

        assert res is res_compute
        mock_ExportApi.get_cached_exports.assert_not_called()

    @patch("shapediver.geometry_api_v2.client.ExportApi.get_cached_exports")
    def test_positive_delay_and_no_timeout(self, mock_get_cached_exports):
        res_cache = ResGetCachedExports(
            version="1",
            exports={
                "4c77e42cee6f1be8afacffd4806cfdc3": ResExportOrDefinition(
                    ResExport(
                        id="4c77e42cee6f1be8afacffd4806cfdc3",
                        version="3faf86a8467e83f0ac969bf03bece264",
                        name="some-name",
                        type=ResExportDefinitionType.DOWNLOAD,
                        hidden=False,
                        dependency=[],
                    )
                ),
            },
        )

        # Mock
        mock_get_cached_exports.return_value = res_cache

        res = sd_utils._wait_for_export_result(
            self.client,
            self.session_id,
            ReqExport(
                parameters=ReqCustomization(),
                exports=["4c77e42cee6f1be8afacffd4806cfdc3"],
            ),
            ResComputeExports(
                version="1",
                exports={
                    "4c77e42cee6f1be8afacffd4806cfdc3": ResExportOrDefinition(
                        ResExport(
                            id="4c77e42cee6f1be8afacffd4806cfdc3",
                            version="3faf86a8467e83f0ac969bf03bece264",
                            name="some-name",
                            type=ResExportDefinitionType.DOWNLOAD,
                            hidden=False,
                            dependency=[],
                            delay=100,
                        )
                    ),
                },
            ),
            123.4,
        )

        assert res is res_cache
        mock_get_cached_exports.assert_called_once()

    @patch("shapediver.geometry_api_v2.client.ExportApi.get_cached_exports")
    def test_positive_delay_and_timeout(self, mock_get_cached_exports):
        res_cache = ResGetCachedExports(
            version="1",
            exports={
                "4c77e42cee6f1be8afacffd4806cfdc3": ResExportOrDefinition(
                    ResExport(
                        id="4c77e42cee6f1be8afacffd4806cfdc3",
                        version="3faf86a8467e83f0ac969bf03bece264",
                        name="some-name",
                        type=ResExportDefinitionType.DOWNLOAD,
                        hidden=False,
                        dependency=[],
                        delay=250,
                    )
                ),
            },
        )

        # Mock
        mock_get_cached_exports.return_value = res_cache

        with self.assertRaises(ApiException):
            sd_utils._wait_for_export_result(
                self.client,
                self.session_id,
                ReqExport(
                    parameters=ReqCustomization(),
                    exports=["4c77e42cee6f1be8afacffd4806cfdc3"],
                ),
                ResComputeExports(
                    version="1",
                    exports={
                        "4c77e42cee6f1be8afacffd4806cfdc3": ResExportOrDefinition(
                            ResExport(
                                id="4c77e42cee6f1be8afacffd4806cfdc3",
                                version="3faf86a8467e83f0ac969bf03bece264",
                                name="some-name",
                                type=ResExportDefinitionType.DOWNLOAD,
                                hidden=False,
                                dependency=[],
                                delay=100,
                            )
                        ),
                    },
                ),
                500,
            )

        assert mock_get_cached_exports.call_count == 3


class Test_get_max_output_delay(TestCase):

    def test_no_outputs(self):
        res = sd_utils._get_max_output_delay(
            ResComputeOutputs(version="1", outputs=None)
        )
        assert res == -1

    def test_empty_outputs(self):
        res = sd_utils._get_max_output_delay(ResComputeOutputs(version="1", outputs={}))
        assert res == -1

    def test_mixed(self):
        res = sd_utils._get_max_output_delay(
            ResComputeOutputs(
                version="1",
                outputs={
                    "0ca411fecc995160971ed9d965acd218": ResOutputOrDefinition(
                        ResOutputDefinition(
                            id="0ca411fecc995160971ed9d965acd218",
                            name="some-name",
                            hidden=False,
                            dependency=[],
                        )
                    ),
                    "33c694f3a090a06560777870d3d1d317": ResOutputOrDefinition(
                        ResOutput(
                            id="33c694f3a090a06560777870d3d1d317",
                            version="0cb58bc66f41e5d02e7698041c61a267",
                            name="some-name",
                            hidden=False,
                            dependency=[],
                        )
                    ),
                    "6298d3d386252e6c0d2a0606fa17b470": ResOutputOrDefinition(
                        ResOutput(
                            id="6298d3d386252e6c0d2a0606fa17b470",
                            version="164b3792229712add59cb8c20ae896d0",
                            name="some-name",
                            hidden=False,
                            dependency=[],
                            delay=1000,
                        )
                    ),
                    "e82d5ea72507658f8d20d73d2e36e329": ResOutputOrDefinition(
                        ResOutput(
                            id="e82d5ea72507658f8d20d73d2e36e329",
                            version="20f19cbcecab95db84ef14be587d786b",
                            name="some-name",
                            hidden=False,
                            dependency=[],
                            delay=1001,
                        )
                    ),
                },
            )
        )
        assert res == 1001


class Test_get_max_export_delay(TestCase):

    def test_no_exports_no_outputs(self):
        res = sd_utils._get_max_export_delay(
            ReqExport(parameters=ReqCustomization(), exports=[]),
            ResComputeExports(version="1", exports=None, outputs=None),
        )
        assert res == -1

    def test_empty_exports_empty_outputs(self):
        res = sd_utils._get_max_export_delay(
            ReqExport(parameters=ReqCustomization(), exports=[]),
            ResComputeExports(version="1", exports={}, outputs={}),
        )
        assert res == -1

    def test_mixed_exports_and_outputs(self):
        res = sd_utils._get_max_export_delay(
            ReqExport(
                parameters=ReqCustomization(),
                exports=[
                    "df4a9c34b6c0cde97ca9ed4862c83d3d",
                    "4c77e42cee6f1be8afacffd4806cfdc3",
                    "81de396951f26b0c1aaeafe54c1711c3",
                    "2e18f3c4fa47270676af072d0ef3d7a6",
                ],
                outputs=[
                    "0ca411fecc995160971ed9d965acd218",
                    "33c694f3a090a06560777870d3d1d317",
                    "6298d3d386252e6c0d2a0606fa17b470",
                    "e82d5ea72507658f8d20d73d2e36e329",
                ],
            ),
            ResComputeExports(
                version="1",
                exports={
                    "df4a9c34b6c0cde97ca9ed4862c83d3d": ResExportOrDefinition(
                        ResExportDefinition(
                            id="df4a9c34b6c0cde97ca9ed4862c83d3d",
                            name="9ad04b1f9080be40d558bcb9bd8e82ab",
                            type=ResExportDefinitionType.DOWNLOAD,
                            hidden=False,
                            dependency=[],
                        )
                    ),
                    "4c77e42cee6f1be8afacffd4806cfdc3": ResExportOrDefinition(
                        ResExport(
                            id="4c77e42cee6f1be8afacffd4806cfdc3",
                            version="3faf86a8467e83f0ac969bf03bece264",
                            name="some-name",
                            type=ResExportDefinitionType.DOWNLOAD,
                            hidden=False,
                            dependency=[],
                        )
                    ),
                    "81de396951f26b0c1aaeafe54c1711c3": ResExportOrDefinition(
                        ResExport(
                            id="81de396951f26b0c1aaeafe54c1711c3",
                            version="8131411b9ab5ed20a3e277fa640136ef",
                            name="some-name",
                            type=ResExportDefinitionType.DOWNLOAD,
                            hidden=False,
                            dependency=[],
                            delay=998,
                        )
                    ),
                    "2e18f3c4fa47270676af072d0ef3d7a6": ResExportOrDefinition(
                        ResExport(
                            id="2e18f3c4fa47270676af072d0ef3d7a6",
                            version="f4c56df78c0851f9889c9ca44f3709dc",
                            name="some-name",
                            type=ResExportDefinitionType.DOWNLOAD,
                            hidden=False,
                            dependency=[],
                            delay=999,
                        )
                    ),
                },
                outputs={
                    "0ca411fecc995160971ed9d965acd218": ResOutputOrDefinition(
                        ResOutputDefinition(
                            id="0ca411fecc995160971ed9d965acd218",
                            name="some-name",
                            hidden=False,
                            dependency=[],
                        )
                    ),
                    "33c694f3a090a06560777870d3d1d317": ResOutputOrDefinition(
                        ResOutput(
                            id="33c694f3a090a06560777870d3d1d317",
                            version="some-version",
                            name="some-name",
                            hidden=False,
                            dependency=[],
                        )
                    ),
                    "6298d3d386252e6c0d2a0606fa17b470": ResOutputOrDefinition(
                        ResOutput(
                            id="6298d3d386252e6c0d2a0606fa17b470",
                            version="some-version",
                            name="some-name",
                            hidden=False,
                            dependency=[],
                            delay=1000,
                        )
                    ),
                    "e82d5ea72507658f8d20d73d2e36e329": ResOutputOrDefinition(
                        ResOutput(
                            id="e82d5ea72507658f8d20d73d2e36e329",
                            version="some-version",
                            name="some-name",
                            hidden=False,
                            dependency=[],
                            delay=1001,
                        )
                    ),
                },
            ),
        )
        assert res == 1001

    def test_ignore_non_requested_exports_and_outputs(self):
        res = sd_utils._get_max_export_delay(
            ReqExport(
                parameters=ReqCustomization(),
                exports=[
                    "df4a9c34b6c0cde97ca9ed4862c83d3d",
                ],
                outputs=[
                    "0ca411fecc995160971ed9d965acd218",
                ],
            ),
            ResComputeExports(
                version="1",
                exports={
                    "df4a9c34b6c0cde97ca9ed4862c83d3d": ResExportOrDefinition(
                        ResExportDefinition(
                            id="df4a9c34b6c0cde97ca9ed4862c83d3d",
                            name="9ad04b1f9080be40d558bcb9bd8e82ab",
                            type=ResExportDefinitionType.DOWNLOAD,
                            hidden=False,
                            dependency=[],
                        )
                    ),
                    "2e18f3c4fa47270676af072d0ef3d7a6": ResExportOrDefinition(
                        ResExport(
                            id="2e18f3c4fa47270676af072d0ef3d7a6",
                            version="f4c56df78c0851f9889c9ca44f3709dc",
                            name="some-name",
                            type=ResExportDefinitionType.DOWNLOAD,
                            hidden=False,
                            dependency=[],
                            delay=1000,
                        )
                    ),
                },
                outputs={
                    "0ca411fecc995160971ed9d965acd218": ResOutputOrDefinition(
                        ResOutputDefinition(
                            id="0ca411fecc995160971ed9d965acd218",
                            name="some-name",
                            hidden=False,
                            dependency=[],
                        )
                    ),
                    "e82d5ea72507658f8d20d73d2e36e329": ResOutputOrDefinition(
                        ResOutput(
                            id="e82d5ea72507658f8d20d73d2e36e329",
                            version="some-version",
                            name="some-name",
                            hidden=False,
                            dependency=[],
                            delay=1000,
                        )
                    ),
                },
            ),
        )
        assert res == -1
