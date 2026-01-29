Usage
=====

The ``threedi_api_client.ThreediApi`` is the main entry point to make calls
to the 3Di API. It handles the login process for you and can be
directly used as client for all API endpoints.

In earlier versions of this library the main entry point was
``threedi_api_client.ThreediApiClient``. This method will remain available until
``threedi_api_client`` version 4.0. Read below how to migrate from ``ThreediApiClient``
to ``ThreediApi``.


.. autoclass:: threedi_api_client.ThreediApi


Migration from ThreediApiClient
-------------------------------

Formerly, the ``threedi_api_client.ThreediApiClient`` was used to interact with
the 3Di API. As of ``threedi_api_client`` version 4, this method is deprecated.
Currently, both methods are allowed, but the legacy one will give warnings.

There are three changes:

1. The ``ThreediApi`` object directly exposes methods to interact with 3Di API resources.
   There is no need of separately constructing `api` objects for each resource. The root package
   ``openapi_client`` will disappear in future versions: do not import it anymore. Direct
   access to the (new) generated API code is possible through ``threedi_api_client.openapi``.
2. The configuration variables are now prefixed with ``"THREEDI_API_"`` instead of ``"API_"``.
3. The ``"THREEDI_API_HOST"`` must not include the version.
4. Advanced users of the asynchronous client (imported from ``threedi_api_client.aio``) should
   start using ``threedi_api_client.ThreediApi`` with ``asynchronous=True``.

Take for example a script that looks like this:

.. code:: python

    from threedi_api_client import ThreediApiClient
    from openapi_client import SimulationsApi

    config = {
        "API_HOST": "https://api.3di.live/v3.0"
        "API_USERNAME": "your.username"
        "API_PASSWORD": "your.password"
    }

    with ThreediApiClient(config=config) as api_client:
        api = SimulationsApi(api_client)
        result = api.simulations_list()


Applying the changes listed above, it is refactored to this:

.. code:: python

    from threedi_api_client import ThreediApi

    config = {
        "THREEDI_API_HOST": "https://api.3di.live",  # no version!
        "THREEDI_API_PERSONAL_API_TOKEN": "your_personal_api_token_here"
    }

    with ThreediApi(config=config) as api:
        result = api.simulations_list()
