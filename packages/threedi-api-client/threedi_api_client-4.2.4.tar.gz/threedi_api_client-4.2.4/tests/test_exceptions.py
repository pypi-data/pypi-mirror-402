def test_exception_identity():
    from threedi_api_client.openapi.exceptions import ApiException as SyncApiException
    from threedi_api_client.aio.openapi.exceptions import ApiException as AsyncApiException

    assert SyncApiException is AsyncApiException
