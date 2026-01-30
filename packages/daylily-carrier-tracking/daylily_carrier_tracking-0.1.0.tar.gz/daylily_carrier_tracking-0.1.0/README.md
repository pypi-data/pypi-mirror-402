# daylily-carrier-tracking

Unified multi-carrier package tracking library + CLI.

## Implementation status

- **FedEx**: implemented (OAuth2 + Track API v1, with optional Ship fallback)
- **UPS**: scaffolded (config + CLI plumbing; live tracking not implemented yet)
- **USPS**: scaffolded (config + CLI plumbing; live tracking not implemented yet)

## Install

### Recommended (development, isolated virtualenv)

This repo includes a helper script that **always** installs into a local `./.venv` so you don't accidentally `pip install -e .` into your system/base Python.

```bash
./dev-setup.sh
```

If you want the venv **activated in your current shell** (so `tday ...` works without `./`), source it:

```bash
. ./dev-setup.sh
```

After setup you can run either:

```bash
./tday --help   # wrapper; prefers ./.venv/bin/python automatically
tday --help     # console script (when your venv is active)
```

### Manual install (advanced)

Only do this if you know what you're doing; the helper above is safer.

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
```

### direnv (optional)

`.envrc` is gitignored by design. Use the provided example:

```bash
cp .envrc.example .envrc
direnv allow
```

### Repo checkout usage without install

You can run the repo wrapper directly; if `./.venv` exists it will be used automatically.

```bash
./tday --help
```

### Deprecated wrapper

```bash
./tracking_day --help
```

## Configuration

### Config locations

New default location (preferred):

```text
~/.config/daylily-carrier-tracking/<carrier>_<env>.yaml
```

Example:

```text
~/.config/daylily-carrier-tracking/fedex_prod.yaml
```

Legacy fallback (for backward compatibility in some code paths):

```text
~/.config/<carrier>/<carrier>_<env>.yaml
```

### Environments

`<env>` is a free-form string used in the filename suffix.

- Default: `prod`
- Common alternatives: `test`, `sandbox`, `dev`

### YAML examples

FedEx (required keys: `oauth_url` (or `api_url`), `client_id`, `client_secret`):

```yaml
---
oauth_url: https://apis.fedex.com/oauth/token
client_id: "YOUR_FEDEX_CLIENT_ID"
client_secret: "YOUR_FEDEX_CLIENT_SECRET"

# Optional overrides:
track_url: https://apis.fedex.com/track/v1/trackingnumbers
ship_track_url: ""  # set to https://apis.fedex.com/ship/v1/trackingnumbers to enable ship fallback
```

UPS (scaffolded; `doctor` currently validates presence of `client_id` + `client_secret`):

```yaml
---
client_id: "YOUR_UPS_CLIENT_ID"
client_secret: "YOUR_UPS_CLIENT_SECRET"
```

USPS (scaffolded; `doctor` currently validates presence of `client_id` + `client_secret`):

```yaml
---
client_id: "YOUR_USPS_CLIENT_ID"
client_secret: "YOUR_USPS_CLIENT_SECRET"
```

### Interactive wizard

Create/update config files interactively:

```bash
tday configure fedex --env prod
tday configure ups --env prod
tday configure usps --env prod
```

Notes:

- `configure fedex` prompts for credentials and can validate them via an OAuth token request.
- `configure ups/usps` currently writes a placeholder YAML and exits non-zero (see Exit Codes).

## CLI

All commands:

```bash
tday --help
tday <command> --help
```

### Global flags

- `--pretty`: pretty-print JSON output (applies to JSON-producing commands like `track`)
- `--no-color`: disable ANSI colored status output on stderr
  - Also respected via `NO_COLOR=1`

### Shell tab completion (bash/zsh)

This repo includes completion scripts under `./completions/` and the CLI can also print them on-demand:

- `tday completion bash`
- `tday completion zsh`

- Bash: `completions/tday.bash`
- Zsh: `completions/_tday`

#### Bash

One-shot (current shell):

```bash
source <(tday completion bash)
```

Repo checkout (source file directly):

```bash
source /path/to/daylily-carrier-tracking/completions/tday.bash
```

To persist, add a `source ...` line to your `~/.bashrc` (or equivalent), e.g.:

```bash
mkdir -p ~/.bash_completion.d
tday completion bash > ~/.bash_completion.d/tday
echo 'source ~/.bash_completion.d/tday' >> ~/.bashrc
```

#### Zsh

One-shot (current shell):

```bash
source <(tday completion zsh)
```

Install (write into a completions dir):

```bash
mkdir -p ~/.zsh/completions
tday completion zsh > ~/.zsh/completions/_tday
```

Then ensure your `~/.zshrc` contains something like:

```bash
fpath=(~/.zsh/completions $fpath)
autoload -Uz compinit
compinit
```

Note: the completion targets the installed command name `tday`. If you mainly run the repo wrapper `./tday`, use:

```bash
# activate the venv so the installed console script is on PATH
. ./.venv/bin/activate
tday --help
```

The completion scripts are intentionally registered **only** for the `tday` command name (not `./tday`, and not the deprecated `tracking_day`).

### `tday test`

Run unit tests.

```bash
tday test
tday test --test-fedex
tday test --test-ups
tday test --test-usps
```

Notes:

- Carrier-specific test selection looks for `tests/test_<carrier>_*.py`.

### `tday configure`

Interactive credential setup wizard.

```bash
tday configure <fedex|ups|usps> [--env prod] [--path /custom/path.yaml] [--skip-validate]
```

### `tday track`

Perform a live tracking call and print a JSON result to stdout.

```bash
tday track <TRACKING_NUMBER> \
  --carrier auto|fedex|ups|usps \
  [--api-preference auto|track|ship] \
  [--no-raw] \
  [--pretty]
