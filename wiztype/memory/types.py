from memobj.property import *

from .properties import *


class HashNode(MemoryObject):
    left: "HashNode" = Pointer(0x0, "HashNode")
    parent: "HashNode" = Pointer(0x8, "HashNode")
    right: "HashNode" = Pointer(0x10, "HashNode")
    is_leaf: bool = Bool(0x19)
    hash: int = Signed4(0x20)
    node_data: "Type" = Pointer(0x28, "Type")


class Type(MemoryObject):
    name: str = CppString(0x38)
    hash: int = Signed4(0x58)
    size: int = Signed4(0x60)
    name_2: str = CppString(0x68)
    is_pointer: bool = Bool(0x88)
    if_ref: bool = Bool(0x89)
    property_list: "PropertyList" = Pointer(0x90, "PropertyList")

    _bases = None

    def get_bases(self) -> list["PropertyList"]:
        # so it only needs to be read once
        if self._bases:
            return self._bases

        fields = self.property_list

        if not fields:
            return []

        bases = []
        current_base = fields
        while base_type := current_base.base_class_list:
            bases.append(base_type)
            current_base = base_type

        self._bases = bases
        return bases


class PropertyList(MemoryObject):
    is_singleton: bool = Bool(0x9)
    offset: int = Signed4(0x10)
    base_class_list: "PropertyList" = Pointer(0x18, "PropertyList")
    type: "Type" = Pointer(0x20, "Type")
    pointer_version: "Type" = Pointer(0x30, "Type")
    properties: list["Property"] = SharedVector(0x58, object_type="Property")
    functions: list["Function"] = SharedVector(0x70, object_type="Function")
    name: str = CppString(0xB8, sso_size=10)


class Property(MemoryObject):
    list: "PropertyList" = Pointer(0x38, "PropertyList")
    container: "Container" = Pointer(0x40, "Container")
    index: int = Signed4(0x50)
    name: str = NullTerminatedString(0x58, 100, pointer=True)
    name_hash: int = Signed4(0x60)
    full_hash: int = Signed4(0x64)
    offset: int = Signed4(0x68)
    type: "Type" = Pointer(0x70, "Type")
    flags: int = Signed4(0x80)
    note: str = CppString(0x80)
    ps_info: str = CppString(0x90)
    enum_options = PropertyEnumOptions(0x98)


class Function(MemoryObject):
    list: "PropertyList" = Pointer(0x30, "PropertyList")
    name: str = CppString(0x38)
    details: "FunctionDetails" = Pointer(0x58, "FunctionDetails")


class Container(MemoryObject):
    vtable: int = Unsigned8(0x0)
    name: str = ContainerName(None)
    is_dynamic: bool = ContainerIsDynamic(None)


class FunctionDetails(MemoryObject):
    called_function: int = Unsigned8(0x30)
    something: int = Unsigned4(0x3C)