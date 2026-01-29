======================
threedi-api-client
======================

.. image:: https://readthedocs.org/projects/threedi-api-client/badge/?version=latest
        :target: https://threedi-api-client.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

.. image:: https://img.shields.io/pypi/v/threedi-api-client.svg
        :target: https://pypi.python.org/pypi/threedi-api-client

.. image:: https://github.com/nens/threedi-api-client/actions/workflows/test.yml/badge.svg
        :target: https://github.com/nens/threedi-api-client/actions/workflows/test.yml


* A Python library for interfacing with the 3Di API
* Free software: BSD license
* Documentation: https://threedi-api-client.readthedocs.io

Features
--------

* Object-oriented API interaction generated with https://openapi-generator.tech/.
* Asynchronous support.
* Advanced file download and upload utility functions.


Installation
------------

We recommend `pip` to install this package::

    pip install --user threedi-api-client


If async support is required, install as follows::

    pip install --user threedi-api-client[aio]


Credits
-------

The OpenAPI client has been generated with OpenAPI generator (https://openapi-generator.tech/), which is
licensed under the Apache License 2.0.

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
