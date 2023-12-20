import pyvisa
import numpy as np


class BaseVisa:

    def __init__(self, device_address):
        rm = pyvisa.ResourceManager()
        if isinstance(device_address, int):
            device_num = int(device_address)
            device = rm.open_resource(f"GPIB0::{device_num}::INSTR", write_termination=termination_char)
        elif isinstance(device_address, str):
            addr = str(device_address)
            device = rm.open_resource(addr)
        else:
            raise ValueError('Invalid device initialization, please provide GPIB num or device address.')
        self.device = device

    def __error_message(self):
        print('Check that device is connected, visible in NI MAX and is not used by another software.')

    def write(self, cmd_str):
        """
        Base Visa command. Writes string command to the device.
        Args:
            cmd_str: command (string)

        Returns: NONE

        """
        device = self.device
        try:
            device.write(cmd_str)
        except pyvisa.VisaIOError as e:
            print('Unable to connect device.\n', e)
            self.__error_message()

    def read(self):
        """
        Base Visa command. Reads string response from the device.
        Returns: response (string)

        """
        device = self.device
        try:
            resp = device.read()
        except pyvisa.VisaIOError as e:
            print('Unable to connect device.\n', e)
            self.__error_message()
        return resp

    def query(self, cmd_str):
        """
        Base Visa command. Writes string command to the device and reads the response.

        Args:
            cmd_str: command (string)

        Returns: response (string)

        """
        device = self.device
        try:
            resp = device.query(cmd_str)
            return resp
        except Exception as e:
            print('Unable to connect device.\n', e)
            self.__error_message()
            return ""

    def query_float(self, cmd_str):
        """
        2nd order command. Same as 'query', but converts response to flat
        Args:
            cmd_str: command (string)

        Returns: response (float)

        """
        device = self.device
        resp = ""
        try:
            resp = device.query(cmd_str)
            num = np.float64(resp)
            return num
        except pyvisa.VisaIOError as e:
            print('Unable to read data from device.\n', e)
            self.__error_message()
            return 0
        except Exception:
            print('Device returned an invalid responce:', resp)

    def query_int(self, cmd_str):
        """
        2nd order command. Same as 'query', but converts response to integer
        Args:
            cmd_str: command (string)

        Returns: response (int)

        """
        device = self.device
        resp = ""
        try:
            resp = device.query(cmd_str)
            num = np.int(resp)
            return num
        except pyvisa.VisaIOError as e:
            print('Unable to read data from device.\n', e)
            self.__error_message()
            return 0
        except Exception:
            print('Device returned an invalid responce:', resp)

    def idn(self):
        """
        Base Visa command queries *IDN?.

        Returns: Name of the device if connection exist

        """
        try:
            print("Connection exist:", self.query('*IDN?'))
        except:
            self.__error_message()

