# notebooklm CLI/API surface

Date: 2026-04-25
Branch: `feat/nblm/notebooklm-cli-surface`
Worktree: `/home/ned/src/ai-work/wittgenstein-worktrees/notebooklm-cli-surface`
Probe venv: `/tmp/witt-notebooklm-py-probe-venv`
Package: `notebooklm-py 0.3.4`

## Scope

This document records the **local CLI and Python API surface** exposed by the installed `notebooklm-py` package.

It is intentionally limited to:

- `--help`-style CLI inspection
- package metadata inspection
- Python import/introspection
- reading installed source files from the probe venv

It does **not** verify real NotebookLM operations, auth flows, browser automation, or network-backed notebook actions.

## Verified local package identity

The verified local mapping is:

- PyPI/install name: `notebooklm-py`
- import package: `notebooklm`
- client module: `notebooklm.client`
- console entry point: `notebooklm -> notebooklm.notebooklm_cli:main`
- installed executable in the probe venv: `/tmp/witt-notebooklm-py-probe-venv/bin/notebooklm`

Important negative fact:

- `notebooklm_py` is **not** the working import package in this environment.

## CLI command map

### Verified top-level command surface

Verified with `notebooklm --help` and `notebooklm <subcommand> --help` for discovered top-level subcommands.

#### Global options

- `--version`
- `--storage PATH`
- `-v, --verbose`
- `--help`

#### Top-level commands

##### Session
- `login`
- `use`
- `status`
- `clear`

##### Notebooks
- `list`
- `create`
- `delete`
- `rename`
- `summary`
- `metadata`

##### Chat
- `ask`
- `configure`
- `history`

##### Command groups
- `source`
- `artifact`
- `note`
- `share`
- `research`
- `generate`
- `download`
- `auth`
- `language`
- `skill`

### Nested commands discovered from group help and Click introspection

These names were discovered locally from `notebooklm <group> --help` and from the imported Click command tree. They were **not** exercised beyond help/introspection.

#### `notebooklm source`
- `list`
- `add`
- `add-drive`
- `add-research`
- `get`
- `fulltext`
- `guide`
- `stale`
- `delete`
- `delete-by-title`
- `rename`
- `refresh`
- `wait`

#### `notebooklm artifact`
- `list`
- `get`
- `rename`
- `delete`
- `export`
- `poll`
- `wait`
- `suggestions`

#### `notebooklm note`
- `list`
- `create`
- `get`
- `save`
- `rename`
- `delete`

#### `notebooklm share`
- `status`
- `public`
- `view-level`
- `add`
- `update`
- `remove`

#### `notebooklm research`
- `status`
- `wait`

#### `notebooklm generate`
- `audio`
- `video`
- `cinematic-video`
- `slide-deck`
- `revise-slide`
- `quiz`
- `flashcards`
- `infographic`
- `data-table`
- `mind-map`
- `report`

#### `notebooklm download`
- `audio`
- `video`
- `cinematic-video`
- `slide-deck`
- `infographic`
- `report`
- `mind-map`
- `data-table`
- `quiz`
- `flashcards`

#### `notebooklm auth`
- `check`

#### `notebooklm language`
- `list`
- `get`
- `set`

#### `notebooklm skill`
- `install`
- `status`
- `uninstall`
- `show`

### CLI source files read

The installed CLI entry file is:

- `/tmp/witt-notebooklm-py-probe-venv/lib/python3.14/site-packages/notebooklm/notebooklm_cli.py`

The installed CLI subcommand modules include:

- `notebooklm/cli/session.py`
- `notebooklm/cli/notebook.py`
- `notebooklm/cli/chat.py`
- `notebooklm/cli/source.py`
- `notebooklm/cli/artifact.py`
- `notebooklm/cli/note.py`
- `notebooklm/cli/share.py`
- `notebooklm/cli/research.py`
- `notebooklm/cli/generate.py`
- `notebooklm/cli/download.py`
- `notebooklm/cli/auth.py` is **not** present as a file; `auth check` is still registered in the Click tree via the package imports
- `notebooklm/cli/language.py`
- `notebooklm/cli/skill.py`

