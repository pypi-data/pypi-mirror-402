# Locker Secret Python SDK

<p align="center">
  <img src="https://cystack.net/images/logo-black.svg" alt="CyStack" width="50%"/>
</p>

 
---

The Locker Secret Python SDK provides convenient access to the Locker Secret API from applications written in the 
Python language. It includes a pre-defined set of classes for API resources that initialize themselves dynamically 
from API responses which makes it compatible with a wide range of versions of the Locker Secret API.


## The Developer - CyStack

The Locker Secret Python SDK is developed by CyStack, one of the leading cybersecurity companies in Vietnam. 
CyStack is a member of Vietnam Information Security Association (VNISA) and Vietnam Association of CyberSecurity 
Product Development. CyStack is a partner providing security solutions and services for many large domestic and 
international enterprises.

CyStack’s research has been featured at the world’s top security events such as BlackHat USA (USA), 
BlackHat Asia (Singapore), T2Fi (Finland), XCon - XFocus (China)... CyStack experts have been honored by global 
corporations such as Microsoft, Dell, Deloitte, D-link...


## Documentation

The documentation will be updated later.

## Requirements

- Python 3.6+

## Installation

Install from PyPip:

```
pip install --upgrade lockersm
```

Install from source with:

```
python setup.py install
```

## Usages


### Configuration access key

The SDK needs to be configured with your access key id and your secret access key, which is available in your 
Locker Secret Dashboard. These keys must not be disclosed. If you reveal these keys, you need to revoke 
them immediately. Environment variables are a good solution and they are easy to consume in most programming languages.

**Set up credentials on Linux/MacOS**
```
export ACCESS_KEY_ID=<YOUR_ACCESS_KEY_ID>
export SECRET_ACCESS_KEY=<YOUR_SECRET_ACCESS_KEY>
```

**Set up credentials on Windows**

Powershell
```
$Env:ACCESS_KEY_ID = '<YOUR_ACCESS_KEY_ID>'
$Env:SECRET_ACCESS_KEY = '<SECRET_ACCESS_KEY>'
```

Command Prompt
```
set ACCESS_KEY_ID=<YOUR_ACCESS_KEY_ID>
set SECRET_ACCESS_KEY=<YOUR_SECRET_ACCESS_KEY>
```

You also need to set `api_base` value (default is `https://api.locker.io/locker_secrets`).
If you need to set your custom headers, you also need to set `headers` value in the `options` param:

Now, you can use SDK to get or set values:
```
from locker import Locker

api_base = "your_base_api.host"
locker = Locker(
    api_base=api_base, 
    options={"headers": headers}
)
```

You can also pass parameters in the `Locker()` method or use the shared credential file (`~/.locker/credentials`), 
but we do not recommend these ways. 
```
locker = Locker(
    access_key_id=os.get_env("<YOUR_ACCESS_KEY_ID>"),
    secret_access_key=os.get_env("<YOUR_SECRET_ACCESS_KEY>"),
    api_base=api_base, 
    options={"headers": headers}
)
```


### List secrets

Use `.list()` to get all the secrets in your project. 

```
secrets = locker.list()
for secret in secrets:
    print(secret.id, secret.key, secret.value)
```

### Get a secret value
This func will get the secret value by a key. If the key does not exist, the SDK will return the default_value.

```
secret_value = locker.get("REDIS_CONNECTION", default_value="TheDefaultValue")
print(secret_value)
```

You could get a secret value by secret key and specific environment name by the `environment_name` parameter. 
If the key does not exist, the SDK will return the default_value.

```
secret_value = locker.get("REDIS_CONNECTION", environment_name="staging", default_value="TheDefaultValue")
print(secret_value)
```


### Retrieve a secret

Use `.retrieve()` function to retrieve the secret object.
```
secret = locker.retrieve("REDIS_CONNECTION", environment_name="staging")
print(secret)
print(secret.id, secret.key, secret.value)
```


### Create new secret

Use `.create()` function to create a new secret.

```
secret = locker.create(key="YOUR_NEW_SECRET_KEY", value="YOUR_NEW_SECRET_VALUE")
```

Create a new secret with a specific environment.

```
secret = locker.create(key="YOUR_NEW_SECRET_KEY", value="YOUR_NEW_SECRET_VALUE", environment_name="staging")
```

### Update a secret

Use `.modify()` function to update the value of the secret.

```
secret = locker.modify(key="YOUR_NEW_SECRET_KEY", value="UPDATED_SECRET_VALUE")
print(secret.key, secret.value, secret.environment_name)
```

Update a secret value by the secret key and the specific environment name.

```
secret = locker.modify(key="YOUR_NEW_SECRET_KEY", value="UPDATED_SECRET_VALUE", environment_name="staging")
print(secret.key, secret.value, secret.environment_name)
```


### List environments

Use `.list_environments()` to get all environments in your project.

```
environments = locker.list_environments()
for env in environments:
    print(env.name, env.external_url)
```

### Retrieve an environment

To retrieve an environment by name, use `.retrieve_environment()`.

Note:
You also use `.get_environment()` but this function will be deprecated in the future.

```
prod_env = locker.retrieve_environment("prod")
print(prod_env.name, prod_env.external_url)
```

