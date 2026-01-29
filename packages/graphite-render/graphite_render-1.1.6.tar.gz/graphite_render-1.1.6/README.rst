Graphite-Render
===============

**Note:** This is a maintained friendly fork of the upstream project at
https://github.com/brutasse/graphite-api.

Graphite-web, without the interface. Just the rendering HTTP API.

This is a minimalistic API server that replicates the behavior of
Graphite-web. I removed everything I could and simplified as much code as
possible while keeping the basic functionality.

Implemented API calls:

* ``/metrics/find``
* ``/metrics/expand``
* ``/render``

No-ops:

* ``/dashboard/find``
* ``/dashboard/load/<name>``
* ``/events/get_data``

Difference from graphite-web
----------------------------

* Stateless. No need for a database.
* No Pickle rendering.
* No remote rendering.
* JSON data in request bodies is supported, additionally to form data and
  querystring parameters.
* Ceres integration will be as an external backend.
* Compatibility with python 3.
* Easy to install and configure.

Goals
-----

* Solid codebase. Good test coverage.
* Ease of installation/use/configuration.
* Compatibility with the original Graphite-web API and 3rd-party dashboards.

Non-goals
---------

* Support for very old Python versions
* Built-in support for every metric storage system in the world. Whisper is
  included by default, other storages are added via 3rd-party backends.

Documentation
-------------

In the ``docs/`` directory.

Hacking
-------

`Tox`_ is used to run the tests for all supported environments. To get started
from a fresh clone of the repository:

.. code-block:: bash

    pip install tox
    tox

.. _Tox: https://testrun.org/tox/
