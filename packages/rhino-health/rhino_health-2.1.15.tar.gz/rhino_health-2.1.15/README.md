# Rhino Health SDK

Programmatic interface for interacting with the **Rhino Health** Federated Learning Platform.

## Example Usage
Please see the sample notebook files provided to you by the Rhino Health Team for additional use cases.

### Create a session

```python
import rhino_health

my_username = "rhino_user@rhinohealth.com" # Replace me
my_password = "ASecurePasswordYouSet321" # Replace me
session = rhino_health.login(username=my_username, password=my_password)
```

There will be three ways to interact with the API after you have a session
1. Use defined endpoints under lib/endpoints for single actions
2. Use our library functions for commonly performed advanced features
3. Use our low level API Interface (advanced users)

### Interact with the API via defined endpoints

We've included convenience functions for our most commonly used endpoints in the library with required input and output
data classes. These can be found in `rhino_health/lib/endpoints`.

```python
my_projects = session.project.get_projects()
my_first_project = my_projects[0]
my_first_project.add_collaborator(collaborating_workgroup_uid)

my_dataset = session.dataset.get_dataset(my_dataset_uid)
dataset_project = my_dataset.project
my_dataset_info = my_dataset.dataset_info
```

### Library Functions

RhinoHealth also provides library functions which combine our basic building blocks to perform common actions.

Example:
```python
from rhino_health.lib.metrics import RocAucWithCI

metric_configuration = RocAucWithCI(y_true_variable="label", y_pred_variable="pred", confidence_interval=95, timeout_seconds=600)
"""
data_filters=[{
        "filter_column":"is_roc",
        "filter_value":1
    }]
"""
result = my_dataset.get_metric(metric_configuration)
print(f"{result.output}")
```

### Interact using the low level API

Please contact us for support with interacting with our low level API.

### Rate Limits
The Rhino SDK handles rate limits of the API for you if you use the same session between threads and will attempt to queue requests.
Excess requests will be sent with exponential backoff. If you send requests to our server from multiple locations
then you may run into exceptions.

## Development Notes

You may need to use `pip install -r requirements.txt --no-cache-dir` on M1 Macs


