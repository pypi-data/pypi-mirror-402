# ![PCF Toolkit](https://img.shields.io/badge/PCF%20Toolkit-Local%20PCF%20dev-1D4ED8?style=for-the-badge&logo=python&logoColor=white)

Developer-first toolkit for authoring Power Apps PCF manifests and running a local proxy that removes the publish loop.

For detailed guides, API reference, and examples, see [the documentation](https://docs.pcf-toolkit.vectorfy.co).

<div align="left">
  <table>
    <tr>
      <td><strong>Lifecycle</strong></td>
      <td>
        <a href="https://github.com/vectorfy-co/pcf-toolkit/actions/workflows/ci.yml">
          <img src="https://img.shields.io/github/actions/workflow/status/vectorfy-co/pcf-toolkit/ci.yml?branch=main&style=flat&logo=githubactions&logoColor=white" alt="CI status" />
        </a>
        <img src="https://img.shields.io/badge/Python-3.13-3776AB?style=flat&logo=python&logoColor=white" alt="Python 3.13" />
        <img src="https://img.shields.io/github/v/release/vectorfy-co/pcf-toolkit?style=flat&logo=github&logoColor=white" alt="Latest release" />
        <a href="./LICENSE.md">
          <img src="https://img.shields.io/badge/License-Community%20Use-334155?style=flat&logo=spdx&logoColor=white" alt="License: Community Use" />
        </a>
      </td>
    </tr>
    <tr>
      <td><strong>Core Stack</strong></td>
      <td>
        <img src="https://img.shields.io/badge/Python-CLI-3776AB?style=flat&logo=python&logoColor=white" alt="Python CLI" />
        <img src="https://img.shields.io/badge/Pydantic-v2-E92063?style=flat&logo=pydantic&logoColor=white" alt="Pydantic" />
        <img src="https://img.shields.io/badge/Typer-CLI-009688?style=flat&logo=fastapi&logoColor=white" alt="Typer CLI" />
        <img src="https://img.shields.io/badge/YAML-JSON-0F172A?style=flat&logo=json&logoColor=white" alt="YAML and JSON" />
        <img src="https://img.shields.io/badge/Proxy-mitmproxy-1F2937?style=flat&logo=serverfault&logoColor=white" alt="mitmproxy" />
        <img src="https://img.shields.io/badge/Tests-Pytest-0A9EDC?style=flat&logo=pytest&logoColor=white" alt="Pytest" />
      </td>
    </tr>
    <tr>
      <td><strong>Navigation</strong></td>
      <td>
        <a href="https://docs.pcf-toolkit.vectorfy.co"><img src="https://img.shields.io/badge/Docs-Full%20Documentation-2563eb?style=flat&logo=readthedocs&logoColor=white" alt="Documentation" /></a>
        <a href="#quick-start"><img src="https://img.shields.io/badge/Local%20Setup-Quick%20Start-059669?style=flat&logo=serverless&logoColor=white" alt="Quick start" /></a>
        <a href="#features"><img src="https://img.shields.io/badge/Overview-Features-7c3aed?style=flat&logo=simpleicons&logoColor=white" alt="Features" /></a>
        <a href="#configuration"><img src="https://img.shields.io/badge/Config-Proxy%20and%20Manifest-0ea5e9?style=flat&logo=zod&logoColor=white" alt="Configuration" /></a>
        <a href="#ci-cd"><img src="https://img.shields.io/badge/Deploy-CI%2FCD-1F4B99?style=flat&logo=githubactions&logoColor=white" alt="CI/CD" /></a>
        <a href="#architecture"><img src="https://img.shields.io/badge/Design-Architecture-1f2937?style=flat&logo=planetscale&logoColor=white" alt="Architecture" /></a>
        <a href="#operations"><img src="https://img.shields.io/badge/Health-Operations-0F172A?style=flat&logo=serverfault&logoColor=white" alt="Operations" /></a>
        <a href="#troubleshooting"><img src="https://img.shields.io/badge/Help-Troubleshooting-DC2626?style=flat&logo=gnubash&logoColor=white" alt="Troubleshooting" /></a>
      </td>
    </tr>
  </table>
</div>

<a id="quick-start"></a>
## ![Quick Start](https://img.shields.io/badge/Quick%20Start-4%20steps-059669?style=for-the-badge&logo=serverless&logoColor=white)

1. Install (recommended): `uv tool install pcf-toolkit@latest`
2. Initialize a proxy config: `pcf-toolkit proxy init`
3. Build your control so `out/controls/{PCF_NAME}` exists.
4. Start the proxy: `pcf-toolkit proxy start MyComponent`

Run without install (useful in CI or scripts):
```bash
uvx pcf-toolkit --help
```

Requirements:
- Python 3.13
- `uv` (recommended for install/run)
- `mitmproxy` (required for proxy mode; auto-installed if `auto_install: true`)
- Optional: Microsoft PAC CLI (`pac`) for environment discovery

<a id="features"></a>
## ![Features](https://img.shields.io/badge/Features-Highlights-7c3aed?style=for-the-badge&logo=simpleicons&logoColor=white)

| Feature Badge | Details |
| --- | --- |
| ![Proxy](https://img.shields.io/badge/Proxy-Local%20Webresources-1f2937?style=flat&logo=serverfault&logoColor=white) | Intercepts PCF webresource requests and serves your local build without publishing. |
| ![Validation](https://img.shields.io/badge/Validation-Pydantic%20v2-22c55e?style=flat&logo=pydantic&logoColor=white) | Strict schema validation with readable errors. |
| ![Serialization](https://img.shields.io/badge/XML-Deterministic-2563eb?style=flat&logo=xml&logoColor=white) | Stable, ordered XML output for clean diffs. |
| ![Import](https://img.shields.io/badge/Import-XML%20to%20YAML-0ea5e9?style=flat&logo=readme&logoColor=white) | Import legacy XML and keep authoring in YAML or JSON. |
| ![Schemas](https://img.shields.io/badge/Schemas-JSON%20Schema-f97316?style=flat&logo=json&logoColor=white) | Export JSON Schema for editor validation and linting. |
| ![Diagnostics](https://img.shields.io/badge/Doctor-Proxy%20checks-8b5cf6?style=flat&logo=gnubash&logoColor=white) | Diagnoses ports, mitmproxy, certs, and dist paths. |

<a id="configuration"></a>
## ![Configuration](https://img.shields.io/badge/Configuration-Proxy%20and%20Manifest-0ea5e9?style=for-the-badge&logo=zod&logoColor=white)

### Proxy config (pcf-proxy.yaml)
Top-level keys:

| Name | Required | Default | Format | Description |
| --- | --- | --- | --- | --- |
| project_root | no | - | path | Project root for global configs. |
| crm_url | no | - | URL | Power Apps environment URL (required for auto-launch). |
| expected_path | no | /webresources/{PCF_NAME}/ | string | Webresource path template to match. |
| proxy | no | - | object | Proxy endpoint settings. |
| http_server | no | - | object | Local HTTP server settings. |
| bundle | no | - | object | Build output location template. |
| browser | no | - | object | Browser preference and path. |
| mitmproxy | no | - | object | mitmproxy path override. |
| environments | no | - | list | Named environments from PAC. |
| open_browser | no | true | bool | Auto-launch browser with proxy settings. |
| auto_install | no | true | bool | Auto-install mitmproxy if missing. |

proxy:

| Name | Required | Default | Format | Description |
| --- | --- | --- | --- | --- |
| host | no | 127.0.0.1 | string | mitmproxy listen host. |
| port | no | 8080 | int | mitmproxy listen port. |

http_server:

| Name | Required | Default | Format | Description |
| --- | --- | --- | --- | --- |
| host | no | 127.0.0.1 | string | Local file server host. |
| port | no | 8082 | int | Local file server port. |

bundle:

| Name | Required | Default | Format | Description |
| --- | --- | --- | --- | --- |
| dist_path | no | out/controls/{PCF_NAME} | path | Build output template for the control. |

browser:

| Name | Required | Default | Format | Description |
| --- | --- | --- | --- | --- |
| prefer | no | chrome | string | Browser preference: chrome or edge. |
| path | no | - | path | Explicit browser binary path. |

mitmproxy:

| Name | Required | Default | Format | Description |
| --- | --- | --- | --- | --- |
| path | no | - | path | Explicit mitmproxy or mitmdump path. |

environments:

| Name | Required | Default | Format | Description |
| --- | --- | --- | --- | --- |
| name | yes | - | string | Friendly environment name. |
| url | yes | - | URL | Environment base URL. |
| active | no | false | bool | Preferred environment when multiple exist. |

### Manifest authoring
- Author manifests in YAML or JSON.
- Generate XML with `pcf-toolkit generate`.
- Import existing XML with `pcf-toolkit import-xml`.
- Validate with `pcf-toolkit validate`.

### Environment variables
Used internally (set automatically by the CLI):

| Name | Required | Default | Format | Description |
| --- | --- | --- | --- | --- |
| PCF_COMPONENT_NAME | yes | - | string | Component name passed to the proxy addon. |
| PCF_EXPECTED_PATH | no | /webresources/{PCF_NAME}/ | string | Path template used by the redirect addon. |
| HTTP_SERVER_HOST | no | 127.0.0.1 | string | Local HTTP server host. |
| HTTP_SERVER_PORT | no | 8082 | int | Local HTTP server port. |

<a id="ci-cd"></a>
## ![CI/CD](https://img.shields.io/badge/CI%2FCD-Overview-1F4B99?style=for-the-badge&logo=githubactions&logoColor=white)

- Provider: GitHub Actions (`.github/workflows/ci.yml`).
- Triggers: pushes to `main`, PRs targeting `main`, and tags starting with `v`.
- Build steps: install uv, install Python 3.13, sync deps, build schema snapshot and JSON schema.
- Guardrail: `git diff --exit-code` ensures generated schema artifacts are committed.
- Tests: `pytest` with coverage report (terminal output only).
- Publish: on tags `v*`, builds and publishes to PyPI with `uv publish`.

<a id="integration"></a>
## ![Integration](https://img.shields.io/badge/Integration-Power%20Apps-2563eb?style=for-the-badge&logo=simpleicons&logoColor=white)

- Optional: Microsoft PAC CLI (`pac`) for environment discovery and selection.
- The proxy expects your control to build into `bundle.dist_path` (defaults to `out/controls/{PCF_NAME}`).
- The proxy intercepts `/webresources/{PCF_NAME}/...` requests and serves files from your local build output.

<a id="auth"></a>
## ![Auth](https://img.shields.io/badge/Auth%20%26%20Routes-External-2563eb?style=for-the-badge&logo=auth0&logoColor=white)

- The toolkit does not manage authentication.
- PAC CLI uses your existing Power Platform login for environment discovery.
- The proxy does not store tokens or credentials; it only rewrites webresource requests.

<a id="telemetry"></a>
## ![Telemetry](https://img.shields.io/badge/Telemetry-None-f97316?style=for-the-badge&logo=opentelemetry&logoColor=white)

- No telemetry is emitted by default.
- No analytics or event collection is built into the CLI.

<a id="database"></a>
## ![Database](https://img.shields.io/badge/Database-None-0f172a?style=for-the-badge&logo=sqlite&logoColor=white)

- This project does not require a database.

<a id="operations"></a>
## ![Operations](https://img.shields.io/badge/Operations-Health%20%26%20Admin-10b981?style=for-the-badge&logo=serverfault&logoColor=white)

- Use `pcf-toolkit proxy doctor` to check ports, mitmproxy, certs, and dist paths.
- Active proxy sessions store PID metadata in `.pcf-toolkit/proxy.session.json`.
- Detached runs write logs to `.pcf-toolkit/proxy.log`.

<a id="dev-workflow"></a>
## ![Developer Workflow](https://img.shields.io/badge/Developer-Workflow-6366f1?style=for-the-badge&logo=git&logoColor=white)

Install dev dependencies:
```bash
uv sync --extra dev
```

Run tests:
```bash
uv run --python 3.13 pytest
```

Regenerate schema artifacts:
```bash
uv run --python 3.13 --script scripts/build_schema_snapshot.py
uv run --python 3.13 --script scripts/build_json_schema.py
```

If you run `scripts/extract_spec.py`, install browser binaries first:
```bash
uv run --python 3.13 python -m playwright install
```

Build a wheel locally:
```bash
uv build
```

<a id="production"></a>
## ![Production](https://img.shields.io/badge/Production-Readiness-0f766e?style=for-the-badge&logo=serverless&logoColor=white)

- Python 3.13 available.
- `schemas/pcf-manifest.schema.json` and `data/schema_snapshot.json` regenerated.
- `pcf-toolkit proxy doctor` passes for your target component.
- CI pipeline is green and release tag is created for publishing.

<a id="architecture"></a>
## ![Architecture](https://img.shields.io/badge/Architecture-Stack%20map-1f2937?style=for-the-badge&logo=planetscale&logoColor=white)

- CLI: Typer-based commands in `pcf_toolkit.cli` and `pcf_toolkit.proxy.cli`.
- Manifest tooling: Pydantic models validate YAML/JSON and serialize deterministic XML.
- Proxy workflow: `mitmproxy` addon rewrites PCF webresource requests to a local `http.server` instance.
- Schema pipeline: scripts extract and normalize Microsoft Learn references into JSON Schema and snapshots.

<a id="cli-reference"></a>
## ![CLI%20Reference](https://img.shields.io/badge/CLI-Commands-1e293b?style=for-the-badge&logo=gnubash&logoColor=white)

| Command | Purpose |
| --- | --- |
| `pcf-toolkit validate <manifest>` | Validate YAML/JSON against the manifest schema. |
| `pcf-toolkit generate <manifest> -o ControlManifest.Input.xml` | Generate deterministic XML. |
| `pcf-toolkit import-xml <ControlManifest.Input.xml>` | Convert XML to YAML/JSON. |
| `pcf-toolkit export-json-schema -o schemas/pcf-manifest.schema.json` | Export JSON Schema. |
| `pcf-toolkit export-schema -o data/schema_snapshot.json` | Export schema snapshot. |
| `pcf-toolkit proxy init` | Create or update proxy config. |
| `pcf-toolkit proxy start <Component>` | Start proxy session. |
| `pcf-toolkit proxy stop` | Stop proxy session. |
| `pcf-toolkit proxy doctor` | Diagnose proxy prerequisites. |

<a id="troubleshooting"></a>
## ![Troubleshooting](https://img.shields.io/badge/Troubleshooting-Playbook-DC2626?style=for-the-badge&logo=gnubash&logoColor=white)

- Manifest invalid: run `pcf-toolkit validate` and fix fields reported in the error table.
- Dist path missing: run your PCF build or update `bundle.dist_path` in `pcf-proxy.yaml`.
- Config not found: run `pcf-toolkit proxy init` or pass `--config`.
- mitmproxy missing: run `pcf-toolkit proxy doctor --fix` or set `mitmproxy.path`.
- mitmproxy CA cert missing: run `pcf-toolkit proxy doctor` and follow OS-specific guidance.
- Browser did not open: set `crm_url` and check `browser.prefer` or `browser.path`.
- Ports already in use: change `proxy.port` or `http_server.port`.

<a id="notes"></a>
## ![Notes](https://img.shields.io/badge/Notes-Policy-0f172a?style=for-the-badge&logo=readme&logoColor=white)

- License: `LICENSE.md` (Vectorfy Co Community Use License).
- No secrets are stored in the repo; use placeholders in configs.
- Some badges use stand-in icons (Typer uses FastAPI, Proxy uses Server Fault).
