from ..base_controller import BaseController


class OrientalMotorsBaseController(BaseController):
    @staticmethod
    def pack_values(values: int | list[int]):
        """Pack a list of 32-bit integers into a list of 16-bit integers."""
        packed_values = []
        if isinstance(values, int):
            values = [values]
        for value in values:
            if value < 0:
                value = value & 0xFFFFFFFF  # Convert to unsigned 32-bit

            packed_values.append((value >> 16) & 0xFFFF)  # High word
            packed_values.append(value & 0xFFFF)  # Low word
        return packed_values

    @staticmethod
    def unpack_values(packed_values: list[int]):
        """Unpack a list of 16-bit integers into a list of 32-bit integers."""
        if len(packed_values) % 2 != 0:
            raise ValueError('Packed values must be an even number of elements.')
        unpacked_values: list[int] = []
        for i in range(0, len(packed_values), 2):
            high_word = packed_values[i]
            low_word = packed_values[i + 1]
            value = (high_word << 16) | low_word

            # convert from unsigned 32-bit to signed 32-bit
            if value & 0x80000000:
                value = value - 0x100000000

            unpacked_values.append(value)
        if len(unpacked_values) == 1:
            return unpacked_values[0]
        return unpacked_values

    def _get_register_int32(
        self, unit_address: int, register_address: int, num_values: int = 1
    ):
        """Read a 32-bit value from two consecutive 16-bit registers."""
        result = self.connection.read_holding_registers(
            unit_address=unit_address,
            register_address=register_address,
            num_registers=2 * num_values,
        ).result()

        if result.isError():
            raise RuntimeError(f'Error reading register {register_address}: {result}')

        return self.unpack_values(result.registers)

    def _set_register_int32(
        self, unit_address: int | list[int], register_address: int, value: int
    ):
        """Write a 32-bit value to two consecutive 16-bit registers."""
        packed_values = self.pack_values(value)
        return self.connection.write_holding_registers(
            unit_address=unit_address,
            register_address=register_address,
            values=packed_values,
        )
