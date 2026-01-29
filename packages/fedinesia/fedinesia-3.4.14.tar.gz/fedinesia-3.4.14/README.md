# Fedinesia

[![Repo](https://img.shields.io/badge/repo-Codeberg.org-blue)](https://codeberg.org/MarvinsMastodonTools/fedinesia) [![CI](https://ci.codeberg.org/api/badges/MarvinsMastodonTools/fedinesia/status.svg)](https://ci.codeberg.org/MarvinsMastodonTools/fedinesia) [![Downloads](https://pepy.tech/badge/fedinesia)](https://pepy.tech/project/fedinesia)

[![Checked against](https://img.shields.io/badge/Safety--DB-Checked-green)](https://pyup.io/safety/) [![Checked with](https://img.shields.io/badge/pip--audit-Checked-green)](https://pypi.org/project/pip-audit/)

[![Code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) [![Version](https://img.shields.io/pypi/pyversions/fedinesia)](https://pypi.org/project/fedinesia) [![Wheel](https://img.shields.io/pypi/wheel/fedinesia)](https://pypi.org/project/fedinesia)

[![AGPL](https://www.gnu.org/graphics/agplv3-with-text-162x68.png)](https://codeberg.org/MarvinsMastodonTools/fedinesia/src/branch/main/LICENSE.md)

> **⚠️ BEWARE, THIS TOOL WILL DELETE SOME OF YOUR POSTS ON THE FEDIVERSE ⚠️**

Fedinesia is a command line (CLI) tool to delete old statuses from Mastodon or Pleroma instances.
It respects rate limits imposed by servers.

## Install and run from [PyPI](https://pypi.org)

It's easy to install Fedinesia from PyPI using the following command:

```bash
pip install fedinesia
```

Once installed, Fedinesia can be started by typing `fedinesia` into the command line.

## Configuration / First Run

Fedinesia will ask for all necessary parameters when run for the first time and store them in a `config.json` file in the current directory.

## Podman / Docker Container

Fedinesia can also be run using [Podman](https://podman.io/) or [Docker](https://www.docker.com/) as follows:

```shell
podman run \
  --env AUDIT_LOG_FILE=/logging/audit.log \
  --env PAUSE_IN_SECONDS=300 \
  --replace \
  --volume ./config:/config \
  --volume ./logging:/logging \
  --name fedinesia \
  codeberg.org/marvinsmastodontools/fedinesia
```

## Podman / Docker Environment Variables

- **PAUSE_IN_SECONDS** (mandatory)
  This must be set to a positive integer. This value is the number of seconds to wait between successive runs of `fedinesia`.

- **AUDIT_LOG_FILE** (optional)
  Full path to where audit log file should be written to. It is intended that logfiles will be written to `/logging` directory.
  No audit log file will be generated / updated if this value has not been set.

- **AUDIT_STYLE** (optional)
  What style of audit log file to write. Possible options are `PLAIN` or `CSV`. Defaults to `PLAIN`.
  Has no effect if `AUDIT_LOG_FILE` has not been set.

- **LIMIT** (optional)
  If set to a positive integer, will make `fedinesia` stop processing any further deletions once this number of statuses have been deleted in the current execution.

- **DRY_RUN** (optional)
  If set to any value, e.g. `DRY_RUN=true`, will make `fedinesia` not actually delete any status. Statuses that would be deleted are shown instead.

- **PROGRESS_FILE** (optional)
  If set to a filename, will store the progress of deleted statuses to that file. This is intended to be used together with the `CONTINUE_PROGRESS` variable. This allows `fedinesia` to process a large number of status deletions over multiple executions while keeping track of progress.

- **CONTINUE_PROGRESS** (optional)
  If set to any value, e.g. `CONTINUE_PROGRESS=true`, will make `fedinesia` continue with deleting statuses from last successfully deleted status in reverse historical order.
  Setting this variable implies that `PROGRESS_FILE` has been set as well.

- **LOGGING_CONFIG** (optional)
  Can be set to a filename containing logging configuration definition. Below is a sample of the logging config file I use during development:

```toml
  [[handlers]]
  sink = &quot;sys.stdout&quot;
  format = &quot;{message}&quot;
  level = &quot;INFO&quot;

  [[handlers]]
  sink = &quot;/logging/dev-fedinesia-debug.log&quot;
  rotation = &quot;1 day&quot;
  retention = 3
  level = &quot;DEBUG&quot;
  format = &quot;{time} - {level} - {name} - {function}({line}) - {message}&quot;
  colorize = &quot;none&quot;
```

## Licensing

Fedinesia is licensed under the [GNU Affero General Public License v3.0](http://www.gnu.org/licenses/agpl-3.0.html).

## Supporting Fedinesia

There are a number of ways you can support Fedinesia:

- Create an issue with problems or ideas you have with/for Fedinesia
- Create a pull request if you are more of a hands-on person
- You can [buy me a coffee](https://www.buymeacoffee.com/marvin8)
- You can send me small change in Monero to the address below:

### Monero donation address

`86ZnRsiFqiDaP2aE3MPHCEhFGTeiFixeQGJZ1FNnjCb7s9Gax6ZNgKTyUPmb21WmT1tk8FgM7cQSD5K7kRtSAt1y7G3Vp98nT`

[AGPL]: https://www.gnu.org/graphics/agplv3-with-text-162x68.png "AGLP 3 or later"
[Repo]: https://img.shields.io/badge/repo-Codeberg.org-blue "Repo at Codeberg.org"
[Downloads]: https://pepy.tech/badge/fedinesia "Download count"
[Code style]: https://img.shields.io/badge/code%20style-black-000000.svg "Code Style: Black"
[Checked against]: https://img.shields.io/badge/Safety--DB-Checked-green "Checked against Safety DB"
[Checked with]: https://img.shields.io/badge/pip--audit-Checked-green "Checked with pip-audit"
[Version]: https://img.shields.io/pypi/pyversions/fedinesia "PyPI - Python Version"
[Wheel]: https://img.shields.io/pypi/wheel/fedinesia "PyPI - Wheel"
[CI]: https://ci.codeberg.org/api/badges/MarvinsMastodonTools/fedinesia/status.svg "CI / Woodpecker"

[Podman]: https://podman.io/
[Docker]: https://www.docker.com/
