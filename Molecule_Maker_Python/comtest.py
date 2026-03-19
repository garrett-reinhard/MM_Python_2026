import serial.tools.list_ports
import serial, time

for p in serial.tools.list_ports.comports():
    print(p.device, p.description, p.hwid)

ports = [p.device for p in __import__('serial').tools.list_ports.comports()]
for pa in ports:
    try:
        s = serial.Serial(pa, 9600, timeout=1)   # set correct baud
        s.write(b'ping\n')
        time.sleep(0.2)
        data = s.read_all()
        print(pa, 'OK', repr(data))
        s.close()
    except Exception as e:
        print(pa, 'ERR', e)