# refcheck

Compare two Python functions using the same inputs. refcheck checks return values,
exceptions, and changes to positional arguments. The Python API can also measure
average execution time.

## Install

Requires Python 3.10 or later. From the repository root:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -e .
```

## Command line

Run the included examples from the repository root:

```powershell
python -m refcheck.cli benchmarks.comparison_cases:double_original benchmarks.comparison_cases:double_changed --output report.json
```

Each function reference can be an importable `module:function` or a file path:

```powershell
python -m refcheck.cli .\benchmarks\comparison_cases.py:double_original .\benchmarks\comparison_cases.py:double_equivalent
```

The CLI uses a generation budget of 100 examples, configurable with `--max-cases`.
Inputs are based on the original function's type annotations.
Both functions receive independent copies of each case's
arguments. It prints `MATCH`, `DIFFERENT`, or `INCOMPLETE` when mutation snapshots
are unavailable and no other difference is known. Differences do not cause a
nonzero exit code.

Omit `--output` for terminal output only. A report replaces an existing file at
the given path; the parent directory must exist. The CLI does not measure timing.
Use `python -m refcheck.cli --help` for usage.

## Python API

Use named cases to check particular inputs. Each case contains a list of
positional arguments; `[[3, 1, 2]]` passes one list argument.

```python
from refcheck.checkers.compare import compare, compare_with_performance


def original(values: list[int]) -> list[int]:
    return sorted(values)


def migrated(values: list[int]) -> list[int]:
    values.sort()
    return values


cases = {"sorting": [[3, 1, 2]]}
results = compare(original, migrated, cases)
result = results["sorting"]

print(result.return_diff)    # False: both return [1, 2, 3].
print(result.mutation_diff)  # Argument 0 differs: only migrated sorts its input.

timed = compare_with_performance(original, migrated, cases, num_executions=100)
print(timed["sorting"].performance_original)  # Average seconds per call.
```

Omit `cases` to generate inputs: `compare(original, migrated, max_cases=100)`.
Generation requires annotations on every parameter and supports fixed positional
parameters, using Hypothesis's `st.from_type()` to resolve their types. Explicit
cases do not require annotations. Both functions must accept the supplied call.

Timing excludes argument copying and skips cases where either function raises.
It does not reset external state between repetitions.

## JSON reports

Export API results with:

```python
from refcheck.reporting import write_json_report

write_json_report(results, "report.json")
```

Reports contain a schema version, summary counts, and each function's inputs,
final argument state, return value or exception, and timings when measured.
`return_diff` also covers exception differences; exceptions match only when their
types and messages match. Mutation differences are keyed by argument position.
`{}` means checked and equal; `null` means unavailable.

NaN/infinity, tuples, and dictionaries with non-string keys use `$type` markers.
Unsupported objects are recorded with their Python type and `repr`.

## Replay a report

New reports use schema version 2 and mark whether each case's starting inputs
can be replayed. Replay supports null, booleans, integers, finite floats, strings,
lists, and dictionaries with string keys. Tuples, non-finite floats, custom
objects, and shared or circular container references are recorded for inspection
but cannot be replayed yet. Ordinary dictionaries containing `$type` are replayed
as dictionaries, never interpreted as Python-object descriptions.

```powershell
# Every case, without generating new inputs.
python -m refcheck.cli benchmarks.comparison_cases:double_original benchmarks.comparison_cases:double_changed --replay report.json

# Cases marked different in the saved report; write fresh results separately.
python -m refcheck.cli benchmarks.comparison_cases:double_original benchmarks.comparison_cases:double_changed --replay report.json --select different --output replayed.json

# Specific cases, in the requested order.
python -m refcheck.cli benchmarks.comparison_cases:double_original benchmarks.comparison_cases:double_changed --replay report.json --case case_1 --case case_3
```

`--select` accepts `all`, `different`, `match`, or `incomplete`. It cannot be
combined with `--case`; repeat `--case` for multiple names. `--max-cases` is only
for generation and cannot be combined with `--replay`.

Selection uses saved statuses, but outcomes are recalculated: a previously
different case may now match. Unknown case names, empty status selections, and
unsupported selected inputs produce errors rather than being silently skipped.
An empty report replays zero cases. All selected inputs and argument counts are
validated before executing targets. Version 1 reports lack replay metadata and
must be regenerated before replay.

Replay leaves the source file unchanged and refuses to write output over it.
New output records the source report path and selected case names in
`replay_source`. It restores argument values, not globals, randomness, databases,
files, or other external state.

The same path is available from Python:

```python
from refcheck.replay import load_replay_cases

cases = load_replay_cases("report.json", status="different")
results = compare(original, migrated, input_data=cases)
```

## Current limits

- Only synchronous positional calls are supported. Generated calls reject
  keyword-only parameters, `*args`, and `**kwargs`.
- Mutation checks compare final argument values, including after exceptions.
  They do not trace intermediate changes, object identity, or local variables.
- Globals, environment variables, files, and other external state are not
  isolated or compared.
- Arguments and returns must support `deepcopy`. Generated callables are not
  reliably supported for comparison and later timing.
- Equality follows Python's rules, except two scalar float NaNs count as equal.
  Arrays, custom equality, cyclic structures, and nested NaNs need further work.
- Generated cases can miss differences. A matching run does not prove equivalence.

## Tests

```powershell
python -m unittest discover -s tests -v
```
