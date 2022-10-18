from pathlib import Path

import click

import wiztype


@click.command()
@click.argument(
    "outfile",
    type=click.Path(exists=False, dir_okay=False, path_type=Path),
    default="outfile.json"
)
@click.option("--version", type=int, default=2, show_default=True)
@click.option("--indent", type=int, default=None)
def main(outfile: Path, version: int, indent: int | None):
    match version:
        case 1:
            tree = wiztype.get_type_tree()
            dumper = wiztype.JsonTypeDumperV1(tree)

            dumper.dump(outfile, indent=indent)
        case 2:
            tree = wiztype.get_type_tree()
            dumper = wiztype.JsonTypeDumperV2(tree)

            dumper.dump(outfile, indent=indent)
        case _:
            click.echo(f"{version} is not a supported version")


if __name__ == "__main__":
    main()
