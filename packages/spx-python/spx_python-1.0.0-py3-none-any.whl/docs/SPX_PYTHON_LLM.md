# SPX_PYTHON_LLM.md

Functional usage guide for LLMs integrating spx-python in other projects.
This file is shipped with the pip package.

## What is spx-python
spx-python is a lightweight Python client for the SPX server REST API. It
exposes the SPX system as a dictionary-like tree of nodes (models, instances,
attributes, and methods).

## Quick start
```python
import os
import spx_python

base_url = os.getenv("SPX_BASE_URL", "http://localhost:8000")
product_key = os.getenv("SPX_PRODUCT_KEY")
if not product_key:
    raise RuntimeError("SPX_PRODUCT_KEY not set")

client = spx_python.init(address=base_url, product_key=product_key)
```

## Dictionary-style navigation
The client behaves like a mapping over the system tree:
- `client["models"]` is the model registry.
- `client["instances"]` is the instance registry.
- Each node returned is another `SpxClient`.

Example:
```python
models = client["models"]
instances = client["instances"]
```

## Create a model and an instance
```python
import uuid

model_key = f"TempSensor_{uuid.uuid4().hex[:8]}"
instance_key = f"sensor_{uuid.uuid4().hex[:8]}"

models = client["models"]
models[model_key] = {
    "attributes": {"temperature": 25.0, "heating_power": 0.0}
}

instances = client["instances"]
instances[instance_key] = model_key
sensor = instances[instance_key]
```

## Read and write attributes
Attributes are accessed under the `attributes` node and use `.internal_value`
for read/write.
```python
temp_attr = sensor["attributes"]["temperature"]
current = temp_attr.internal_value
temp_attr.internal_value = current + 5.0
```

If a node exposes configuration parameters as attributes, treat them the same
way (access via `attributes` and update `.internal_value`).

## Call methods on nodes
Any unknown attribute access becomes a method call on the server. Common
methods include `reset`, `start`, `stop`, `prepare`, and `run`.
```python
sensor.reset()
sensor.start()
sensor.stop()

client.prepare()
client.run()
```

## Path-based updates
You can update attributes via a relative path using `put_attr`:
```python
sensor.put_attr("attributes/temperature/internal_value", 42.0)
```

## Delete models and instances
```python
del instances[instance_key]
del models[model_key]
```

## Recommended helpers
Helpers live in `spx_python.helpers` and are safe to use in integrations and
tests. Use them instead of re-implementing retries or bootstrapping logic.

### Model and instance setup
- `load_model_definition(path)`: load YAML or JSON into a dict.
- `load_model(client, model_key, model_path)`: load from disk and register the model.
- `ensure_model(client, model_key, model_def)`: idempotent update; returns True if changed.
- `create_instance(client, model_name, ...)`: create instance with auto key and optional overrides.
- `ensure_instance(client, instance_key, model_key, ...)`: ensure or recreate, apply overrides, and start/reset.
- `bootstrap_model_instance(spx_python, ...)`: init client + load model + ensure instance in one call.

Example:
```python
from pathlib import Path
from spx_python.helpers import (
    load_model,
    create_instance,
    wait_for_attribute_value,
)

load_model(client, "TempSensor", Path("models/temp_sensor.yaml"))
instance = create_instance(
    client,
    "TempSensor",
    overrides={"attributes/temperature/internal_value": 22.0},
)
wait_for_attribute_value(instance, "attributes/temperature", 22.0, timeout=2.0)
```

### Wait/poll helpers
- `wait_seconds(duration, interval=0.2)`: sleep with short intervals.
- `wait_for_condition(predicate, timeout=5.0, interval=0.1)`: poll until True.
- `wait_for_attribute(instance, attr_path, predicate, ...)`: poll attribute path.
- `wait_for_attribute_value(instance, attr_path, expected, ...)`: value equals expected.
- `wait_for_state(instance, expected, ...)`: wait for instance state.

Example:
```python
from spx_python.helpers import wait_for_state

instance.start()
wait_for_state(instance, {"running", "RUNNING"}, timeout=5.0, interval=0.2)
```

### Logging and test helpers
- `spx_ensure_attribute(instance, attr_path, default)`: ensure a list attribute exists.
- `spx_append_attribute_value(instance, attr_path, entry)`: append to a list attribute.
- `spx_log_test_case(attr_path="test_logs")`: decorator for unittest cases.
- `SpxAssertionLoggingMixin`: mixin to log assertion outcomes.
- `SpxPytestLoggerPlugin`: pytest plugin with fixtures for logging.

Example:
```python
from spx_python.helpers import spx_ensure_attribute, spx_append_attribute_value

spx_ensure_attribute(instance, "test_logs", default=[])
spx_append_attribute_value(
    instance,
    "test_logs",
    {"kind": "note", "message": "setup complete"},
)
```

## Error handling
Errors raise `SpxApiError` (subclass of `requests.HTTPError`) with response and
fault details attached.
```python
from spx_python.client import SpxApiError

try:
    _ = client["instances"]["missing"]
except SpxApiError as exc:
    status = exc.response.status_code
    fault = exc.fault
```

## Testing patterns (pytest/unittest)
Integration tests should skip when `SPX_PRODUCT_KEY` is missing or the server
is unavailable.

### pytest
```python
import os
import pytest

PRODUCT_KEY = os.environ.get("SPX_PRODUCT_KEY")
if not PRODUCT_KEY:
    pytest.skip("SPX_PRODUCT_KEY not set", allow_module_level=True)
```

### unittest
```python
import os
import unittest
import spx_python

product_key = os.environ.get("SPX_PRODUCT_KEY")
if not product_key:
    raise unittest.SkipTest("SPX_PRODUCT_KEY not set")

try:
    client = spx_python.init(product_key=product_key)
except Exception as exc:
    raise unittest.SkipTest(f"Unable to init SPX client: {exc}") from exc
```

## Cleanup pattern
Always clean up models and instances created by tests.
```python
models = client["models"]
instances = client["instances"]
models["tmp_model"] = {"attributes": {"x": 1}}
instances["tmp_instance"] = "tmp_model"
try:
    ...
finally:
    try:
        del instances["tmp_instance"]
    except Exception:
        pass
    try:
        del models["tmp_model"]
    except Exception:
        pass
```
