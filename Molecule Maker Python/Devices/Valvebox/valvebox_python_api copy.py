import ctypes
import clr
import subprocess
from subprocess import *
import os
import sys
clr.AddReference('.\Devices\Valvebox\ValveModule_DLL')
from ValveModule_DLL import ValveMod
#test = ValveMod()
#test.Initialize(1,1)
#Contains Constructor for Default valves (starting address 1, 24 ports)
#Is used over importing DLL to all other files for clealiness and Customizable exceptions

import time
import serial
import serial.tools.list_ports



class ValveData:
    """Dataclass equivalent to represent individual valve status."""
    def __init__(self):
        self.is_present: bool = False
        self.current_port: int = 0
        self.port_count: int = 0
        self.initialization_port: int = 0


class ValveMod:
    def __init__(self, port_name: str = "COM1", baud_rate: int = 38400):
        # 1-indexed to match C# logic (indexes 0 to 24, using 1..24)
        self.valve = [ValveData() for _ in range(25)]
        
        self.total_modules: int = 0
        self.communications_is_open: bool = False
        self.in_test_mode: bool = False
        self.reentrance_time: float = 0.0
        
        # Serial Port Configuration
        self.port_name: str = port_name
        self.baud_rate: int = baud_rate
        self.serial_port: serial.Serial | None = None

    @property
    def test_mode(self) -> bool:
        return self.in_test_mode

    @test_mode.setter
    def test_mode(self, value: bool):
        self.in_test_mode = value

    def get_port_position(self, address: int) -> int:
        return self.valve[address].current_port

    def get_port_count(self, address: int) -> int:
        return self.valve[address].port_count

    def get_initialization_port(self, address: int) -> int:
        return self.valve[address].initialization_port

    def set_initialization_port(self, address: int, value: int):
        self.save_configuration(address, self.valve[address].port_count, value)

    def initialize(self, number_of_modules: int, first_address: int) -> bool:
        self.total_modules = number_of_modules
        
        if not self.communications_is_open:
            self.communications_is_open = self._open_communications(first_address)
            if not self.communications_is_open:
                print("Communications was not opened with the J-KEM Valve Module.")

        found_count = 0
        if self.communications_is_open:
            for i in range(first_address, 25):
                if self._test_connection(i):
                    found_count += 1
                    config = self._get_configuration(i)
                    self.valve[i].port_count = config & 0x0F
                    self.valve[i].initialization_port = (config >> 4) & 0x0F

                    if (self.valve[i].initialization_port == 0 or 
                        self.valve[i].initialization_port > 12 or 
                        self.valve[i].port_count == 0 or 
                        self.valve[i].port_count > 12):
                        self._close_port()
                        print(f"Error testing Port Status. Module message: {i}")
                        return False

                    if not self._jkem_check(i):
                        self._close_port()
                        print(f"Error. Valve current exceeds allowed limit. Module message: {i}")
                        return False

                    self.port(i, self.valve[i].initialization_port, wait_for_ready=False)
                    if found_count == number_of_modules:
                        break

        return self.communications_is_open

    def _jkem_check(self, address: int) -> bool:
        cmd = bytearray(8)
        cmd[0] = 204
        cmd[1] = address & 0xFF
        cmd[2] = 35
        cmd[3] = 0
        cmd[4] = 0
        cmd[5] = 221
        
        checksum = self._get_checksum(cmd, 6)
        cmd[6] = checksum[0]
        cmd[7] = checksum[1]

        resp = self._send(address, cmd, wait_for_ready=False)
        return resp[0] != 0 and resp[3] == 3

    def _open_communications(self, address: int) -> bool:
        if self.in_test_mode:
            self.communications_is_open = True
            return True

        # Attempt to open default port
        try:
            self._connect_serial(self.port_name)
            if self._test_connection(address):
                self.communications_is_open = True
                return True
            else:
                self._close_port()
        except Exception:
            self._close_port()

        # Search available serial ports if initial connection fails
        if not self.communications_is_open and serial is not None:
            ports = [p.device for p in serial.tools.list_ports.comports()]
            for p_name in ports:
                try:
                    self._connect_serial(p_name)
                    if self._test_connection(address):
                        self.communications_is_open = True
                        self.port_name = p_name
                        break
                    self._close_port()
                except Exception:
                    self._close_port()

        return self.communications_is_open

    def _test_connection(self, address: int) -> bool:
        if self.in_test_mode:
            return True

        cmd = bytearray(8)
        cmd[0] = 204
        cmd[1] = address & 0xFF
        cmd[2] = 63
        cmd[3] = 0
        cmd[4] = 0
        cmd[5] = 221
        
        checksum = self._get_checksum(cmd, 6)
        cmd[6] = checksum[0]
        cmd[7] = checksum[1]

        for _ in range(3):
            resp = self._send(address, cmd, wait_for_ready=False)
            if resp[2] == 0:
                return True
            time.sleep(0.1)

        return False

    def _get_configuration(self, address: int) -> int:
        cmd = bytearray(8)
        cmd[0] = 204
        cmd[1] = address & 0xFF
        cmd[2] = 48
        cmd[3] = 0
        cmd[4] = 0
        cmd[5] = 221
        
        checksum = self._get_checksum(cmd, 6)
        cmd[6] = checksum[0]
        cmd[7] = checksum[1]

        resp = self._send(address, cmd, wait_for_ready=False)
        if resp[0] != 0 and resp[2] == 0:
            return resp[3]
        return 0

    def save_configuration(self, address: int, port_count: int, init_port: int):
        val = (init_port << 4) + port_count
        cmd = bytearray(14)
        cmd[0] = 204
        cmd[1] = address & 0xFF
        cmd[2] = 16
        cmd[3] = 255
        cmd[4] = 238
        cmd[5] = 187
        cmd[6] = 170
        cmd[7] = val & 0xFF
        cmd[8] = 0
        cmd[9] = 0
        cmd[10] = 0
        cmd[11] = 221

        checksum = self._get_checksum(cmd, 12)
        cmd[12] = checksum[0]
        cmd[13] = checksum[1]

        self._send(address, cmd, wait_for_ready=False)
        self.valve[address].initialization_port = init_port
        self.valve[address].port_count = port_count

    def _send(self, address: int, command: bytearray, wait_for_ready: bool = True) -> bytearray:
        if self.in_test_mode:
            return bytearray([204, 1, 0, 0, 0, 221, 232, 1])

        # Ensure delay between consecutive commands
        now = time.time()
        if now < self.reentrance_time:
            time.sleep(self.reentrance_time - now)

        response = bytearray(8)
        try:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.reset_input_buffer()
                self.serial_port.reset_output_buffer()
                self.serial_port.write(command)

                # Wait for response (up to 1 second timeout)
                end_time = time.time() + 1.0
                while time.time() < end_time:
                    if self.serial_port.in_waiting >= 8:
                        response = bytearray(self.serial_port.read(8))
                        break
                    time.sleep(0.01)
        except Exception as ex:
            print(f"Communication error: {ex}")

        if wait_for_ready and not self._wait_for_motion_complete(address):
            print(f"Valve module #{address} failed to reach the correct port.")

        self.reentrance_time = time.time() + 0.1  # 100 ms spacing
        return response

    def is_ready(self, address: int) -> bool:
        cmd = bytearray(8)
        cmd[0] = 204
        cmd[2] = 74
        cmd[3] = 0
        cmd[4] = 0
        cmd[5] = 221

        if address > 0:
            cmd[1] = address & 0xFF
            checksum = self._get_checksum(cmd, 6)
            cmd[6] = checksum[0]
            cmd[7] = checksum[1]
            resp = self._send(address, cmd, wait_for_ready=False)
            return resp[2] == 0
        else:
            for i in range(1, self.total_modules + 1):
                if self.valve[i].is_present:
                    cmd[1] = i & 0xFF
                    checksum = self._get_checksum(cmd, 6)
                    cmd[6] = checksum[0]
                    cmd[7] = checksum[1]
                    resp = self._send(address, cmd, wait_for_ready=False)
                    if resp[2] != 0:
                        return False
            return True

    def _wait_for_motion_complete(self, address: int) -> bool:
        cmd = bytearray(8)
        cmd[0] = 204
        cmd[1] = address & 0xFF
        cmd[2] = 74
        cmd[3] = 0
        cmd[4] = 0
        cmd[5] = 221
        
        checksum = self._get_checksum(cmd, 6)
        cmd[6] = checksum[0]
        cmd[7] = checksum[1]

        end_time = time.time() + 2.0
        while time.time() <= end_time:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.reset_input_buffer()
                self.serial_port.reset_output_buffer()
                self.serial_port.write(cmd)

                read_timeout = time.time() + 0.1
                resp = bytearray(8)
                resp[2] = 4  # Default non-zero status

                while time.time() < read_timeout:
                    if self.serial_port.in_waiting >= 8:
                        resp = bytearray(self.serial_port.read(8))
                        break
                    time.sleep(0.005)

                if resp[2] == 0:
                    return True

            time.sleep(0.1)

        return False

    def _get_checksum(self, command: bytearray, bytes_to_sum: int) -> bytearray:
        total = sum(command[:bytes_to_sum])
        checksum = bytearray(2)
        if total >= 256:
            checksum[1] = (total // 256) & 0xFF
            checksum[0] = (total % 256) & 0xFF
        else:
            checksum[1] = 0
            checksum[0] = total & 0xFF
        return checksum

    def port(self, address_or_cmd, port_number: int | None = None, wait_for_ready: bool = True) -> bool:
        """
        Supports both overloads:
        1. port(address: int, port_number: int, wait_for_ready: bool)
        2. port(command_str: str, wait_for_ready: bool)
        """
        # String Command Overload
        if isinstance(address_or_cmd, str):
            cmd_str = address_or_cmd.replace(" ", "")
            pairs = cmd_str.split(";")
            
            cmd = bytearray(8)
            cmd[0] = 204
            cmd[2] = 68
            cmd[4] = 0
            cmd[5] = 221

            for pair in pairs:
                if not pair:
                    continue
                addr_str, port_str = pair.split(",")
                addr, p_num = int(addr_str), int(port_str)

                cmd[1] = addr & 0xFF
                cmd[3] = p_num & 0xFF
                checksum = self._get_checksum(cmd, 6)
                cmd[6] = checksum[0]
                cmd[7] = checksum[1]

                if self.serial_port and self.serial_port.is_open:
                    self.serial_port.reset_input_buffer()
                    self.serial_port.reset_output_buffer()
                    self.serial_port.write(cmd)

                self.valve[addr].current_port = p_num
                time.sleep(0.005)

            if wait_for_ready:
                for pair in pairs:
                    if not pair:
                        continue
                    addr = int(pair.split(",")[0])
                    self._wait_for_motion_complete(addr)

            return True

        # Int Overload
        else:
            address = address_or_cmd
            cmd = bytearray(8)
            cmd[0] = 204
            cmd[1] = address & 0xFF
            cmd[2] = 68
            cmd[3] = port_number & 0xFF
            cmd[4] = 0
            cmd[5] = 221

            checksum = self._get_checksum(cmd, 6)
            cmd[6] = checksum[0]
            cmd[7] = checksum[1]

            resp = self._send(address, cmd, wait_for_ready)
            if resp[2] in (1, 254):
                self.valve[address].current_port = port_number
                return True
            return False

    def query_port_position(self, address: int) -> int:
        cmd = bytearray(8)
        cmd[0] = 204
        cmd[1] = address & 0xFF
        cmd[2] = 62
        cmd[3] = 0
        cmd[4] = 0
        cmd[5] = 221

        checksum = self._get_checksum(cmd, 6)
        cmd[6] = checksum[0]
        cmd[7] = checksum[1]

        resp = self._send(address, cmd, wait_for_ready=False)
        if resp[0] != 0 and resp[2] == 0:
            pos = resp[3]
            self.valve[address].current_port = pos
            return pos
        return 0

    def change_address(self, old_address: int, new_address: int):
        password = input("Enter password: ").strip().upper()
        if password == "PASSWORD":
            cmd = bytearray(14)
            cmd[0] = 204
            cmd[1] = old_address & 0xFF
            cmd[2] = 0
            cmd[3] = 255
            cmd[4] = 238
            cmd[5] = 187
            cmd[6] = 170
            cmd[7] = new_address & 0xFF
            cmd[8] = 0
            cmd[9] = 0
            cmd[10] = 0
            cmd[11] = 221

            checksum = self._get_checksum(cmd, 12)
            cmd[12] = checksum[0]
            cmd[13] = checksum[1]

            self._send(old_address, cmd, wait_for_ready=False)
            if not self._test_connection(new_address):
                cmd[3] = 255

    def _connect_serial(self, port: str):
        if serial is None:
            raise ImportError("pyserial module is not installed.")
        self.serial_port = serial.Serial(
            port=port,
            baudrate=self.baud_rate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.3
        )

    def _close_port(self):
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.communications_is_open = False






class valves:
    def __init__(self):
        self.valve_object = ValveMod()
        self.valves_loaded = False
        
        valves_loaded = self.valve_object.Initialize(1,24)
        if valves_loaded == False:
            sys.exit("ERROR V1: Valves failed to load. \n try plugging in valves first+running to init")
                     
    def set_valve(self, valve, port):
         self.valve_object.Port(valve, port)