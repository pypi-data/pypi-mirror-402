# Configurematic

## Description

Have you found yourself in the situation where you have the same configuration
in multiple configuration files?  We all know config should be in one place
only but sometimes we have several `.env` files, for example, for related apps,
and `env` file for docker plus some configuration in places like
`pyproject.toml`, `package.json`, etc.

Configurematic lets you write a single `.env` file (called `config.env` by
default) and have variable from that file substituted into any other file.  
It is a lightweight, compact script with `python-dotenv` as its only
dependency.

## Installing

Install with

```shell
pip install configurematic
```

Alternatively, install it with `pipx`:

```shell
pipx install configurematic
```

## Using Configurematic

First create your `config.env` file.  An example might be

```shell
APP_NAME="My App Name"
DBPASSWORD="SecretPassword"
```

This is parsed by `dotenv` so you can have blank lines, comments starting
with `#`, etc.

Next create files you want to substitute these into.  Prefix them with
`example-` (though this can be overridden with the `--prefix` option).

For example you might have

`example-env`:

```shell
APP_NAME="__APP_NAME__"
```

`app/example-.env`:

```shell
APP_NAME="__APP_NAME__"
PWD="__DBPASSWORD__"
```

Anything between the `__` pairs is substituted by the variable matching that
name in your `config.env`, provided it exists.

Your `example-*` files don't have to be `.env`-like and can have multiple 
variables on one line, eg

```python
print("The current version is __MAJOR__VERSION__.__MINOR_VERSION__")
```

Variables starting and ending with `__` will only be substituted if they
are in your `config.env` file.

Next, create a file listing your templates (without the `example-` prefix),
one per line:

`files.txt`:

```
env
app/.env
```

This file can also contain blank lines and comments starting with `#`.
Alternatively you can list the files on the command line.  Whitespace at the
start and end of each line though is stripped, therefore filenames cannot
start or end with a whitespace character (not that they should).  Whitespace
inside a filename is fine.  They also cannot start with a `#`, though it can
appear elsewhere in the filename.

If for some reason you do want a space at the beginning or end of a filename
or you do want a file to start with `#`, list the files on the command line
instead of in a file.

Finally, run Configurematic:

```shell
configurematic
```

Next to each of your `example-*` files you will see a new file without
the `example-` prefix.

Run it again and the new files will be overwritten (warning, you will
lose any manual changes) but the old versions will be copied to a new file
next to it with a `.old` suffix (which can be overridden with `--backup-ext`).

## Options

Use `--conf-file` or `-c` to use a different file instead of `config.env`.

Use `--files` or `-f` to use a different file instead of `files.txt`.

To output all the files to a different directory (with the same directory
hierarchy within it), use `--outdir` or `-o`.

Change the prefix with `-p` or `--prefix`.

`-r` or `--recursive` turns on recusion (see below).

Change `__` to something else with `-d` or `--delimeter`.

Change the backup extension with `-b` or `--backup-ext`.  Set this to `""`
to not write backup files.

Turn off verbose output with `-q` or `--silent`.

Instead of listing the files in a file pointed to with `-f`, you can list
them on the command line, eg:

```shell
configurematic env app/.env
```
## Recursion

You can make substitution recursive with the `-r` or `--recursive` flag.

Say you have the following in your `config.env`:

```shell
VAR1="__VAR2__"
VAR2="Value Here"
```

and the following in a template:

```shell
MY_VAR1="__VAR1__"
```

The result will be

```shell
MY_VAR1="Value Here"
```

By default, recursion is off, meaning only one level of substitution is made.

## Changing files

If you edit a generated file, then run Configurematic again, you will lose
your changes (though they are kept in the backup file).  Thus it is best
to edit your `example-*` files only (and of course `config.env`), and rerun 
Configurematic to generate the files again.

## Licence

Configurematic is distributed under the Apache licence.

## Author

Matthew Baker is an IT manager at ETH Zurich.  He also does consultancy work.
Contact him at `matt@mattbaker.ch`.


