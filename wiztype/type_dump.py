import json
from pathlib import Path


from wiztype.memory import HashNode, Type, Property


class TypeDumper:
    def __init__(self, type_tree: dict[str, HashNode]):
        self.type_tree = type_tree

    def dump(self, output_file: str | Path):
        output = ""
        for formatted_class in self.class_loop(self.type_tree):
            output += formatted_class

        self.output(output_file, output)

    def class_loop(self, type_tree):
        for name, node in type_tree.items():
            data = node.node_data

            formatted_properties = []

            if property_list := data.property_list:
                for property_ in property_list.properties:
                    formatted_enum_options = []
                    if (enum_options := property_.enum_options) is not None:
                        for enum_option_name, enum_option_value in enum_options.items():
                            formatted_enum_options.append(
                                self.format_enum_option(
                                    enum_option_name, enum_option_value
                                )
                            )

                    property_name, property_info = self.get_property_info(
                        property_
                    )

                    formatted_properties.append(
                        self.format_property(
                            property_name, property_info, formatted_enum_options
                        )
                    )

            base_names, class_hash = self.get_class_info(data)
            formatted_class = self.format_class(
                name, base_names, class_hash, formatted_properties
            )

            yield formatted_class

    @staticmethod
    def output(output_file, output):
        with open(output_file, "w+") as fp:
            fp.write(output)

    @staticmethod
    def get_class_info(node_data: Type):
        bases = node_data.get_bases()
        # & 0xFFFF_FFFF makes it unsigned
        class_hash = node_data.hash & 0xFFFF_FFFF
        return [base.name for base in bases], class_hash

    @staticmethod
    def get_property_info(property_: Property):
        property_name = property_.name
        property_type = property_.type

        container = property_.container
        property_list = property_.list

        property_info = {
            "type": property_type.name,
            "id": property_.index,
            "offset": property_.offset,
            "flags": property_.flags,
            "container": container.name,
            "dynamic": container.is_dynamic,
            "singleton": property_list.is_singleton,
            "pointer": property_type.is_pointer,
            # & 0xFFFF_FFFF makes the value unsigned
            "hash": property_.full_hash & 0xFFFF_FFFF,
        }

        return property_name, property_info

    def format_enum_option(self, name: str, value: int):
        raise NotImplemented()

    def format_property(
        self, name: str, info: dict[str, str], enum_options: list[str]
    ):
        raise NotImplemented()

    def format_class(
        self, name: str, base_names: list[str], class_hash: int, properties: list[str]
    ):
        raise NotImplemented()


class JsonTypeDumperV1(TypeDumper):
    @staticmethod
    def output(output_file, output, indent: int | None = None):
        with open(output_file, "w+") as fp:
            json.dump(output, fp, indent=indent)

    def dump(self, output_file: str | Path, *, indent: int | None = None):
        output = {}
        for formatted_class in self.class_loop(self.type_tree):
            output.update(formatted_class)

        self.output(output_file, output, indent)

    def format_enum_option(self, name: str, value: str):
        return {name: value}

    def format_property(
        self, name: str, info: dict[str, str], enum_options: list[dict]
    ):
        res = {name: info}

        if enum_options:
            options = {}

            for enum_dict in enum_options:
                options.update(enum_dict)

            # noinspection PyTypeChecker
            res[name]["enum_options"] = options

        return res

    def format_class(
        self, name: str, base_names: list[str], class_hash: int, properties: dict
    ):
        props = {}

        for prop in properties:
            props.update(prop)

        return {name: {"bases": base_names, "hash": class_hash, "properties": props}}


class JsonTypeDumperV2(JsonTypeDumperV1):
    version = 2

    def dump(self, output_file: str | Path, *, indent: int | None = None):
        output = {
            "version": self.version,
            "classes": {},
        }
        for formatted_class in self.class_loop(self.type_tree):
            output["classes"].update(formatted_class)

        self.output(output_file, output, indent)

    def format_enum_option(self, name: str, value: int | str):
        try:
            return {name: int(value) & 0xFFFF_FFFF}
        except ValueError:
            return {name: value}

    def format_property(
        self, name: str, info: dict[str, str], enum_options: list[dict]
    ):
        res = {name: info}

        if enum_options:
            options = {}

            for enum_dict in enum_options:
                options.update(enum_dict)

            # noinspection PyTypeChecker
            res[name]["enum_options"] = options

        return res

    def format_class(
        self, name: str, base_names: list[str], class_hash: int, properties: dict
    ):
        props = {}

        for prop in properties:
            props.update(prop)

        return {
            str(class_hash): {
                "name": name,
                "bases": base_names,
                "hash": class_hash,
                "properties": props,
            }
        }


if __name__ == "__main__":
    from wiztype.type_tree import get_type_tree

    tree = get_type_tree()
    dumper = JsonTypeDumperV2(tree)

    dumper.dump("output.json", indent=None)
