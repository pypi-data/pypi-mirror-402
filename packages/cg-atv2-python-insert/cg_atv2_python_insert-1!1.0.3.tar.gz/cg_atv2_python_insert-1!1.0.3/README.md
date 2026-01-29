# cg_atv2_python_insert

This package provides functionality to parse a Python script, identify specific
'magic comments', and substitute these comments with code from other files.
It's designed to be used in environments where code templates and supplementary
files are involved, such as automated grading or code templating systems.

The script supports command-line interaction, allowing users to specify the
file to be processed. It then reads through the specified Python script, looks
for magic comments in the format `# CG_INSERT filename`, and replaces these
comments with the contents of the referenced file, executing it as part of the
script.

The file to be processed cannot contain any call to `sys.exit()`, `quit()`,
`exit()`, `os._exit()` or any method that raises the `SystemExit` error.
This will raise a `ValueError` if the filled in template is then run.

## Usage:

Run the script from the command line with the filename as an argument.

-   `./example.py`

```python
foo = 4

# CG_INSERT other.py

print (foo+bar)

```

-   `./other.py`

```python
bar = 3
```

Running `python -m cg_atv2_python_insert example.py` results in the following file being generated

-   `./filled_example.py`

```
foo = 4

try:
    exec(compile(open('other.py').read(), 'other.py', 'exec'), globals())
except SystemExit as e:
    raise ValueError("Call not allowed") from e

print (foo+bar)

```

If the filled template is then run, the result printed on screen will be `7`

## Module contains:

-   CLI To generate a python file where each magic comment is substituted by the correct exec call.

# Limitation:

This module is not intended to handle complex substitutions or manage
dependencies between inserted scripts. The magic comment needs to be placed at the top level,
outside of any function or class.
