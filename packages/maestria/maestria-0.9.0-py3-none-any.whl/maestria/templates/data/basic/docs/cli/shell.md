# Interactive Shell

The interactive shell provides a calculator environment where you can perform multiple operations without restarting the command.

## Starting the Shell

```bash
{{project_slug}} shell
```

**Options:**
- `--interactive`, `-i`: Start in interactive mode (optional, shell is interactive by default)

## Available Commands

Once in the shell, you can use the following commands:

### Calculation Commands

- `add X Y`: Add two numbers
- `sub X Y`: Subtract Y from X
- `sum X Y ...`: Calculate the sum of multiple numbers

### Memory Commands

- `memory`: Show the current memory value
- `m+X`: Add X to memory
- `m-X`: Subtract X from memory
- `mr`: Reset memory to zero
- `history`: Show operation history

### Utility Commands

- `help`: Display a list of available commands
- `exit` or `quit`: Exit the shell

## Example Session

```
$ {{project_slug}} shell
{{project_name}} Interactive Shell
Type 'help' for a list of commands, 'exit' to quit
>>> help
Available commands:
  add X Y     - Add two numbers
  sub X Y     - Subtract Y from X
  sum X Y ... - Calculate sum of numbers
  memory      - Show current memory value
  m+X         - Add X to memory
  m-X         - Subtract X from memory
  mr          - Reset memory to zero
  history     - Show operation history
  exit        - Exit the shell

>>> add 5 3
5 + 3 = 8

>>> m+10
Added 10 to memory. New value: 10

>>> memory
Memory: 10

>>> m-3
Subtracted 3 from memory. New value: 7

>>> history
┏━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━┓
┃ Operation  ┃ Value  ┃ Result ┃
┡━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━┩
│ add        │ 10     │ 10     │
│ subtract   │ 3      │ 7      │
└────────────┴────────┴────────┘

>>> mr
Memory reset to 0

>>> sum 1 2 3 4 5
1 + 2 + 3 + 4 + 5 = 15

>>> exit
```