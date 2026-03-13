import serial
import time
#class hotplate:
#     def __init__(self):
     
class HotPlate:
    """IKA RET Control Visc Class API
    When creating Must Include a COM port as a string: 'COM2' 
    This is probably super unstable right now
    For Safety Reasons Stir speed and temp set point init to 0
    Variable list:
    1: Temp Setpoint?
    2: Temp Setpoint?
    
    """
    def __init__ (self, port):
        self.ser = serial.Serial(
            port=port,
            parity=serial.PARITY_EVEN,
            timeout=10,
            write_timeout=10,
            xonxoff=False
        )
        self.SetStirSpeed(0)
        self.SetTemp(0)


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
            print("ERROR H2: Something went wrong reading a variable on a hotplate")


    #Stir Functions
    def SetStirSpeed(self, speed):
        """Set Setpoint Stir Speed of hotplate in RPM
        Acceptable ranges: 0; 50-1700"""
        
        if ((speed in range(50, 1700)) or (speed ==0)):
            self.__set_stir_speed = speed
            self._send_command(f"OUT_SP_4 {speed}")
        else:
            print("ERROR H1_S1: Speed Setpoint out of range")

    def GetCurrentStirSpeedSetpoint(self):
        """Returns Current Stir Speed Setpoint"""
        return(self.__set_stir_speed)
    
    def GetCurrentStirSpeed(self):
        """Returns Current Stir Speed"""
        self._send_command("IN_PV_4")

        return(self._read_response())
    
    def StartStir(self):
        """Turn on Stir unit"""
        self._send_command("START_4")

    def StopStir(self):
        """Turn off Stir unit"""
        self._send_command("STop_4")
    
    #Heater Functions
    def StartHeater(self):
        """Turn on heating unit"""
        self._send_command("START_1")

    def StopHeater(self):
        """Turn off heating unit"""
        self._send_command("STOP_1")    

    def SetTemp(self, temperature):
        """Set Setpoint temperature of hotplate in C
        Acceptable ranges: 0-265C"""
        
        if temperature in range(0, 265):
            self.__set_point_temp = temperature
            self._send_command(f"OUT_SP_1 {temperature}")
        else:
            print("ERROR H1_T1: Temperature Setpoint out of range")

    def GetCurrentSetPointTemp(self):
        """Returns Current temperature Setpoint"""
        return(self.__set_point_temp)

    def WaitUntilTemp(self, margin):
        """Measures Temp of hotplate every 10s until within margin of temp
        input: margin"""
        while(self.GetCurrentTemp not in range(self.__set_point_temp - margin,self.__set_point_temp + margin )):
            time.sleep(10)
            print(f"Current Temp: {self.GetCurrentTemp()}")

    def GetCurrentTemp(self):
        """Returns Current Temp"""
        self._send_command("IN_PV_1")

        return(self._read_response())
#Add functions for internal(hotplate) and External temp. sensors.  External is likely more important.