```

Key flags:

- `--carrier`
  - `auto` uses `detect_carrier()` to guess a carrier (best-effort).
- `--no-raw` omits the raw carrier payload from the returned JSON.
- `--api-preference` (FedEx only)
  - `track`: Track API only
  - `ship`: Ship endpoint only (requires `ship_track_url` to be set)
  - `auto`: try Track first; if the response looks like “not found” and `ship_track_url` is configured, try Ship

Examples:

```bash
tday track 395579987149 --carrier fedex --api-preference auto --pretty --no-raw
tday track 1Z999AA10123456784 --carrier auto --pretty
```

### `tday doctor`

Diagnose config + (optionally) test live FedEx OAuth/track.

```bash
tday doctor \
  [--all] \
  --carrier auto|fedex|ups|usps \
  [--env prod] \
  [--config-path /path/to/config.yaml] \
  [--no-network] \
  [--tracking-number <TRACKING_NUMBER>] \
  [--json]
```

Also supported:

- `--all`: run doctor for **fedex + ups + usps** and emit a single aggregated JSON report (implies `--json`).
  - Note: `--all` currently **cannot** be combined with `--config-path` (no per-carrier overrides yet).

Examples and sample payloads: see [`docs/doctor-examples.md`](docs/doctor-examples.md).

#### JSON output (`--json`)

`--json` prints structured JSON to **stdout** (CI/support-ticket friendly) and suppresses human/colored output.

High-level shape:

- `doctor_version`
- `carrier`: `{ requested, detected, effective }`
- `env`
- `python`: `{ executable, version }`
- `package`: `{ file }` (or `{ error }`)
- `config`: `{ source, path, exists, keys, required, presence, valid, ... }`
- `network`: `{ requested, implemented, note, oauth, track }`
- `tracking`: `{ number, normalized, normalized_error }`

Examples:

```bash
tday doctor --carrier fedex --env prod --tracking-number 395579987149 --json | jq
tday doctor --carrier ups --env prod --json | jq
tday doctor --carrier usps --env prod --json | jq

