from typing import Any

from iced_x86 import Decoder, Instruction, Code, Register, MemoryOperand
from memobj import MemoryProperty, MemoryObject


class CppString(MemoryProperty):
    def __init__(self, offset: int | None, encoding: str = "utf-8", sso_size: int = 16):
        super().__init__(offset)
        self.encoding = encoding
        self.sso_size = sso_size

    def from_memory(self) -> Any:
        length = self.memory_object.memobj_process.read_formatted(
            self.memory_object.base_address + self.offset + 16,
            "i",
        )

        if length >= self.sso_size:
            if self.memory_object.memobj_process.process_64_bit:
                pointer_format = "Q"
            else:
                pointer_format = "I"

            address = self.read_formatted_from_offset(pointer_format)

        else:
            address = self.memory_object.base_address + self.offset

        try:
            return self.memory_object.memobj_process.read_memory(address, length).decode(self.encoding)
        except UnicodeDecodeError:
            return ""

    def to_memory(self, value: Any):
        raise NotImplementedError()

    def memory_size(self) -> int:
        return 32


# TODO rework this into a MemoryObject
class SharedVector(MemoryProperty):
    def __init__(
            self,
            offset: int | None,
            max_size: int = 500,
            object_type: type[MemoryObject] | str | None = None,
    ):
        super().__init__(offset)
        self.max_size = max_size
        self.object_type = object_type

    def from_memory(self) -> Any:
        start = self.read_formatted_from_offset(self.pointer_format_string)
        end = self.memory_object.memobj_process.read_formatted(
            self.memory_object.base_address + 8 + self.offset,
            self.pointer_format_string
        )

        size = end - start
        element_number = size // 16

        # less than 0 on dealloc
        if size <= 0:
            return []

        if element_number > self.max_size:
            raise ValueError(f"Size was {element_number} and the max was {self.max_size}")

        element_data = self.memory_object.memobj_process.read_memory(start, size)

        pointers = []
        data_position = 0
        for _ in range(element_number):
            pointers.append(int.from_bytes(element_data[data_position:data_position+8], "little", signed=False))
            # 8 byte pointer, 8 byte ref data*
            data_position += 16

        if self.object_type is None:
            return pointers

        if isinstance(self.object_type, str):
            typed_object_type = MemoryObject.__memory_object_instances__.get(self.object_type)

            if typed_object_type is None:
                raise ValueError(f"No MemoryObject type named {self.object_type}")

            self.object_type = typed_object_type

        objects = []
        for pointer in pointers:
            objects.append(self.object_type(
                address=pointer,
                process=self.memory_object.memobj_process,
            ))

        return objects

    def to_memory(self, value: Any):
        pass

    def memory_size(self) -> int:
        pointer_size = 8 if self.memory_object.memobj_process.process_64_bit else 4
        return pointer_size * 3


class PropertyEnumOptions(MemoryProperty):
    def read_cpp_string(self, address: int, *, sso_size: int = 16, encoding: str = "utf-8"):
        length = self.memory_object.memobj_process.read_formatted(
            address + 16,
            "I",
        )

        if length >= sso_size:
            if self.memory_object.memobj_process.process_64_bit:
                pointer_format = "Q"
            else:
                pointer_format = "I"

            address = self.memory_object.memobj_process.read_formatted(address, pointer_format)

        else:
            address = address

        try:
            return self.memory_object.memobj_process.read_memory(address, length).decode(encoding)
        except UnicodeDecodeError:
            return ""

    def from_memory(self) -> Any:
        start = self.read_formatted_from_offset(self.pointer_format_string)

        if start == 0:
            return None

        end = self.memory_object.memobj_process.read_formatted(
            self.memory_object.base_address + 0xA0,
            self.pointer_format_string
        )

        total_size = end - start

        current = start
        enum_opts = {}
        for entry in range(total_size // 0x48):
            name = self.read_cpp_string(current + 0x28)

            # TODO: int variants are always returned as string
            if string_value := self.read_cpp_string(current):
                enum_opts[name] = string_value
            else:
                enum_opts[name] = self.memory_object.memobj_process.read_formatted(
                    current + 0x20, "I"
                )

            current += 0x48

        return enum_opts

    def to_memory(self, value: Any):
        raise NotImplementedError()

    def memory_size(self) -> int:
        pointer_size = 8 if self.memory_object.memobj_process.process_64_bit else 4
        return pointer_size * 2


class ContainerName(MemoryProperty):
    def from_memory(self) -> Any:
        # noinspection PyUnresolvedReferences
        vtable = self.memory_object.vtable
        lea_func_addr = self.memory_object.memobj_process.read_formatted(vtable + 0x8, "q")
        name_offset = self.memory_object.memobj_process.read_formatted(lea_func_addr + 3, "i")
        # I need to read a null terminated string, but I can't use my MemoryProperty
        # this is an oversight
        string_bytes = self.memory_object.memobj_process.read_memory(
            lea_func_addr + 7 + name_offset,
            20,
        )

        end = string_bytes.find(b"\x00")

        if end == 0:
            return ""

        if end == -1:
            raise ValueError("No null end")

        return string_bytes[:end].decode()

    def to_memory(self, value: Any):
        raise NotImplementedError()

    # TODO: same as below
    def memory_size(self) -> int:
        return 0


class ContainerIsDynamic(MemoryProperty):
    def from_memory(self) -> Any:
        # noinspection PyUnresolvedReferences
        vtable = self.memory_object.vtable
        get_dynamic_func_addr = self.memory_object.memobj_process.read_formatted(
            vtable + 0x20, self.pointer_format_string
        )

        get_dynamic_bytes = self.memory_object.memobj_process.read_memory(get_dynamic_func_addr, 3)

        decoder = Decoder(64, get_dynamic_bytes)

        xor_al_al = Instruction.create_reg_reg(
            Code.XOR_R8_RM8,
            Register.AL,
            Register.AL
        )
        mov_al_1 = Instruction.create_reg_i32(
            Code.MOV_R8_IMM8,
            Register.AL,
            1
        )

        for instruction in decoder:
            if instruction == xor_al_al:
                return False
            elif instruction == mov_al_1:
                return True
            # Note: ret should never enter here
            else:
                raise RuntimeError(f"Invalid dynamic container instruction: {instruction=}")

    def to_memory(self, value: Any):
        raise NotImplementedError()

    # TODO: this should be a Pointer
    def memory_size(self) -> int:
        return 8
