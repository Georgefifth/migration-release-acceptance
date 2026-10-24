# Install into your project

Use the same Python 3.12+ test virtualenv that can import your application's
dependencies. Keep the application and its reviewed integration configuration in
your own repository. A source checkout is not needed when running the installed
project or offline-report commands.

The provisional distribution name is migration-release-acceptance, version 0.1.6.
It is not published on PyPI. Do not install a similarly named registry package.

## Obtain the wheel

Download the `.whl` file from a successful `package-contract` job's `dist/`
artifacts in this GitLab project. Keep the exact source commit and artifact SHA-256
with your CI configuration. The job's `reports/wheel-contract/verification.json`
records the tested wheel hash. This identifies the tested artifact; it is not a
package signature or evidence of a customer's installation.

Alternatively, build from a reviewed source checkout:

```sh
python3 -m pip wheel --no-deps --wheel-dir dist .
```

Only the acceptance package and bundled reference SQL are distributed. The
upstream FastAPI source, integration demos, local reports and credentials are not
part of the wheel. The wheel contains the project's MIT license and notices.

## Install in your application's test environment

From your own project, with its test virtualenv active:

```sh
python -m pip install /path/to/migration_release_acceptance-0.1.6-py3-none-any.whl
migration-accept --help
```

Installation also installs the declared PostgreSQL driver dependency. The first
installation needs access to your configured Python package index unless the
dependencies are already available locally. Application/framework dependencies
are your project's responsibility; they are not bundled into the tool.

Create a reviewed `project_acceptance.py` configuration as shown in
[the integration guide](application-integration.md). Run from the directory that
contains that module:

```sh
migration-accept --integration project_acceptance:integration --check
```

The command explicitly makes the invoking project directory importable for this
run and restores the prior import path afterward. Importing your named module and
calling its configuration function executes trusted Python code; the tool does
not automatically discover application behavior or sandbox imported modules.

With `DATABASE_URL` pointing to a disposable PostgreSQL test database and
`ACCEPTANCE_DISPOSABLE_DB=yes`:

```sh
migration-accept --integration project_acceptance:integration --candidate title-storage --output reports/acceptance
```

Replace title-storage with your declared candidate name. Exit 0 means
GO_WITHIN_SCOPE, 1 means BLOCK, and 2 means configuration/setup/INCONCLUSIVE.
The tool cleans its owned application processes and random schema; it does not
remove a database service supplied by your application/CI.

## Review saved evidence without a database

```sh
migration-report reports/acceptance/title-storage.json --output reports/review
```

Open the printed HTML path. Rendering preserves the saved verdict and does not
approve a release. Named candidates have individual reports; the guarded paired
comparison is limited to the matching breaking/expand reference candidates.

The short `python3 -m acceptance.trial` Docker demo remains a source-checkout
workflow. Installed users use their reviewed configuration and test database.
The public FastAPI integration also remains a source/CI example; installing this
wheel does not download or install that application.

## What the installation test establishes

`package-contract` builds a wheel, creates a fresh virtualenv, installs the wheel
non-editably, removes checkout-related Python environment overrides, and changes
to a separate generated project directory. It verifies:

- Console-script configuration loading from that directory.
- Preflight and offline rendering without database settings.
- Bundled SQL availability after installation.
- Real old/new HTTP subprocess imports from the installed package.
- A blocked rename (exit 1, eight failures) and compatible migration (exit 0,
  sixteen passing checks), including schema/application cleanup.
- An unreachable disposable database (exit 2/INCONCLUSIVE), failed-step context
  and bounded terminal guidance without a connection URL in the output.

The downstream app is the bundled synthetic reference app. This does not establish
independent team adoption, human setup time or compatibility with arbitrary apps.
It specifically checks installation behavior that running from the tool's own
source directory would fail to test.

Packaging uses standard [Python entry points](https://packaging.python.org/en/latest/specifications/entry-points/)
and [setuptools package data](https://setuptools.pypa.io/en/latest/userguide/datafiles.html).
