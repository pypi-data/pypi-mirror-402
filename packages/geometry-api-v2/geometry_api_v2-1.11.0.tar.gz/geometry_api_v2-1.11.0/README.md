<p align="center">
  <a href="https://www.shapediver.com/">
    <img src="https://sduse1-assets.shapediver.com/production/assets/img/navbar_logo.png" alt="ShapeDiver" width="392" />
  </a>
</p>

# GeometryBackendSdkPython

[ShapeDiver](https://www.shapediver.com/) is a cloud platform for building online applications
based on parametric 3D files made with [Rhinoceros 3D](https://www.rhino3d.com/) and
[Grasshopper](https://www.grasshopper3d.com/).

Using the **ShapeDiver Geometry Backend API** allows access to ShapeDiver models without using the
**ShapeDiver Viewer**. This SDK provides functionality to communicate with the Geometry Backend API
**version 2**, and includes type hints describing request and response data objects. See the
[API documentation](https://sdeuc1.eu-central-1.shapediver.com/api/v2/docs/) for more details.

## Authentication

The authentication system for the Geometry Backend API is based on **ticket objects** and **JWT
tokens**, which are handled by the [ShapeDiver Platform](https://www.shapediver.com/app/). You can
obtain **tickets** and **JWT tokens** by:

- using your account on the [ShapeDiver Platform](https://www.shapediver.com/app/) (tickets only),
  or

- you can obtain them programmatically using the [ShapeDiver Platform API](https://app.shapediver.com/api/documentation) (both tickets and JWT tokens).

An SDK for the [ShapeDiver Platform API](https://app.shapediver.com/api/documentation) will be
released soon.

When obtaining a ticket for your model from the ShapeDiver Platform, please be aware that you will
need a _ticket for backend access_, since you are accessing the Geometry Backend API from an
arbitrary client application that is not a web browser. For more details see the [ShapeDiver
Help Center developer settings](https://help.shapediver.com/doc/developers-settings).

## Base URL

The base URL to use depends on which ShapeDiver Geometry Backend System your model was uploaded to.
You can find the base URL in your model's dashboard on the ShapeDiver Platform, it is also called
the _model view url_.

## Usage - Ticket only

```python
from shapediver.geometry_api_v2 import SdClient, Configuration, SessionApi

def init_session():
    # Please see above on how to obtain a ticket
    ticket = "8b23fae66cf535719a9ec797e390208b2003e3cfc894b7624ada2f6894515f8836a4-66303337623538322d34386"

    # Initialize the SDK client instance by providing the base URL
    client = SdClient(Configuration("https://sdeuc1.eu-central-1.shapediver.com"))

    # Initialize a new session using the ticket.
    res = SessionApi(client).create_session_by_ticket(ticket)
    print(res)
```

## Usage - Ticket and JWT

It is possible to configure your ShapeDiver models such that JWT tokens are required to communicate
with them, which provides a strong authorisation mechanism. In this case you will need to use the
[ShapeDiver Platform API](https://app.shapediver.com/api/documentation) to obtain a JWT token for
your model on demand:

```python
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
```

## Examples

Examples on how to interact with available endpoints are given in the
[tests](https://github.com/shapediver/GeometryBackendSdkPython/tree/main/tests) folder.

## Making Changes & Contributing

Most of the code in this repository has been generated via the
[OpenAPI Generator](https://github.com/OpenAPITools/openapi-generator). The specification of the
Geometry Backend API version 2 can be found in the
[ShapeDiver OAS](https://github.com/shapediver/OpenApiSpecifications/blob/main/geometry_backend_v2.yaml)
repository. Additionally, we have added wrappers and utility functions to improve overall
usability.

### Prerequisites

This project is written in _Python 3_ and uses version **3.9.x**. For Unix systems, we recommend
[pyenv](https://github.com/pyenv/pyenv) to install and manage multiple Python versions. Once
installed, run the following commands:

```bash
pyenv install -v 3.9
pyenv global 3.9
```

Additionally, we use some tools for various tasks. We recommend
[pipx](https://github.com/pypa/pipx) to install Python applications in isolation. Once installed,
run the following commands:

```bash
pipx install pre-commit
pipx install twine
pipx install tox
pipx install pyscaffold
```

Project-specific commands are handled via [just](https://github.com/casey/just), so install this
tool as well. To get an overview of all available commands, run `just --list`.

### Setup

This project makes use of [virtual environments](https://docs.python.org/3/library/venv.html) to
manage Python packages. Run the following commands to create a new virtual environment (`.venv`)
and to install all dependencies:

```bash
just setup
source .venv/bin/activate
pre-commit install
```

It is a good idea to update the hooks to the latest version via `pre-commit autoupdate`.

## Generate Code

To re-generate the code from the
[ShapeDiver OAS](https://github.com/shapediver/OpenApiSpecifications/blob/main/geometry_backend_v2.yaml)
file, you need to install version 7 of the
[OpenAPI Generator](https://github.com/OpenAPITools/openapi-generator?tab=readme-ov-file#1---installation).
We recommend installing it as a global NPM package:

```bash
npm i -g openapi-generator
```

Afterwards, update the local file `./oas_spec.yaml` and generate the new code via
`just generate <version>`. The _version_ argument represents the respective Git tag from
[ShapeDiver OAS](https://github.com/shapediver/OpenApiSpecifications/tags). For instance, use
version "1.0.0" when targeting the Git tag "gb_v2@1.0.0".

Alternatively, the client can be generated from a local file. Check out the [ShapeDiver OAS
repository](https://github.com/shapediver/OpenApiSpecifications) and run `just generate local`.

## Release

To release new versions of this package, create the file `~/.pypirc` with the following content:

```txt
[distutils]
index-servers =
  pypi
  testpypi

[pypi]
repository = https://upload.pypi.org/legacy/
username = __token__
password = <token of main user>

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = <token of test user>
```

Afterwards, run `just release <version>` to build, publish, and commit a new version of the Python
package. The _version_ argument represents the new version of the package.

## Test

Unit and integration tests can be executed via `just test`. However, should you want to run only a
single test file then use `tox -- <path>` instead.

## Versioning

We take care to provide backwards compatibility for all older versions. However, new features might
be limited to newer API versions. Therefore, we recommend always using the newest API version out
there.

## Support

If you have questions, please use the [ShapeDiver Help Center](https://help.shapediver.com/).

You can find out more about ShapeDiver [right here](https://www.shapediver.com/).

## Licensing

This project is released under the [MIT
License](https://github.com/shapediver/GeometryBackendSdkPython/blob/main/LICENSE).

## Note

This project has been set up using _PyScaffold 4.5_. See [PyScaffold](https://pyscaffold.org/) for
details and additional information.
