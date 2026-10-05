"""Azure Functions app entry point (issue #37).

The Functions Python v2 programming model requires `function_app.py` at
the deployed app's root, exposing a module-level `app = func.FunctionApp()`
instance that the host discovers. The actual trigger/binding wiring (and
that `app` instance itself) live in `telemetry_pipeline/function_app.py` -
importable/testable independently of the Functions runtime, see that
module's docstring for why. This file just re-exports it so the deployed
package also satisfies the runtime's root-file discovery convention.
"""
from telemetry_pipeline.function_app import app  # noqa: F401
