# Command Line Interface

{{project_name}} provides a comprehensive command-line interface (CLI) for performing calculations and managing data.

## Command Structure

The main command is `{{project_slug}}`, with various subcommands organized by functionality:

```
{{project_slug}} <command> [options] [arguments]
```

## Global Options

- `--version`: Display the current version and exit

## Available Commands

### Calculate Commands

The `calculate` group provides commands for basic calculations:

- [add](./calculate.md#add): Add two numbers
- [subtract](./calculate.md#subtract): Subtract one number from another
- [sum](./calculate.md#sum): Calculate the sum of multiple numbers

### Memory Commands

The `memory` group provides commands for working with calculator memory:

- [add](./memory.md#add): Add a value to memory
- [subtract](./memory.md#subtract): Subtract a value from memory
- [show](./memory.md#show): Display the current value in memory
- [reset](./memory.md#reset): Reset the memory to zero
- [history](./memory.md#history): Show the history of operations

### Batch Processing

The `batch` group provides commands for processing data in batch:

- [process](./batch.md#process): Process numbers from a file

### Interactive Shell

- [shell](./shell.md): Start an interactive calculator shell

## Command Documentation

- [Calculate Commands](./calculate.md)
- [Memory Commands](./memory.md)
- [Batch Commands](./batch.md)
- [Shell](./shell.md)

## Example Usage

```bash
# Basic calculations
{{project_slug}} calculate add 5 3
{{project_slug}} calculate subtract 10 4
{{project_slug}} calculate sum 1 2 3 4 5

# Memory operations
{{project_slug}} memory add 5
{{project_slug}} memory show
{{project_slug}} memory subtract 2
{{project_slug}} memory reset

# Batch processing
{{project_slug}} batch process data.json --operation add --base 10 --output results.json

# Interactive shell
{{project_slug}} shell
```