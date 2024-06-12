import serial
from ublox_gps import UbloxGps
import asyncio
import socketio
import json

port = serial.Serial('/dev/serial0', baudrate=38400, timeout=1)
gps = UbloxGps(port)
sio = socketio.AsyncClient()

@sio.event
async def connect():
    print('Connection established')

@sio.event
async def disconnect():
    print('Disconnected from server')
    
async def send_location():
    await sio.connect('http://localhost:5000')

    try:
        print("Listening for UBX Messages")
        while True:
            try:
                veh = gps.veh_attitude()
                geo = gps.geo_coords()
                data = {
                    "longitude": geo.lon,
                    "latitude": geo.lat,
                    "heading": geo.headMot,
                    "Heading": veh.heading,
                    "Rool": veh.roll,
                    "Pitch": veh.pitch,
                    "Roll Acceleration": veh.accRoll,
                    "Pitch Acceleration": veh.accPitch,
                    "Heading Acceleration": veh.accHeading
                    
                }
                print("Sending data:", data)  
                await sio.emit('gps_data', data)
                print("Data sent: ", data)
                await asyncio.sleep(1)  # Add a delay to avoid flooding the server
            except (ValueError, IOError) as err:
                print(err)
    finally:
        await sio.disconnect()
        port.close()


if __name__ == '__main__':
    asyncio.run(send_location())
