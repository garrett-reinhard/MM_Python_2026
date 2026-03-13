import serial
import time

     
class HotPlate:

    def __init__ (self, port):
        self.ser = serial.Serial(
            port=port,
            baudrate=19200,
            parity=serial.PARITY_EVEN,
            timeout=10,
            write_timeout=10,
            xonxoff=False
        )



    def _send_command(self, output):
        """Sends a command to the Hotplate
        String Does NOT need to be in Byte format"""
        byte_command = bytes(f"{output}\n", encoding="utf-8")
        self.ser.write(byte_command)
        
    def _read_response(self):
        """Read Value returned by hotplate after sending a command"""
        try:
            #Hotplate returns the value AND the variable, this only returns the value
            return(self.ser.readline().decode("utf-8").strip().split()[0])
        except:
            print("ERROR H2: Something went wrong reading a variable")


link = HotPlate("COM2")
link._send_command("DCR")
print(link._read_response())

