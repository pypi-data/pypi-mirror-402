# Batch Commands

Commands for processing data in batch.

## process

Process a batch of numbers from a file.

```bash
{{project_slug}} batch process FILE [OPTIONS]
```

**Arguments:**
- `FILE`: Path to a JSON file containing an array of numbers

**Options:**
- `--operation`: Operation to perform on the data (default: `add`)
  - `add`: Add the base value to each number
  - `subtract`: Subtract each number from the base value
  - `sum`: Calculate the sum of all numbers and add the base value
- `--base`: Base value for operations (default: `0`)
- `--output`: Output file for results in JSON format

**Example:**

Process a file by adding 10 to each number:

```bash
$ {{project_slug}} batch process data.json --operation add --base 10
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Batch Results: Added each number to 10       ┃
┡━━━━━━━━━━━━━━┯━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Input        │ Result                       │
├──────────────┼──────────────────────────────┤
│ 1            │ 11                           │
│ 2            │ 12                           │
│ 3            │ 13                           │
│ 4            │ 14                           │
│ 5            │ 15                           │
└──────────────┴──────────────────────────────┘
```

Process a file, subtract each number from 100, and save results:

```bash
$ {{project_slug}} batch process data.json --operation subtract --base 100 --output results.json
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Batch Results: Subtracted each number from 100  ┃
┡━━━━━━━━━━━━━━┯━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Input        │ Result                          │
├──────────────┼─────────────────────────────────┤
│ 1            │ 99                              │
│ 2            │ 98                              │
│ 3            │ 97                              │
│ 4            │ 96                              │
│ 5            │ 95                              │
└──────────────┴─────────────────────────────────┘
Results saved to results.json
```

Calculate the sum of all numbers plus a base value:

```bash
$ {{project_slug}} batch process data.json --operation sum --base 10
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Batch Results: Calculated sum and added 10    ┃
┡━━━━━━━━━━━━━━━━━━━┯━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Input             │ Result                    │
├───────────────────┼───────────────────────────┤
│ Sum of all inputs │ 25                        │
└───────────────────┴───────────────────────────┘
```

## Input File Format

The input file should be a JSON array of numbers:

```json
[1, 2, 3, 4, 5]
```

## Output File Format

The output file (when using the `--output` option) will be a JSON array of the results:

```json
[11, 12, 13, 14, 15]
```