### Create new environment

To create a new environment, use `.create_environment()`.

```
new_environment = locker.create_environment(name="staging", external_url="staging.host")
print(new_environment.name, new_environment.external_url)
```

### Update an environment

To update the `external_url` of the environment by name, use `.update_environment()`.

```
environment = locker.modify_environment(name="staging", external_url="new.staging.host")
```


### Error Handling

Locker Secret SDK offers some kinds of errors. They can reflect external events, like invalid credentials, network 
interruptions, or code problems, like invalid API calls.

If an immediate problem prevents a function from continuing, the SDK raises an exception. It’s a best practice to catch 
and handle exceptions. To catch an exception, use Python’s `try/except` syntax. Catch `locker.error.LockerError` or 
its subclasses to handle Locker-specific exceptions only. Each subclass represents a different kind of exception. 
When you catch an exception, you can use its class to choose a response.

Example:

```
from locker import Locker
from locker.error import LockerError


# Create new secret and handle error
try:
    new_secret = locker.create(key="GOOGLE_API", value="my_google_api", environment_name="staging")
    print(new_secret.key, new_secret.value, new_secret.description, new_secret.environment_name)
except LockerError as e:
    print(e.user_message)
    print(e.http_body)
    print(e.code)
    print(e.status_code)
```

In the SDK, error objects belong to `locker.error.LockerError` and its subclasses. Use the documentation for each class 
for advice about how to respond.

| Code              | Status code (HTTP Status code) | Name                    | Class                              | Description                                                                              | 
|-------------------|--------------------------------|-------------------------|------------------------------------|------------------------------------------------------------------------------------------|
| unauthorized      | 401                            | Authentication Error    | locker.error.AuthenticationError   | Invalid `access_client_id` or invalid `secret_access_key`                                |
| permission_denied | 403                            | Permission Denied Error | locker.error.PermissionDeniedError | Your credential does not have enough permission to execute this operation                |
| rate_limit        | 429                            | Rate Limit Error        | locker.error.RateLimitError        | Too many requests                                                                        |
| not_found         | 404                            | Resource Not Found      | locker.error.ResourceNotFoundError | The requested resource is not found                                                      |
| server_error      | 500                            | API Server Error        | locker.error.APIServerError        | Something went wrong on Locker’s end (These are rare)                                    |
| http_error        | 503                            | API Connect Error       | locker.error.APIConnectionError    | The request to API server error. Check your network connection                           |
| cli_error         | null                           | CLI Run Error           | locker.error.CliRunError           | The encryption/decryption binary runs error by invalid local data, process interruptions |
| locker_error      | null                           | General Locker Error    | locker.error.LockerError           | The general error                                                                        |



### Logging

The library can be configured to emit logging that will give you better insight into what it's doing. 
There are some levels: `debug`, `info`, `warning`, `error`.

The `info` logging level is usually most appropriate for production use, 
but `debug` is also available for more verbosity.

There are a few options for enabling it:

1. Set the environment variable `LOCKER_LOG` to the value `debug`, `info`, `warning` or `error`

```sh
$ export LOCKER_LOG=debug
```

2. Set `log` when initializing the Locker object:

```python
from locker import Locker

locker = Locker(log="debug")
```
or 
```python
from locker import Locker

locker = Locker()
locker.log = "debug"
```


## Examples

See the [examples' folder](/examples).

## Development

First install for development.
```
pip install -r requirements-dev.txt
```

### Run tests

Test by using tox. We test against the following versions.
- 3.6
- 3.7
- 3.8
- 3.9
- 3.10
- 3.11
- 3.12
- 3.13
- 3.14

To run all tests against all versions, use:
```
tox
```

Run all tests for a specific Python version:
```
tox -e py3.10
```

Run all tests in a single file:
```
tox -e py3.10 -- tests/test_util.py
```

## Troubleshooting

This section provides solutions to problems you might encounter when using the SDK. 

### Using with gunicorn

If the Locker object is declared at the same time as your gunicorn application and gunicorn's number of workers 
is greater than 1, you must use gunicorn's `--preload` parameter to load the application code before the worker process 
is forked.

```
gunicorn --preload -w 5 -b 0.0.0.0:8000 your_project.wsgi:application
```

<!--
### Using in multiple-thread

When using Locker in multi-threading, you should place the Locker declaration in a mutex lock to prevent 
race conditions

Example:

```
from threading import Lock

# create a lock
lock = Lock()
# acquire the lock
lock.acquire()
# Declare Locker object Here
locker = Locker(
    access_key_id=access_key_id, 
    secret_access_key=secret_access_key
)
locker.get(YOUR_SECRET_KEY)
# release the lock
lock.release()
```
-->

<!-- ### Upgrading the version -->



## Reporting security issues

We take the security and our users' trust very seriously. If you found a security issue in Locker SDK Python, please 
report the issue by contacting us at <contact@locker.io>. Do not file an issue on the tracker. 


## Contributing

Please check [CONTRIBUTING](CONTRIBUTING.md) before making a contribution.


## Help and media

- FAQ: https://support.locker.io

- Community Q&A: https://forum.locker.io

- News: https://locker.io/blog


## License
