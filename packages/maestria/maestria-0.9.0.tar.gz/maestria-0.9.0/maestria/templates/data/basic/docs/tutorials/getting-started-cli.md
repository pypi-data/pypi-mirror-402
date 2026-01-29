# Getting Started with the CLI

This tutorial will walk you through the basic usage of the {{project_name}} command-line interface.

## Prerequisites

- {{project_name}} installed (`pip install {{project_slug}}`)

## Verifying Installation

First, check that {{project_name}} is installed correctly:

```bash
{{project_slug}} --version
```

You should see the current version of {{project_name}} displayed.

## Basic Calculations

### Addition

To add two numbers, use the `calculate add` command:

```bash
{{project_slug}} calculate add 5 3
```

Output:
```
5 + 3 = 8
```

### Subtraction

To subtract one number from another, use the `calculate subtract` command:

```bash
{{project_slug}} calculate subtract 10 4
```

Output:
```
10 - 4 = 6
```

### Sum of Multiple Numbers

To calculate the sum of multiple numbers, use the `calculate sum` command:

```bash
{{project_slug}} calculate sum 1 2 3 4 5
```

Output:
```
1 + 2 + 3 + 4 + 5 = 15
```

## Working with Memory

The calculator has a memory feature that maintains state between commands.

### Adding to Memory

To add a value to memory:

```bash
{{project_slug}} memory add 5
```

Output:
```
Added 5 to memory. New value: 5
```

### Checking Memory Value

To see the current value in memory:

```bash
{{project_slug}} memory show
```

Output:
```
Memory: 5
```

### Subtracting from Memory

To subtract a value from memory:

```bash
{{project_slug}} memory subtract 2
```

Output:
```
Subtracted 2 from memory. New value: 3
```

### Resetting Memory

To reset the memory to zero:

```bash
{{project_slug}} memory reset
```

Output:
```
Memory reset to 0
```

### Viewing Operation History

To see the history of operations performed:

```bash
{{project_slug}} memory history
```

Output:
```
┏━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━┓
┃ Operation  ┃ Value  ┃ Result ┃
┡━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━┩
│ add        │ 5      │ 5      │
│ subtract   │ 2      │ 3      │
│ reset      │ N/A    │ 0      │
└────────────┴────────┴────────┘
```

## Using the Interactive Shell

For continuous calculations, use the interactive shell:

```bash
{{project_slug}} shell
```

In the shell, you can run commands such as:

```
>>> add 5 3
5 + 3 = 8

>>> m+10
Added 10 to memory. New value: 10

>>> memory
Memory: 10

>>> exit
```

## Next Steps

Now that you've learned the basics of the CLI, check out:

- [Working with Calculator Memory](./working-with-memory.md) - For more advanced memory operations
- [Batch Processing of Data Files](./batch-processing.md) - To process multiple numbers from files