from memobj.property import *

from .properties import *


class BetterDereffedPointer(DereffedPointer):
    def from_memory_deref(self) -> Any:
        addr = self.from_memory()
        if Pointer.is_null(addr):
            return None

        # circular import bs
        from memobj import MemoryObject
        from memobj.object import MemoryObjectMeta

        if type(self._pointed_type) is MemoryObjectMeta and issubclass(self._pointed_type, MemoryObject):
            return self._pointed_type(address=addr, process=self.memory_object.memobj_process)

        elif isinstance(self._pointed_type, str):
            # noinspection PyProtectedMember
            typed_object_type = MemoryObject._resolve_string_class_lookup(self._pointed_type)
            self._pointed_type = typed_object_type

            return self._pointed_type(address=addr, process=self.memory_object.memobj_process)

        elif isinstance(self._pointed_type, MemoryProperty):
            # create a mock object at the address
            self._pointed_type.memory_object = MemoryObject(
                address=addr,
                process=self.memory_object.memobj_process,
            )
            self._pointed_type.offset = 0

            return self._pointed_type.from_memory()

        else:
            raise TypeError("pointed-to type is neither MemoryObject nor MemoryProperty")


class HashNode(MemoryObject):
    left: "HashNode" = BetterDereffedPointer(0x0, "HashNode")
    parent: "HashNode" = BetterDereffedPointer(0x8, "HashNode")
    right: "HashNode" = BetterDereffedPointer(0x10, "HashNode")
    is_leaf: bool = Bool(0x19)
    hash: int = Signed4(0x20)
    node_data: "Type" = BetterDereffedPointer(0x28, "Type")


class Type(MemoryObject):
    name: str = CppString(0x38)
    hash: int = Signed4(0x58)
    size: int = Signed4(0x60)
    name_2: str = CppString(0x68)
    is_pointer: bool = Bool(0x88)
    if_ref: bool = Bool(0x89)
    property_list: "PropertyList" = BetterDereffedPointer(0x90, "PropertyList")

    def get_bases(self) -> list["PropertyList"]:
        if (fields := self.property_list) is None:
            return []

        bases = []
        current_base = fields
        while (base_type := current_base.base_class_list) is not None:
            bases.append(base_type)
            current_base = base_type

        return bases


class PropertyList(MemoryObject):
    is_singleton: bool = Bool(0x9)
    offset: int = Signed4(0x10)
    base_class_list: "PropertyList" = BetterDereffedPointer(0x18, "PropertyList")
    type: "Type" = BetterDereffedPointer(0x20, "Type")
    pointer_version: "Type" = BetterDereffedPointer(0x30, "Type")
    properties: list["Property"] = SharedVector(0x58, object_type="Property")
    functions: list["Function"] = SharedVector(0x70, object_type="Function")
    name: str = CppString(0xB8, sso_size=10)


class Property(MemoryObject):
    list: "PropertyList" = BetterDereffedPointer(0x38, "PropertyList")
    container: "Container" = BetterDereffedPointer(0x40, "Container")
    index: int = Signed4(0x50)
    name: str = BetterDereffedPointer(0x58, NullTerminatedString(None, search_size=100))
    name_hash: int = Signed4(0x60)
    full_hash: int = Signed4(0x64)
    offset: int = Signed4(0x68)
    type: "Type" = BetterDereffedPointer(0x70, "Type")
    flags: int = Signed4(0x80)
    note: str = CppString(0x80)
    ps_info: str = CppString(0x90)
    enum_options = PropertyEnumOptions(0x98)


class Function(MemoryObject):
    list: "PropertyList" = BetterDereffedPointer(0x30, "PropertyList")
    name: str = CppString(0x38)
    details: "FunctionDetails" = BetterDereffedPointer(0x58, "FunctionDetails")


class Container(MemoryObject):
    vtable: int = Unsigned8(0x0)
    name: str = ContainerName(None)
    is_dynamic: bool = ContainerIsDynamic(None)


class FunctionDetails(MemoryObject):
    called_function: int = Unsigned8(0x30)
    something: int = Unsigned4(0x3C)
