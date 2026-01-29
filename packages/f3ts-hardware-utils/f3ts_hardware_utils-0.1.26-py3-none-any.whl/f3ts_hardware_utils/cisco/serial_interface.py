"""Cisco Catalyst Managed Ethernet Switch Serial Interface."""
import time

import serial


class CatalystSerialException(Exception):
    """Custom exception class for Cisco errors."""

    pass


class CatalystSerial:
    """Custom class for Cisco Serial Interface."""

    def __init__(
        self,
        username: str,
        password: str,
        port: str = None,
        baudrate: int = 115200,
        bytesize: int = 8,
        parity: str = "N",
        stopbits: int = 1,
        timeout: int = 8,
    ):
        """Cisco Catalyst Switch Serial Interface.

        :param username: Cisco device username
        :type username: str
        :param password: Cisco device password
        :type password: str
        :param port: Serial port to attempt to connect to, defaults to None
        :type port: str, optional
        :param baudrate: Serial baudrate, defaults to 115200
        :type baudrate: int, optional
        :param bytesize: Serial bytesize, defaults to 8
        :type bytesize: int, optional
        :param parity: Serial parity, defaults to "N"
        :type parity: str, optional
        :param stopbits: Serial stopbits, defaults to 1
        :type stopbits: int, optional
        :param timeout: Serial request timeout, defaults to 8 seconds
        :type timeout: int, optional
        """
        if port:
            self.port = port
        else:
            self._auto_discover_and_connect()

        self.console = serial.Serial(
            port=self.port,
            baudrate=baudrate,
            bytesize=bytesize,
            parity=parity,
            stopbits=stopbits,
            timeout=timeout,
        )

        self.username = username
        self.password = password

    def _auto_discover_and_connect(self) -> None:
        """Automatically discover and connect to a Cisco Switch device."""
        ports_list = serial.tools.list_ports.comports()
        ports = [port for port, desc, hwid in ports_list if "0525:A4A7" in hwid]
        print(f"Found these possible serial ports in system {ports}")

        if not ports:
            raise CatalystSerialException("No Cisco Switch devices found in system")
        if len(ports) > 1:
            print("More than one Cisco Switch detected")

        self.port = ports[0]  # Connect to first one

    def write_serial(self, cmd: str):
        """Send command to serial interface.

        :param cmd: command to send to serial interface
        :type cmd: str
        """
        self.console.write(cmd.encode("utf-8"))
        time.sleep(0.25)

    def read_serial(self):
        """Check and return data if there is data waiting to be read."""
        data_bytes = self.console.inWaiting()
        if data_bytes:
            return self.console.read(data_bytes).decode("utf-8")
        else:
            return ""

    def check_logged_in(self):
        """Check if logged in to router."""
        self.write_serial("\r")
        prompt = self.read_serial()
        if ">" in prompt or "#" in prompt:
            return True
        else:
            return False

    def login(self):
        """Login to router."""
        login_status = self.check_logged_in()
        if login_status:
            return "Already logged into cisco router"

        print("Logging into router")
        max_tries = 5
        tries = 0
        while tries < max_tries:
            tries += 1
            self.write_serial("\r")
            input_data = self.read_serial()
            if "User Name" not in input_data:
                continue
            self.write_serial(self.username + "\r")

            input_data = self.read_serial()
            if "Password" not in input_data:
                continue
            self.write_serial(self.password + "\r")

            login_status = self.check_logged_in()
            if login_status:
                break

        if tries >= max_tries:
            return "Unable to log in to Cisco Router"

        return "Succesfully logged into cisco router"

    def logout(self):
        """Exit from self.console session."""
        while self.check_logged_in():
            self.write_serial("exit\r\n")

    def send_command(self, cmd=""):
        """Send a command down the channel."""
        self.write_serial(cmd + "\r")
        output = self.read_serial()

        return output

    def send_commands(self, cmds=""):
        """Send a command down the channel."""
        cmds = cmds.split(",")
        outputs = []
        for cmd in cmds:
            outputs += [self.send_command(cmd)]
        return outputs