# Aggregate all carriers into one JSON report
tday doctor --all --env prod --json | jq
```

#### Carrier auto-detection

If you want `doctor` to infer carrier from the tracking number:

```bash
tday doctor --carrier auto --tracking-number <TRACKING_NUMBER> --json | jq
```

### Deprecated aliases

These are kept for backward compatibility and map to `track` internally:

- `tday fedex <TN> [...]` → `tday track <TN> --carrier fedex [...]`
- `tday ups <TN> [...]` → `tday track <TN> --carrier ups [...]`
- `tday usps <TN> [...]` → `tday track <TN> --carrier usps [...]`

## Exit codes (CI-friendly)

These are the current conventions used by the CLI:

### `tday doctor`

- `0`: config valid (and any requested FedEx network checks succeeded)
- `2`: config missing/invalid (all carriers) OR other validation error
- `3`: FedEx OAuth token request failed
- `4`: FedEx live track call failed

In `doctor --all` mode, the overall exit code is the “most severe” code across carriers (priority: `4 > 3 > 2 > 0`).

### `tday track`

- `0`: success
- `1`: runtime error (exception)
- `2`: carrier not implemented / config issues resulting in `NotImplementedError`

### `tday configure`

- `0`: wrote config (and validation succeeded, if applicable)
- `2`: UPS/USPS wizard is scaffolded (placeholder written)
- `3`: FedEx credential validation failed

### `tday test`

- `0`: all selected tests passed
- `2`: `tests/` missing, or a selected carrier test pattern matched no files
- otherwise: underlying `python -m unittest` return code

## CI (GitHub Actions) snippet

Minimal CI steps that (a) capture `doctor --json` output to files via `tee`, and (b) **fail the job** on non-zero exit codes.

> Note: GitHub Actions `run:` steps use `bash -e -o pipefail` by default on Linux/macOS runners, so a failing `tday doctor ...` will still fail even when piped to `tee`.

```yaml
- name: Doctor (UPS)
  run: tday doctor --carrier ups --env prod --json | tee ups_doctor.json

- name: Doctor (USPS)
  run: tday doctor --carrier usps --env prod --json | tee usps_doctor.json

- name: Doctor (ALL carriers, single JSON)
  run: tday doctor --all --env prod --json | tee doctor_all.json
```

## Credential setup (how to obtain credentials)

This project expects you to create carrier developer credentials and store them locally in `~/.config/daylily-carrier-tracking/`.

### FedEx

Portals/docs (observed 2026-01-22):

- FedEx Developer Portal: https://developer.fedex.com/api/en-us/home.html
- OAuth/Authorization docs: https://developer.fedex.com/api/en-us/catalog/authorization/v1/docs.html

Typical steps:

1. Create/login to a FedEx Developer account.
2. Create a project/app and enable APIs:
   - Track API (v1)
   - (Optional) Ship API if you want the `ship` fallback route
3. Generate OAuth2 client credentials (client id / client secret).
4. Create `~/.config/daylily-carrier-tracking/fedex_prod.yaml` with `oauth_url`, `client_id`, `client_secret`.
5. Validate:

```bash
tday doctor --carrier fedex --env prod --json | jq
```

Notes:

- Production credentials may require additional FedEx account verification/approval.
- Sandbox vs production endpoints/credentials are distinct; name your `--env` accordingly.

### UPS

Portals/docs (observed 2026-01-22):

- UPS Developer Portal: https://developer.ups.com/
- OAuth Client Credentials tag/docs entry point: https://developer.ups.com/tag/OAuth-Client-Credentials

Typical steps:

1. Create/login to a UPS Developer account.
2. Create an app and subscribe to the APIs you need (e.g., Tracking).
3. Generate OAuth client credentials.
4. Create `~/.config/daylily-carrier-tracking/ups_prod.yaml` with `client_id` and `client_secret`.
5. Validate config presence (network checks not implemented yet):

```bash
tday doctor --carrier ups --env prod --json | jq
```

### USPS

Portals/docs (observed 2026-01-22):

- USPS Developer Portal: https://developers.usps.com/home
- USPS Web Tools overview: https://www.usps.com/business/web-tools-apis/

Typical steps:

1. Create/login to the USPS Developer Portal.
2. Request access to the relevant APIs for tracking.
3. Create `~/.config/daylily-carrier-tracking/usps_prod.yaml` with `client_id` and `client_secret`.
4. Validate config presence (network checks not implemented yet):

```bash
tday doctor --carrier usps --env prod --json | jq
```

Note (time-sensitive): The USPS Web Tools page currently warns that legacy Web Tools APIs are being sunset (see USPS site for the current status).

## Tests

```bash
python -m unittest discover -s tests
```
