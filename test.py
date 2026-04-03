from smbus import SMBus
import time

lightbus = SMBus(1)  # Create a new I2C bus
i2caddress = 0x39

lightbus.read_byte_data(i2caddress,0x80)


while 1:
    results=lightbus.read_i2c_block_data(i2caddress,0x94,4)
    light_data=results[1]+results[2]*0x100+results[3]*0x10000
    print(light_data)
    time.sleep(2)

    