## Python API surface map

### Public package export surface

Verified from `notebooklm/__init__.py`:

- primary client: `NotebookLMClient`
- auth type: `AuthTokens`
- default storage constant: `DEFAULT_STORAGE_PATH`
- notebook/source/artifact/note/chat/share dataclasses and enums
- exception hierarchy rooted at `NotebookLMError`
- configuration enums such as `AudioFormat`, `ReportFormat`, `SharePermission`, `VideoStyle`

The package declares a large `__all__` export surface in `notebooklm/__init__.py`, so importing from `notebooklm` is the supported public API style.

### Main client module

Installed file:

- `/tmp/witt-notebooklm-py-probe-venv/lib/python3.14/site-packages/notebooklm/client.py`

Verified client class:

- `NotebookLMClient(auth: AuthTokens, timeout: float = 30.0)`

Verified `NotebookLMClient` members:

- `from_storage(cls, path: str | None = None, timeout: float = 30.0)` — async classmethod
- `refresh_auth(self)` — async
- `auth` — property
- `is_connected` — property
- async context-manager methods are present in source: `__aenter__`, `__aexit__`

### Namespaced API objects created by `NotebookLMClient`

Verified from `client.py` source:

- `client.notebooks`
- `client.sources`
- `client.notes`
- `client.artifacts`
- `client.chat`
- `client.research`
- `client.settings`
- `client.sharing`

### Verified API classes and public method families

All of the classes below are installed under `site-packages/notebooklm/` and were discovered by importing `notebooklm.client` and reading installed source.

#### `NotebooksAPI` (`_notebooks.py`)
- async: `list`, `create`, `get`, `delete`, `rename`, `get_summary`, `get_description`, `remove_from_recent`, `get_raw`, `share`, `get_metadata`
- sync: `get_share_url`

#### `SourcesAPI` (`_sources.py`)
- async: `list`, `get`, `wait_until_ready`, `wait_for_sources`
- async source creation/update methods: `add_url`, `add_text`, `add_file`, `add_drive`, `delete`, `rename`, `refresh`
- async inspection methods: `check_freshness`, `get_guide`, `get_fulltext`

#### `ChatAPI` (`_chat.py`)
- async: `ask`, `get_conversation_turns`, `get_conversation_id`, `get_history`, `configure`, `set_mode`
- sync/local-cache helpers: `get_cached_turns`, `clear_cache`

#### `ArtifactsAPI` (`_artifacts.py`)
- async list/get families: `list`, `get`, `list_audio`, `list_video`, `list_reports`, `list_quizzes`, `list_flashcards`, `list_infographics`, `list_slide_decks`, `list_data_tables`
- async generation families: `generate_audio`, `generate_video`, `generate_cinematic_video`, `generate_report`, `generate_study_guide`, `generate_quiz`, `generate_flashcards`, `generate_infographic`, `generate_slide_deck`, `generate_data_table`, `generate_mind_map`, `revise_slide`
- async download/export families: `download_audio`, `download_video`, `download_infographic`, `download_slide_deck`, `download_report`, `download_mind_map`, `download_data_table`, `download_quiz`, `download_flashcards`, `export`, `export_report`, `export_data_table`
- async lifecycle helpers: `delete`, `rename`, `poll_status`, `wait_for_completion`, `suggest_reports`

#### `NotesAPI` (`_notes.py`)
- async: `list`, `get`, `create`, `update`, `delete`, `list_mind_maps`, `delete_mind_map`

#### `ResearchAPI` (`_research.py`)
- async: `start`, `poll`, `import_sources`

#### `SettingsAPI` (`_settings.py`)
- async: `set_output_language`, `get_output_language`

