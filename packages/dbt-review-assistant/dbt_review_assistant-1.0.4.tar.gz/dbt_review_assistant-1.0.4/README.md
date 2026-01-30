[![Tests and Code Checks](https://github.com/sambloom92/dbt-review-assistant/actions/workflows/main.yml/badge.svg)](https://github.com/sambloom92/dbt-review-assistant/actions/workflows/main.yml)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)

# dbt Review Assistant

## A collection of CLI tools designed to make reviewing dbt projects quicker and easier

`dbt-review-assistant` is a Python-based CLI tool which helps dbt developers with ensuring their projects are well
**documented**, comprehensively **tested** and **consistent**.

Maintaining dbt projects can be challenging, especially when the projects get large, complex and have lots of
contributors. `dbt-review-assistant` aims to help developers and reviewers to focus on what matters, by taking care of
the most boring checklist items automatically.

There are 21 checks available in this package, which are available as both standalone CLI commands or as pre-commit
hooks:

### Model checks:

- `models-have-descriptions`: Check if models have descriptions
- `models-have-tags`: Check if models have tags. Optionally specify a set from which models must have all tags,
  or from which they must have at least one tag
- `models-have-contracts`: Check if models have contracts enabled
- `models-have-constraints`: Check if models have constraints configured
- `models-have-data-tests`: Check if models have data tests
- `models-have-unit-tests`: Check if models have unit tests
- `models-have-properties-file`: Check if models have a
  corresponding [properties YAML file](https://docs.getdbt.com/reference/define-properties)
- `model-columns-have-descriptions`: Check if model columns have descriptions
- `model-columns-have-types`: Check if model columns have data types documented
- `model-column-names-match-manifest-vs-catalog`: Check if model column names match between the manifest.json and the
  catalog.json
- `model-column-types-match-manifest-vs-catalog`: Check if model column data types match between the manifest.json and
  the catalog.json
- `model-column-descriptions-are-consistent`: Check if all instances of a column have the same description across
  different models

### Source checks:

- `sources-have-descriptions`: Check if sources have descriptions
- `sources-have-data-tests`: Check if sources have data tests
- `source-columns-have-descriptions`: Check if source columns have descriptions
- `source-columns-have-types`: Check if source columns have data types documented
- `source-column-names-match-manifest-vs-catalog`: Check if source column names match between the manifest.json and the
  catalog.json
- `source-column-types-match-manifest-vs-catalog`: Check if source column data types match between the manifest.json and
  the catalog.json

### Macro checks:

- `macros-have-descriptions`: Check if macros have descriptions
- `macro-arguments-have-descriptions`: Check if macro arguments have descriptions
- `macro-arguments-match-manifest-vs-sql`: Check if macro arguments match between the manifest.json and the macro SQL
  code

## Installing as a stand-alone package

To install the package to be used without pre-commit, run the following:

```commandline
pip install dbt-review-assistant
```

## Usage

Run the following command:

```commandline
dbt-review-assistant
```
Or the abbreviated command:

```commandline
dbtra
```

#### Supported Check Arguments

The following arguments may be used globally, or per-check:

`--project-dir`: Optional - path to the dbt project directory (where the dbt_project.yml file is located). Defaults to
the current working directory.

`--manifest-dir`: Optional - path to the dbt manifest.json file (usually in the dbt project's `target` directory).
Defaults to the `target` directory underneath the dbt project directory.

`--catalog-dir`: path to the dbt catalog.json file (usually in the dbt project's `target` directory).
Defaults to the `target` directory underneath the dbt project directory.

`--include-materializations`: Optional - list of materializations to include models by. Only models materialized as one
of these values will be considered in-scope for the check(s).

`--exclude-materializations`: Optional - list of materializations to exclude models by. Only models not materialized as
one of these values will be considered in-scope for the check(s).

`--include-packages`: Optional - list of dbt package names to include nodes by. Only nodes in one of these packages will
be considered in-scope for the check(s).

`--exclude-packages`: Optional - list of dbt package names to exclude nodes by. Only nodes not in one of these packages
will be considered in-scope for the check(s).

`--include-tags`: Optional - list of tags to include nodes by. Only nodes having at least one of these tags will
be considered in-scope for the check(s).

`--exclude-packages`: Optional - list of tags to exclude nodes by. Nodes which have at least one of these tags will be
considered out-of-scope for the check(s).

`--include-node-paths`: Optional - list of node paths to include nodes by. Nodes not under any of these paths will be
considered out-of-scope for the check(s).

`--exclude-node-paths`: Optional - list of node paths to exclude nodes by. Nodes under any of these paths will be
considered out-of-scope for the check(s).

`--must-have-all-constraints-from`: Optional - List of constraint names, from which objects must have the full set.

`--must-have-any-constraint-from`: Optional - List of constraint names, from which objects must have at least one value.

`--must-have-all-data-tests-from`: Optional - List of data test names, from which objects must have the full set.

`--must-have-any-data-test-from`: Optional - List of data test names, from which objects must have at least one value.

`--must-have-all-tags-from`: Optional - List of tags, from which objects must have the full set.

`--must-have-any-tag-from`: Optional - List of tags, from which objects must have at least one value.

### Running checks individually

To run individual checks using the CLI, run the `dbt-review-assistant` command followed by the name of a check, and any
arguments required, for example:

```commandline
dbt-review-assistant all-models-have-descriptions --include-packages my_dbt_project
```

### Running several checks together

The intended usage of this tool is running several checks all together. This way users ensure the integrity of their dbt
whole project with one single command, and several checks can be written to complement each other and give wide
coverage. There may also be a performance advantage, as `dbt-review-assistant` can cache data between checks to avoid
having to re-load data from the manifest and catalog files.

The config file allows users to configure any number of checks in YAML. Simply create a file named
`.dbt-review-assistant.yaml` and place it anywhere in the repo. Here is an example of a basic config file, defining two
checks:

```yaml
# .dbt-review-assistant.yaml

global_arguments:
  arguments: [
    "--project-dir",
    "my_dbt_project",
    "--include-packages",
    "my_dbt_project",
  ]

per_check_arguments:
  - check_id: models-have-descriptions
    description: We love descriptions! Everything should have descriptions
  - check_id: models-have-constraints
    description: >
      Primary Key constraints are great, but we only want them on tables
    arguments: [
      "--must-have-all-constraints-from",
      "primary_key",
      "--include-materializations",
      "table",
      "incremental"
    ]
```

To run all the checks specified in the config file, use `all-checks` as the check id, and include the `--config-dir` or
`-c`
argument, to tell `dbt-review-assistant` where the config file is:

```commandline
dbt-review-assistant all-checks --config-dir ./my_dbt_project
```

Note - if using `all-checks` then any arguments other than `--config-dir` are ignored, in favour of arguments specified
in the config file.

#### global_arguments

The global_arguments section sets default arguments which will be passed to every check. These arguments will be
overridden by individual checks, if they also define the same arguments with different values.

#### per_check_arguments

The per_check_arguments section sets the arguments for each check instance. Each check instance must specify a
`check-id`, and may optionally set an array of string `arguments`. Note that `check-id` does not need to be unique -
the same check can be used any number of times, to allow them to be used with different arguments. The `description`
key is completely optional, but it is suggested to add a description to tell other developers what the specific check is
and why it is needed, so all contributors to your project know what the expectations are.

### Running checks using pre-commit

All checks may be run as pre-commit hooks, either individually, or as one single entry encompassing one or more checks.

For example, to run all hooks, use the all-checks hook and point it to the config file directory:

```yaml
repos:
  - repo: https://github.com/sambloom92/dbt-review-assistant
    rev: <latest tag>
    hooks:
      - id: all-checks
        args: [ "--config-dir", "my_dbt_project" ]
```

Or to run individual checks as standalone hooks:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/sambloom92/dbt-review-assistant
    rev: <latest tag>
    hooks:
      - id: all-models-have-descriptions
        pass_filenames: false
        args: [ "--include-packages", "my_dbt_project" ]
      - id: all-models-have-constraints
        pass_filenames: false
        args: [
          "--must-have-all-constraints-from",
          "primary_key",
          "--include-materializations",
          "table",
          "incremental"
        ]
```

Note that the recommended option is to use the single entry version, because this can benefit from improved performance
by allowing `dbt-review-assistant` to cache data in memory between checks. Running checks individually forces them to be
run in
separate environments, so they cannot share cached data.

### Using `pass_filenames`

pre-commit hooks have an option called `pass_filenames`, which defaults to true. This instructs pre-commit to pass all
filenames that are staged for commit into the hook entry command as positional arguments.

`dbt-review-assistant` does not support `pass_filenames: true`, and so all hooks will come with `pass_filenames: false`
by default, and it should not be overridden. Be aware that if using these hooks with `repo: local`, this will change the
default value back to `pass_filenames: false`, so all examples here explicitly include the correct setting, even though
it is not always strictly necessary.

Disabling `pass_filenames` for hooks is a deliberate design choice, which greatly simplifies how the tool works.
Although it can be helpful to only run checks on files that have changed, this is very complicated to do correctly in
practice, due to the complex dependencies between files within dbt projects. A more 'slim' option might be developed as
a future improvement, but for now the entire project is checked (unless nodes are excluded by specific arguments),
regardless of which files are staged for commit.

### Refreshing dbt artifacts

All checks rely on the data in the dbt `manifest.json` file, and some checks have an additional dependency on the dbt
`catalog.json` file. As such, these files need to be refreshed whenever any change is made to the dbt project, otherwise
`dbt-review-assistant` will not have the most up-to-date view of your project. `dbt-review-assistant` does not look at
any SQL or YAML files in your project at all, or connect to you database, or even run any dbt commands - the manifest
and catalog JSON files are its only source of truth.

This table shows which checks require which dbt artifacts:

| check-id                                        | manifest | catalog |
|-------------------------------------------------|----------|---------|
| `models-have-descriptions`                      | ✅        | ❌       |
| `models-have-tags`                              | ✅        | ❌       |
| `models-have-contracts`                         | ✅        | ❌       |
| `models-have-constraints`                       | ✅        | ❌       |
| `models-have-data-tests`                        | ✅        | ❌       |
| `models-have-unit-tests`                        | ✅        | ❌       |
| `models-have-properties-file`                   | ✅        | ❌       |
| `model-columns-have-descriptions`               | ✅        | ❌       |
| `model-columns-have-types`                      | ✅        | ❌       |
| `model-column-names-match-manifest-vs-catalog`  | ✅        | ✅       |
| `model-column-types-match-manifest-vs-catalog`  | ✅        | ✅       |
| `model-column-descriptions-are-consistent`      | ✅        | ❌       |
| `sources-have-descriptions`                     | ✅        | ❌       |
| `sources-have-data-tests`                       | ✅        | ❌       |
| `source-columns-have-descriptions`              | ✅        | ❌       |
| `source-columns-have-types`                     | ✅        | ❌       |
| `source-column-names-match-manifest-vs-catalog` | ✅        | ✅       |
| `source-column-types-match-manifest-vs-catalog` | ✅        | ✅       |
| `macros-have-descriptions`                      | ✅        | ❌       |
| `macro-arguments-have-descriptions`             | ✅        | ❌       |
| `macro-arguments-match-manifest-vs-sql`         | ✅        | ❌       |

These JSON files are typically in the `.gitignore`, so they are not tracked in git, and are often cleaned up when
running `dbt clean`, so knowing how to generate them is important.

To refresh the manifest, run:

```commandline
dbt parse
```

To refresh the catalog, run:

```commandline
dbt docs generate --no-compile
```

To ensure the manifest and/or catalog are refreshed automatically by pre-commit, simply add dbt commands as locally
installed entries to your existing pre-commit configuration, before the checks:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: refresh-manifest
        name: Refresh dbt Manifest
        entry: dbt parse
        args: [
          "--project-dir",
          "./my_dbt_project",
          "--profiles-dir",
          "./my_dbt_project"
        ]
        language: python
        pass_filenames: false
        types: [sql,yaml]
      - id: refresh-catalog
        name: Refresh dbt Catalog
        entry: dbt docs generate
        args: [
          "--project-dir",
          "./my_dbt_project",
          "--profiles-dir",
          "./my_dbt_project",
          "--no-compile"
        ]
        language: python
        pass_filenames: false
        types: [sql,yaml]
  - repo: https://github.com/sambloom92/dbt-review-assistant
    rev: <latest tag>
    hooks:
      - id: all-models-have-descriptions
        args: [ "--include-packages", "my_dbt_project" ]
      - id: all-models-have-constraints
        args: [
          "--must-have-all-constraints-from",
          "primary_key",
          "--include-materializations",
          "table",
          "incremental"
        ]
```

The `refresh-manifest` and `refresh-catalog` hooks demonstrated above are not part of `dbt-review-assistant`, and rely
on your project's own local dbt installation. Add whichever arguments you would normally include when running dbt
commands within your project. To use these in a CI environment such as GitHubActions, ensure that the worker has
the dbt adapter installed and, if refreshing the catalog, has permission to connect to your database.

### GitHub Actions

This tool can be used as part of a GitHub Actions Workflow, however this repository does
not provide a ready-made GitHub Action. This is because the implementation details would be heavily dependent on the 
project's unique dbt setup, including the build system and method of authentication to connect to the data platform.

To write your own GitHub Actions Workflow, the following steps should be included:

1. Run the `dbt parse` command. Note that this requires dbt to be installed.
2. Run the `dbt docs generate --no-compile` command (Optional - can be skipped if not required - see table of check requirements above). 
Note that this requires a connection, and therefore authentication with your data plaform.
3. Run the `dbt-review-assistant` command

Here is an example of a GitHub Actions Workflow for a BigQuery project, using service account authentication,
with the keyfile stored as a GitHub secret:

```yaml
# .github/workflows/ci.yml

name: run dbt review assistant
on:
  pull_request:
    branches:
      - main
jobs:
  run_bigquery:
    name: dbt-review-assistant
    runs-on: ubuntu-latest

    env:
      DBT_PROFILES_DIR: ./
      DBT_GOOGLE_PROJECT: ${{ vars.DBT_GOOGLE_PROJECT }}
      DBT_GOOGLE_DATASET: ${{ vars.DBT_GOOGLE_DATASET }}
      DBT_GOOGLE_KEYFILE: /tmp/google/google-service-account.json
      KEYFILE_CONTENTS: ${{secrets.KEYFILE_CONTENTS}}

    steps:
      - run: mkdir -p "$(dirname $DBT_GOOGLE_KEYFILE)"
      - run: echo "$KEYFILE_CONTENTS" > $DBT_GOOGLE_KEYFILE
      - uses: "actions/checkout@v4"
      - uses: "actions/setup-python@v5"
        with:
          python-version: "3.12"
      - name: Install uv
        run: python3 -m pip install uv
      - name: Install python deps
        run: uv pip install -r requirements.txt --system
      - name: Run dbt deps
        run: dbt deps
      - name: Run dbt parse
        run: dbt parse
      - name: Run dbt docs generate
        run: dbt docs generate --no-compile
      - name: Run dbt-review-assistant
        run: dbt-review-assistant all-checks --config ./
```

With the following `profiles.yml` contents:

```yaml
# .profiles.yml

jaffle_shop:
  outputs:
    dev:
      job_execution_timeout_seconds: 300
      job_retries: 1
      location: europe-west2
      method: service-account
      keyfile: "{{ env_var('DBT_GOOGLE_KEYFILE') }}"
      project: "{{ env_var('DBT_GOOGLE_PROJECT') }}"
      dataset: "{{ env_var('DBT_GOOGLE_DATASET') }}"
      priority: interactive
      threads: 1
      type: bigquery
  target: dev
```

This example requires a GitHub secret called `KEYFILE_CONTENTS`, with the contents of a service account keyfile, and the
following environment variables:
- `DBT_GOOGLE_KEYFILE`: filepath to the service account JSON keyfile
- `DBT_GOOGLE_PROJECT`: GCP project ID for the dbt project
- `DBT_GOOGLE_DATASET`: GCP dataset ID for the dbt project

Your data platform may require a different authentication method, and your dbt project may require different steps for
installing dependencies, so adjust this example accordingly.

### Acknowledgements

This tool was inspired by the popular [dbt-checkpoint](https://github.com/dbt-checkpoint/dbt-checkpoint) pre-commit
hooks by [DataCoves](https://datacoves.com/product) (formerly pre-commit-dbt). I have found these hooks
immensely useful for my own dbt projects, and I am very grateful to them for contributing it. That said, there were a
number of ways in which I believed it could be improved and simplified, so I decided to try writing my own tool. While
there may be similarities in some of the checks, all code in this repository is written by myself, with nothing taken
from any other projects or AI tools.
