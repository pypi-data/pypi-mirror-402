# Memory Commands

Commands for working with calculator memory.

## add

Add a value to memory.

```bash
{{project_slug}} memory add VALUE
```

**Arguments:**
- `VALUE`: Number to add to memory

**Example:**
```bash
$ {{project_slug}} memory add 5
Added 5 to memory. New value: 5
```

## subtract

Subtract a value from memory.

```bash
{{project_slug}} memory subtract VALUE
```

**Arguments:**
- `VALUE`: Number to subtract from memory

**Example:**
```bash
$ {{project_slug}} memory subtract 2
Subtracted 2 from memory. New value: 3
```

## show

Display the current value in memory.

```bash
{{project_slug}} memory show
```

**Example:**
```bash
$ {{project_slug}} memory show
Memory: 3
```

## reset

Reset the memory to zero.

```bash
{{project_slug}} memory reset
```

**Example:**
```bash
$ {{project_slug}} memory reset
Memory reset to 0
```

## history

Show the history of operations.

```bash
{{project_slug}} memory history
```

**Example:**
```bash
$ {{project_slug}} memory history
┏━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━┓
┃ Operation  ┃ Value  ┃ Result ┃
┡━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━┩
│ add        │ 5      │ 5      │
│ subtract   │ 2      │ 3      │
│ reset      │ N/A    │ 0      │
└────────────┴────────┴────────┘
```