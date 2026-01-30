python-rundeck
===============
![PyPI Version](https://img.shields.io/pypi/v/python-rundeck)
![Python Versions](https://img.shields.io/pypi/pyversions/python-rundeck)
![License](https://img.shields.io/pypi/l/python-rundeck)
![Downloads](https://static.pepy.tech/badge/python-rundeck)

Python client for the Rundeck API (v14-v56), inspired by the python-gitlab architecture. Provides typed managers for key resources (projects, jobs, executions, tokens, users, system, configuration) and SCM (import/export).

Contents
--------
- Installation
- Quick start
- Configuration
- Available resources
- Return types policy
- Examples by resource
- Error handling
- Development and testing

Installation
------------
Prerequisites: Python 3.11+. Install from PyPI.

```bash
pip install python-rundeck
```

Quick start
-----------
```python
from rundeck.client import Rundeck

rd = Rundeck(url="https://rundeck.example.com", token="MY_TOKEN", api_version=56)
# Password auth (session cookie) if no token
rd = Rundeck(url="https://rundeck.example.com", username="admin", password="admin", api_version=56)

# List projects
projects = rd.projects.list()
for p in projects:
    print(p.name)

# Get a project and run a job
project = rd.projects.get("demo")
jobs = project.jobs.list()
# Use as_execution=True to receive an Execution object.
execu = jobs[0].run(as_execution=True)
print(execu.id)
```

Configuration
-------------
Configuration follows a cascading model (args > env > files > defaults) via `RundeckConfig`.

Main parameters:
- `url`: Rundeck URL (e.g. `https://rundeck.example.com`)
- `token`: API token (header `X-Rundeck-Auth-Token`)
- `username` / `password`: Session authentication (j_security_check) if no token is provided.
- `api_version`: API version (e.g. `56`)
- `timeout`: Request timeout (float, seconds)
- `ssl_verify`: TLS verification (bool or CA path)

Config files: if needed, pass `config_files` or `Rundeck.from_config(config_section=...)`.
Useful env vars (client config):
- `RUNDECK_URL`: Base URL
- `RUNDECK_TOKEN`: API token (header `X-Rundeck-Auth-Token`)
- `RUNDECK_USERNAME` / `RUNDECK_PASSWORD`: Session auth (if no token)
- `RUNDECK_API_VERSION`: API version (e.g. 56)
- `RUNDECK_TIMEOUT`: Request timeout (seconds)
- `RUNDECK_SSL_VERIFY`: TLS verification (bool or CA path)
- `RUNDECK_USER_AGENT`: HTTP User-Agent

Available resources
-------------------
- `projects` (`ProjectManager`): CRUD projects, job export/import, project config, archive (export/import).
- `jobs` (`JobManager`): list, get, deletions, bulk actions, execution.
- `executions` (`ExecutionManager`): list/filter, running, get/delete, advanced query.
- `tokens` (`TokenManager`): list, get, create, delete.
- `users` (`UserManager`): user operations (per current implementation).
- `metrics` (`MetricsManager`): `/metrics` endpoints (list/data/healthcheck/ping).
- `plugins` (`PluginManager`): list installed plugins (`/plugin/list`).
- `webhooks` (`WebhookEventManager` + `ProjectWebhookManager`): project webhook management and sending via token.
- `key_storage` (`StorageKeyManager`): key storage management `/storage/keys`.
- `adhoc` (`AdhocManager`, via `project.adhoc`): run AdHoc commands/scripts.
- `system` (`SystemManager`): system info, executions enable/disable, logstorage, ACL.
- `config_management` (`ConfigManagementManager`): global configuration `/config`.
- `scm` (via `project.scm` and `job.scm`): import/export plugins, setup, enable/disable, status, actions (commit/import/export...).

Return types policy
-------------------
- Resource managers use `list/get/create/update` to return objects (`RundeckObject`).
- Factory managers return the created resource object for actions that create it
  (e.g., `project.adhoc` returns `Execution`).
- Utility managers return raw API responses (dict/str/bytes).
- `delete(...)` returns `None`.
- Object methods return raw API responses and update the object in place when needed.
- Explicit flags are used when an object return is requested (e.g., `as_execution=True`).

Resource managers:
- `projects`, `jobs`, `executions`, `tokens`, `users`, `plugins`, `features`, `key_storage`, `system.acl`, `project.webhooks`.

Factory managers:
- `adhoc` (via `project.adhoc`).
  Returns `Execution` objects (execution factory).

Utility managers:
- `system`, `config_management`, `metrics`, `scheduler`, `webhooks` (event send).
- `scm` (via `project.scm` and `job.scm`), and project sub-managers like
  `project.config`, `project.resources`, `project.sources`, `project.readme`,
  `project.archive`, `project.acl`.

Note: `project.webhooks.create(...)` returns the raw API response (e.g., `{"msg": "Saved webhook"}`)
because the Rundeck API does not return the created webhook object.

Example:
```python
job = rd.jobs.get("job-id")          # -> Job (object)
resp = job.run()                     # -> dict (raw API response)
execu = job.run(as_execution=True)   # -> Execution (object)
execution.refresh()                  # updates in place, returns None
```

Examples by resource (complete)
-------------------------------
Projects
```python
# CRUD project
p = rd.projects.create("demo")
p = rd.projects.get("demo")
rd.projects.delete("demo")
projects = rd.projects.list()

# Export / import jobs from a project (via job manager)
project.jobs.export(format="json", idlist="id1,id2", groupPath="group/sub")
project.jobs.import_jobs(content=open("jobs.json").read(), format="json", dupeOption="update", uuidOption="remove")

# Project export / import (ZIP archive)
archive = project.archive
resp = archive.export(export_all=False, export_webhooks=True)  # Raw response (zip)
token_info = archive.export_async(exportAll=True)
status = archive.export_status(token_info.get("token", ""))
zip_resp = archive.export_download(token_info.get("token", ""))

# Archive import (sync or async)
archive.import_archive(
    content=open("project-export.zip", "rb").read(),
    jobUuidOption="preserve",
    importExecutions=True,
    importConfig=True,
)
archive.import_archive(content=open("project-export.zip", "rb").read(), async_import=True)
archive.import_status()

# Project README / MOTD
project.readme.get_readme()  # default text
project.readme.get_readme(accept="application/json")
project.readme.update_readme("New content", content_type="text/plain")
project.readme.delete_readme()
project.readme.get_motd()
project.readme.update_motd("Message of the day", content_type="text/plain")
project.readme.delete_motd()

# Project config (key/value)
conf = p.config.get()
p.config.keys.get("project.label")
p.config.keys.set("project.label", "Demo")
p.config.keys.update({"project.description": "Sample"})
p.config.replace({"project.label": "Demo", "project.description": "Sample"})
p.config.keys.delete("project.label")

# SCM import/export (on a project)
scm_import = project.scm.import_  # or getattr(project.scm, "import")
scm_export = project.scm.export

# Plugin discovery
scm_import.plugins.list()
scm_export.plugins.list()

# Input fields for a plugin and setup (explicit plugin_type)
fields = scm_import.plugins.input_fields("git-import")
scm_import.config.setup("git-import", {"url": "ssh://git@example.com/repo.git", "dir": "/tmp/repo"})

# Enable/disable a plugin
scm_import.config.enable("git-import")
scm_export.config.disable("custom-export")

# SCM status/config
import_status = scm_import.actions.status()
export_conf = scm_export.config.get()

# Project-side SCM actions (e.g., commit/pull/push depending on plugin)
action_fields = scm_export.actions.input_fields("commit")
scm_export.actions.perform(
    "commit",
    input_values={"message": "Sync jobs"},
    jobs=["job-1"],
    items=["path/job-1.yaml"],
    deleted=["obsolete/path.yaml"],
)
```

Jobs
```python
# List jobs for a project
jobs = rd.jobs.list(project="demo", groupPath="ops")

# From a parent project
project = rd.projects.get("demo")
jobs = project.jobs.list()

# Direct access to a job
job = rd.jobs.get("job-id")
job.delete()
job.definition(format="yaml")
job.retry("exec-id", argString="-opt val")
job.enable_execution()
job.disable_execution()
job.enable_schedule()
job.disable_schedule()
info = job.info()
meta = job.meta(meta="name,description")
tags = job.tags()
workflow = job.workflow()
forecast = job.forecast(time="2024-05-01T10:00:00Z", max=5)

# Export/import jobs via manager (project parameter or parent)
rd.jobs.export(project="demo", format="xml", idlist="id1,id2", groupPath="group")
rd.jobs.import_jobs(
    project="demo",
    content=open("jobs.xml", "rb").read(),
    fileformat="xml",
    dupeOption="update",
)
# Or via a parent project
project.jobs.export(format="json")
project.jobs.import_jobs(content=open("jobs.json", "rb").read(), fileformat="json")

Note: import remains exposed as `import_jobs(...)` (the Python keyword prevents a direct call to `.import`). If you prefer the alias, use `getattr(rd.jobs, "import")(...)`.

# Run and get the execution
execution = job.run(as_execution=True, argString="-option value")

# Bulk actions
rd.jobs.bulk.enable_execution(["id1", "id2"])
rd.jobs.bulk.disable_execution(["id1", "id2"])
rd.jobs.bulk.delete(["id1", "id2"])
rd.jobs.bulk.enable_schedule(["id1", "id2"])
rd.jobs.bulk.disable_schedule(["id1", "id2"])

# Upload option files and uploaded files
job.upload_option_file("csvfile", open("data.csv", "rb").read(), file_name="data.csv")
job.list_uploaded_files(max=20)
rd.jobs.get_uploaded_file_info("file-id")

# SCM import/export on a job
job_scm_export = job.scm.export
job_scm_import = job.scm.import_  # or getattr(job.scm, "import")

job_scm_export.status()
job_scm_export.diff()
job_scm_export.perform("commit", input_values={"message": "Sync job"})

job_scm_import.status()
job_scm_import.input_fields("pull")
job_scm_import.perform("pull", input_values={"message": "Update from repo"})

# Project resources
resources = project.resources.list(format="json", groupPath="ops")
node = project.resources.get("node1")
sources = project.sources.list()
source_details = project.sources.get(1)
project.sources.list_resources(1, accept="application/json")
project.sources.update_resources(1, content="{}", content_type="application/json")
project.acl.list()
project.acl.get("policy.aclpolicy")
project.acl.create("policy.aclpolicy", content="...yaml...")
project.acl.update("policy.aclpolicy", content="...yaml...")
project.acl.delete("policy.aclpolicy")
```

Executions
```python
# Simple or paginated list
execs = rd.executions.list(project="demo", status="running", max=50, offset=0)
running = rd.executions.running(project="demo")  # or "*" for all

# Details / deletion
e = rd.executions.get("123")
rd.executions.delete("123")
rd.executions.bulk_delete(["123", "124"])

# Advanced query
advanced = rd.executions.query(
    project="demo",
    statusFilter="failed",
    userFilter="alice",
    jobIdListFilter=["id1", "id2"],
    groupPath="ops",
    max=100,
)

# Execution methods
e.abort(asUser="admin")
output = e.get_output(offset=0, maxlines=100)
state = e.get_state()
is_running = e.is_running()
e.refresh()  # reload data
```

Tokens
```python
tokens = rd.tokens.list()
user_tokens = rd.tokens.list(user="alice")
t = rd.tokens.get("tok-1")
new_token = rd.tokens.create(user="alice", roles=["admin"], duration="90d", name="cli")
rd.tokens.delete(new_token.id)
```

Users
```python
users = rd.users.list()
me = rd.users.get_current()
u = rd.users.get("bob")
roles = rd.users.current_roles()

# Update via manager or object
u = rd.users.update("bob", firstName="Bob", lastName="Builder", email="bob@example.com")
u.roles()            # via the object
u.update(email="new@example.com")  # updates and refreshes the object
```

System
```python
system = rd.system
info = system.info()

# Log storage
system.logstorage.info()
system.logstorage.incomplete(max=50, offset=0)
system.logstorage.incomplete_resume()

# Execution mode (sub-manager)
system.executions.enable()
system.executions.disable()
system.executions.status()

# ACL
system.acl.list()
system.acl.get("policy.aclpolicy")
system.acl.create("policy.aclpolicy", content="...yaml...")
system.acl.update("policy.aclpolicy", content="...yaml...")
system.acl.delete("policy.aclpolicy")

# Scheduler takeover (cluster)
rd.scheduler.takeover(all_servers=True)
rd.scheduler.takeover(server_uuid="uuid-123", project="demo", job_id="job-1")
```

Metrics
```python
metrics = rd.metrics
metrics.list()
metrics.data()
metrics.healthcheck()
metrics.ping()

# Installed plugins
plugins = rd.plugins.list()
for plugin in plugins:
    print(plugin.name, plugin.service)

# Plugin details
first = plugins[0]
detail = rd.plugins.detail(first.service, first.name)

# Project webhooks and send
project = rd.projects.get("demo")
wh = project.webhooks
wh.create(
    project=project.id,
    name="hook1",
    user="admin",
    roles="admin",
    eventPlugin="log-webhook-event",
    config={},
    enabled=True,
)
hooks = wh.list()
first_hook = hooks[0]
wh.update(first_hook.id, name="hook1-updated")
rd.webhooks.send(first_hook.authToken, json={"hello": "world"})
wh.delete(first_hook.id)

# Key storage (/storage/keys)
ks = rd.key_storage
# Create a secret (password)
ks.create("integration/secret1", content="s3cr3t", content_type="application/x-rundeck-data-password")
resources = ks.list()  # root listing
meta = ks.get("integration/secret1")
content = meta.content()  # raw bytes
ks.delete("integration/secret1")

# AdHoc commands/scripts
project = rd.projects.get("demo")
exec1 = project.adhoc.run_command("echo 'hello world'")
exec2 = project.adhoc.run_script("echo 'from script'")
# exec2.id to track execution
# Stub mode (no immediate refresh) then manual refresh
exec_stub = project.adhoc.run_command("echo stub", refresh=False)
exec_stub.refresh()  # load the full object
# Script via multipart (upload)
exec3 = project.adhoc.run_script(
    script_file=("hello.sh", "echo multipart", "text/plain"),
    refresh=False,
)

# System features
features = rd.features.list()
if features:
    first = features[0]
    status = rd.features.get(first.name)
    print(first.name, status.enabled)
```

Global configuration `/config`
```python
cfg = rd.config_management
all_configs = cfg.list()
cfg.save([{"key": "ui.banner", "value": "Hello"}])
cfg.delete("ui.banner", strata="default")
cfg.refresh()
cfg.restart()
```

Pagination
----------
Managers inherit `RundeckObjectManager.iter(...)` (offset/max). Example:
```python
for job in rd.jobs.iter(project="demo", page_size=100):
    print(job.id)
```

Error handling
--------------
HTTP errors go through `raise_for_status` and raise dedicated exceptions (e.g., `RundeckAuthenticationError`, `RundeckNotFoundError`, `RundeckValidationError`, `RundeckConflictError`, `RundeckServerError`). Handle them with a `try/except` block around client calls.

Development and testing
-----------------------
- Development setup (contributors): clone the repo and run `poetry install`.
- Formatting/Lint: `black src/rundeck tests/`, `ruff check src/rundeck tests/`
- Typing: `mypy src/rundeck/`
- Tests: `pytest`
- Local integration tests: `scripts/run-integration.sh` (starts docker compose at repo root, exports by default `RUNDECK_URL=http://localhost:4440`, `RUNDECK_TOKEN=adminToken`, `RUNDECK_API_VERSION=56`, waits for the healthcheck, runs `poetry run pytest -m integration`). You can override env vars before running. Add `KEEP_STACK=1` to keep the instance running after tests. Dedicated teardown script: `scripts/stop-integration.sh`.

Code structure
--------------
- `src/rundeck/base.py`: generic objects/managers, `_build_path` helpers, pagination, CRUD.
- `src/rundeck/client.py`: HTTP client, `http_get/post/put/delete/list` methods.
- `src/rundeck/v1/objects/`: domain managers and objects (projects, jobs, executions, system, tokens, users, config_management).
- Managers/objects schema: we apply the manager -> object pattern wherever the API exposes an identifiable resource (jobs, projects, users, tokens, executions, etc.). For purely global or utility endpoints without a resource (e.g., `/system` and its subdomains, `/config`, `/metrics`), we use dedicated sub-managers rather than forcing an artificial object.