#### `SharingAPI` (`_sharing.py`)
- async: `get_status`, `set_public`, `set_view_level`, `add_user`, `update_user`, `remove_user`

### Auth and path implications visible from source

Verified from `notebooklm/auth.py` and `notebooklm/paths.py`:

- `NotebookLMClient.from_storage()` ultimately loads Playwright `storage_state.json`
- default home directory is `~/.notebooklm`, overridable by `NOTEBOOKLM_HOME`
- default storage path is `~/.notebooklm/storage_state.json`
- auth source code explicitly fetches fresh CSRF/session tokens from `https://notebooklm.google.com/`
- package docs in `__init__.py` state that it uses **undocumented Google APIs that can change without notice**

## What is verified safe

The following were verified without performing real NotebookLM operations:

- creating or reusing the isolated probe venv
- importing `notebooklm` and `notebooklm.client`
- reading package metadata via `pip show` / `importlib.metadata`
- resolving the console entry point
- running `notebooklm --help`
- running `notebooklm <top-level-subcommand> --help` for discovered top-level subcommands
- importing the Click CLI object and listing its command tree
- reading installed source files from the probe venv

For Wittgenstein, the currently verified safe smoke command remains:

```bash
source /tmp/witt-notebooklm-py-probe-venv/bin/activate
notebooklm --help
```

## What is still not verified

The following remain out of scope and must **not** be assumed:

- `notebooklm login` runtime behavior
- `notebooklm list`, `create`, `delete`, `rename`, `summary`, `metadata` runtime behavior
- `notebooklm ask`, `configure`, `history` runtime behavior
- any `source`, `artifact`, `note`, `share`, `research`, `generate`, `download`, `language`, `skill`, or `auth check` runtime behavior beyond help/introspection
- whether non-help commands are purely local or trigger browser/network activity
- whether `NotebookLMClient.from_storage()` works with real credentials in this environment
- whether any of the async client methods are stable against current upstream NotebookLM behavior
- whether Playwright/browser dependencies are required for real auth flows here
- any adapter behavior, replay behavior, or artifact capture beyond the existing dossier provider seam

## Adapter implications for the dossier provider

### Immediate implications

1. **Use the verified names, not guessed names.**
   - install: `notebooklm-py`
   - import: `notebooklm`
   - CLI: `notebooklm`

2. **The package already exposes a richer Python API than the CLI contract we have verified.**
   If a future lane builds a real adapter, it can choose between:
   - wrapping the CLI, or
   - calling `NotebookLMClient` directly.

3. **The client is async and auth-backed.**
   Any real adapter will need an async boundary plus explicit credential/storage handling.

4. **Real auth/network behavior is outside the currently trusted dossier-core boundary.**
   This aligns with `DEC-0001`: NotebookLM can remain a provider seam, but it must not silently become a second authority path.

### Recommended shape for a future adapter lane

A future NotebookLM adapter should start as a thin provider seam that:

- keeps dossier-core local-first
- uses the verified smoke command and import path as preflight checks
- records provider request/response metadata in `provider-output.md`
- treats auth/session/network failures as structured provider errors
- preserves the existing offline artifact spine and replay behavior
- keeps implementation authority local/deterministic unless a later decision explicitly widens the boundary

### What this lane does **not** justify

This surface probe does **not** justify:

- wiring NotebookLM into dossier-core now
- importing `notebooklm` inside the current guarded Level A authority surface
- adding browser automation
- treating NotebookLM outputs as implementation-authorizing facts
- assuming that CLI help implies safe execution for non-help commands

## Notes on introspection limits

A direct `inspect.signature()` pass over some installed async methods hit a Python 3.14 annotation-evaluation `TypeError` inside the package's installed code. Public method families were therefore verified by a mix of:

- import-based member discovery
- coroutine detection
- installed source-file reading

That is sufficient for this surface map, but it is another reason not to overclaim runtime compatibility from introspection alone.
