# Calculate Commands

Commands for performing basic calculations.

## add

Add two numbers together.

```bash
{{project_slug}} calculate add NUMBER1 NUMBER2
```

**Arguments:**
- `NUMBER1`: First number
- `NUMBER2`: Second number

**Example:**
```bash
$ {{project_slug}} calculate add 5 3
5 + 3 = 8
```

## subtract

Subtract one number from another.

```bash
{{project_slug}} calculate subtract NUMBER1 NUMBER2
```

**Arguments:**
- `NUMBER1`: First number
- `NUMBER2`: Second number to subtract from the first

**Example:**
```bash
$ {{project_slug}} calculate subtract 10 4
10 - 4 = 6
```

## sum

Calculate the sum of multiple numbers.

```bash
{{project_slug}} calculate sum NUMBER...
```

**Arguments:**
- `NUMBER...`: One or more numbers to sum

**Example:**
```bash
$ {{project_slug}} calculate sum 1 2 3 4 5
1 + 2 + 3 + 4 + 5 = 15
```