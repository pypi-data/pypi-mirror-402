.. These are examples of badges you might want to add to your README:
   please update the URLs accordingly

    .. image:: https://api.cirrus-ci.com/github/<USER>/geometry_api_v2.svg?branch=main
        :alt: Built Status
        :target: https://cirrus-ci.com/github/<USER>/geometry_api_v2
    .. image:: https://readthedocs.org/projects/geometry_api_v2/badge/?version=latest
        :alt: ReadTheDocs
        :target: https://geometry_api_v2.readthedocs.io/en/stable/
    .. image:: https://img.shields.io/coveralls/github/<USER>/geometry_api_v2/main.svg
        :alt: Coveralls
        :target: https://coveralls.io/r/<USER>/geometry_api_v2
    .. image:: https://img.shields.io/pypi/v/geometry_api_v2.svg
        :alt: PyPI-Server
        :target: https://pypi.org/project/geometry_api_v2/
    .. image:: https://img.shields.io/conda/vn/conda-forge/geometry_api_v2.svg
        :alt: Conda-Forge
        :target: https://anaconda.org/conda-forge/geometry_api_v2
    .. image:: https://pepy.tech/badge/geometry_api_v2/month
        :alt: Monthly Downloads
        :target: https://pepy.tech/project/geometry_api_v2
    .. image:: https://img.shields.io/twitter/url/http/shields.io.svg?style=social&label=Twitter
        :alt: Twitter
        :target: https://twitter.com/geometry_api_v2

.. image:: https://img.shields.io/badge/-PyScaffold-005CA0?logo=pyscaffold
    :alt: Project generated with PyScaffold
    :target: https://pyscaffold.org/

|

===============
geometry_api_v2
===============


    SDK to communicate with the ShapeDiver Geometry API version 2


`ShapeDiver <https://www.shapediver.com/>`_ is a cloud platform for building online applications
based on parametric 3D files made with `Rhinoceros 3D <https://www.rhino3d.com/>`_ and `Grasshopper
<https://www.grasshopper3d.com/>`_.

Using the **ShapeDiver Geometry Backend API** allows access to ShapeDiver models without using the
**ShapeDiver Viewer**. This SDK provides functionality to communicate with the Geometry Backend API
**version 2**, and includes type hints describing request and response data objects. See the
`API documentation <https://sdeuc1.eu-central-1.shapediver.com/api/v2/docs/>`_ for more details.


Authentication
==============

The authentication system for the Geometry Backend API is based on **ticket objects** and **JWT
tokens**, which are handled by the `ShapeDiver Platform <https://www.shapediver.com/app/>`_. You can
obtain **tickets** and **JWT tokens** by:

- using your account on the `ShapeDiver Platform <https://www.shapediver.com/app/>`_ (tickets only),
  or

- you can obtain them programmatically using the `ShapeDiver Platform API
  <https://app.shapediver.com/api/documentation>`_ (both tickets and JWT tokens).

An SDK for the `ShapeDiver Platform API <https://app.shapediver.com/api/documentation>`_ will be
released soon.

When obtaining a ticket for your model from the ShapeDiver Platform, please be aware that you will
need a *ticket for backend access*, since you are accessing the Geometry Backend API from an
arbitrary client application that is not a web browser. For more details see the `ShapeDiver
Help Center developer settings <https://help.shapediver.com/doc/developers-settings>`_


Base URL
========

The base URL to use depends on which ShapeDiver Geometry Backend System your model was uploaded to.
You can find the base URL in your model's dashboard on the ShapeDiver Platform, it is also called
the *model view url*.


Usage - Ticket only
===================
::

    from shapediver.geometry_api_v2 import SdClient, Configuration, SessionApi

    def init_session():
        # Please see above on how to obtain a ticket
        ticket = "8b23fae66cf535719a9ec797e390208b2003e3cfc894b7624ada2f6894515f8836a4-66303337623538322d34386"

        # Initialize the SDK client instance by providing the base URL
        client = SdClient(Configuration("https://sdeuc1.eu-central-1.shapediver.com"))

        # Initialize a new session using the ticket.
        res = SessionApi(client).create_session_by_ticket(ticket)
        print(res)


Usage - Ticket and JWT
======================

It is possible to configure your ShapeDiver models such that JWT tokens are required to communicate
with them, which provides a strong authorisation mechanism.
In this case you will need to use the `ShapeDiver Platform API
<https://app.shapediver.com/api/documentation>`_ to obtain a JWT token for your model on demand.::

    from shapediver.geometry_api_v2 import SdClient, Configuration, SessionApi

    def init_session():
        # Please see above on how to obtain a ticket and a JWT
        jwt = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6Ikp1c3QgYSB0ZXN0IiwiaWF0IjoxNjE4OTExMjcxLCJleHAiOjE2MTg5MTQ4OTcsImp0aSI6IjYzMjA3ODE3LWJiNWQtNDY3Zi04NzRkLWM4N2EyYzAxYmZlZCJ9.S5Ps_Fx5p6aJxdBOJMBKgpf2SIlp--6kkIZU55tiqEg"
        ticket = "8b23fae66cf535719a9ec797e390208b2003e3cfc894b7624ada2f6894515f8836a4-66303337623538322d34386"

        # Initialize the SDK client instance by providing the base URL
        client = SdClient(
            Configuration("https://sdeuc1.eu-central-1.shapediver.com", access_token=jwt)
        )

        # Initialize a new session using the ticket.
        res = SessionApi(client).create_session_by_ticket(ticket)
        print(res)


Examples
========

Examples on how to interact with available endpoints are given in the `tests
<https://github.com/shapediver/GeometryBackendSdkPython/tree/main/tests>`_ folder.

Versioning
==========

We take care to provide backwards compatibility for all older versions. However, new features might
be limited to newer API versions. Therefore, we recommend always using the newest API version out
there.

Support
=======

If you have questions, please use the `ShapeDiver Help Center <https://help.shapediver.com/>`_.

You can find out more about ShapeDiver `right here <https://www.shapediver.com/>`_.


Licensing
=========

This project is released under the `MIT License
<https://github.com/shapediver/GeometryBackendSdkPython/blob/main/LICENSE>`_.
