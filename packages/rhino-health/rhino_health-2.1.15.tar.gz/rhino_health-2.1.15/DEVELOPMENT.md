## Installing development dependencies
```shell
python3.13 -m venv --upgrade-deps .venv
. .venv/bin/activate
# Workaround for weird issue with pip building wheels with Python 3.13 on Mac.
[[ "$OSTYPE" == "darwin"* ]] && export PIP_NO_CACHE_DIR=1
pip install -r requirements.txt
```

## Updating dependencies
```shell
python3.13 -m venv --upgrade-deps .venv
. .venv/bin/activate
# Workaround for weird issue with pip building wheels with Python 3.13 on Mac.
[[ "$OSTYPE" == "darwin"* ]] && export PIP_NO_CACHE_DIR=1
pip install -e ".[dev,test,lint,kaplan-meier]"
pip freeze > requirements.txt
```

## Pre Deployment/Merge Checklist
1) Make sure to update the `__version__` variable in
   [`rhino_health/__init__.py`](rhino_health/__init__.py) if you wish to
   publish a new version, so the documentation refers to the correct version.
2) Make sure to test the interation tests against the branch. If you are adding
   new endpoints, please write new integration tests in the cloud repository.
   You can go to the cloud repository and kick off an integration test against
   a specific SDK branch.
3) Once merged, the documentation should be auto generated and updated. If any
   issues occur, please ask the developers.

## Unit Test Fixture Generation
1) Copy a result from swagger for the endpoint in question.
2) Replace the UIDs with something more friendly or update the test to
   reference the new uid.

## Hidden Fields
Running `make test` will run the SDK tests with extra field forbidden
enforcement. This is a great way to automatically detect which new API fields
are missing and need to be added to the SDK.

If there is a field that you purposely do not want to surface to users, you can
add it to the `__hidden__: List[str]` class attribute on the `RhinoBaseModel`.

## Test with tox
Tox tests our code in different environments: with different combinations of 
supported versions of Python and libraries we depend on.
To run the tests:
1) make sure your virtual env is activated, run ```source .venv/bin/activate```
2) run  ```tox``` to run tests in all the environment.
   This will take some time since there are many combinations -> many environments to build
3) run  ```tox -e py39``` to run all the python 3.9 combinations
4) to test a specific environment, for example in the case your tests failed in ci,
   check the failure log and find the environment, in this case it is python3.9, requests2.28,
   funcy1.18 and pydantic2.5
   run ```tox -e py39-requests2.28-funcy1.18-pydantic2.5``` 
