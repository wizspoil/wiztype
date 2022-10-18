# wiztype
A type dumper for wizard101

## install
`pip install wiztype`

## usage
an instance of wizard101 must be open for all commands

```shell
# generate a normal dump in the current directory named after the current revision
$ wiztype
# generate a dump with indent level 4 (for human reading)
$ wiztype --indent 4
# generate a version 1 dump (wizwalker)
$ wiztype --version 1 --indent 4
```

## support
discord: https://discord.gg/2u7bGvhYcJ

## json spec

```json5
{
  "version": 2,
  "classes": {
    "class hash (as string)": {
      "bases": ["class base classes"],
      "name": "class name",
      "singleton": true,
      "properties": {
        "property name": {
          "type": "property type",
          "id": 123,
          "offset": 123,
          "flags": 123,
          "container": "container name",
          "dynamic": true,
          "pointer": true,
          "hash": 123,
          "enum_options": {
            "option name": 123,
            // __DEFAULT is a string
            "__DEFAULT": "option name",
            // __BASECLASS is a string
            "__BASECLASS": "option name",
          }
        }
      }
    }
  }
}
```
