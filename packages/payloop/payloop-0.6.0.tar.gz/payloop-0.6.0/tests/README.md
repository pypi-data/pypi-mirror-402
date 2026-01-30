# Payloop Python SDK Tests

This directory contains both tests for the Python SDK code, and integration tests.

The integration tests make real LLM calls.  They rely on environment variables to be set.

**Integration tests are skipped by default.**

## Running Tests

To run all tests **except** integration tests, just run:

    pytest

To include integration tests, you must run:

    pytest --integration

This will include integration tests in those that are collected and run.

Without `--integration`, all tests using `@pytest.mark.integration` will be skipped by default.

**The integration tests will run against the staging environment by default.**

To run the integration tests against the local environment, use:

    pytest --integration --environment=local

## Using the Payloop SDK Locally

To use the Payloop Python SDK that's sitting in your local directory, run:

    pip install -e ~/src/payloop/python-sdk

...or similar.  This will allow your `payloop` module to use the contents of your local directory,
rather than a pip-managed version elsewhere on disk.

## Integration Tests

### Integration Test-specific Dependencies

These integration test scripts assume they're running using Python LLM SDK versions.

The `tests/clients/requirements-integration-tests.txt` file contains the dependencies required to run the integration tests.

When you want to run the integration tests, you must install these dependencies (in a virtual environment, if needed):

    pip install -r tests/clients/requirements-integration-tests.txt

Keep `requirements-integration-tests.txt` up-to-date as needed.

### Environment Variables

The integration tests make actual LLM SDK calls.

Therefore, they are dependent on these environment variables:

* `ANTHROPIC_API_KEY`
* `AWS_BEDROCK_ACCESS_TOKEN`
* `GOOGLE_APPLICATION_CREDENTIALS`
* `OPENAI_API_KEY`
* `PAYLOOP_API_KEY`

If any required environment variables are not set, test(s) should fail with clear error messages indicating the reason.

If you want to test any or all LLM-dependent integration tests, you must set the corresponding environment variables.

### Set `PAYLOOP_API_KEY`

You must have the `PAYLOOP_API_KEY` environment variable set to a valid API key from the environment you are testing against!

We don't want to hardcode API key values in our tests.

Create an API key (if needed), and set the `PAYLOOP_API_KEY` environment variable to it.

### Running a Single Integration Test

Do you want to run only a single integration test?  Here's an example:

    # Be in your tests directory first!
    # This allows the conftest.py file to be loaded.

    ((venv) ) brian:~/src/payloop/python-sdk/tests (pay-126-move-integration-tests-to-pytest)$ pwd
    /Users/brian/src/payloop/python-sdk/tests


    ((venv) ) brian:~/src/payloop/python-sdk/tests (pay-126-move-integration-tests-to-pytest)$ pytest --integration --environment=local clients/openai/test_openai_sync.py
    ===================================================================================================== test session starts =====================================================================================================
    platform darwin -- Python 3.12.10, pytest-8.4.2, pluggy-1.6.0
    rootdir: /Users/brian/src/payloop/python-sdk
    configfile: pyproject.toml
    plugins: anyio-4.12.1, logfire-4.18.0, langsmith-0.6.1, asyncio-0.26.0
    asyncio: mode=Mode.STRICT, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
    collected 1 item

    clients/openai/test_openai_sync.py .                                                                                                                                                                                    [100%]

    ====================================================================================================== 1 passed in 1.86s ======================================================================================================

### Adding a New Integration Test

When adding a new integration test, mark it with:

    @pytest.mark.integration

This will ensure that the integration test is skipped by default.

It can then only be run when using `pytest --integration`.

### Running Integration Tests Locally

If you are actively changing the Payloop backend and/or Python SDK code, you may want to run integration tests locally.

To do so, you must have the following services running first:

* Payloop `backend` API (typically on `localhost:8080`)
* Payloop `ai` API (typically on `localhost:8001`)

In the `ai` repo, you may have to edit `app/bin/run-local-server.sh` for it to run on port `8001`.

Our AI developers typically don't run the `backend` API locally, and they both use port `8000` by default.

# How is Pytest Configured?

See `tests/conftest.py`.

This adds support for the `--integration` command-line flag.

It also adds support for the `--environment` flag, and defaults it to `staging`.

`tests/clients/conftest.py` contains an `integration_environment` fixture, which
enforces that required environment variables are set.

If any prerequisite environment variables are not set, tests will fail with a clear reason describing the problem.
