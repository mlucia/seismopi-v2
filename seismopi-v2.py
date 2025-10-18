# seismopi.py
# Original code by RR-Inyo (https://github.com/RR-Inyo/seismopi)
# Copyright (c) 2021 RR-Inyo (assumed, based on original repository)
# Modifications by Grok for BMI160 sensor, USGS MMI calculation, and luma.oled library
# Created for personal use or with permission from the original author
# Uses pigpio for I2C, luma.oled for SSD1306 display, and NumPy for data processing

import pigpio
import time
import numpy as np
from BMI160 import BMI160
from usgs_mmi import get_mmi
from luma.oled.device import ssd1306
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.core.virtual import viewport

BUS_OLED    = 11        # I2C bus number for OLED display
SDA_OLED    = 23        # I2C SDA pin for OLED display
SCL_OLED    = 24        # I2C SCL pin for OLED display
ADDR_OLED   = 0x3c      # I2C slave address for OLED display

def main():
    # Initialize pigpio
    pi = pigpio.pi()
    if not pi.connected:
        raise RuntimeError("Cannot connect to pigpio daemon")

    try:
        # Initialize BMI160 on I2C-1 (default hardware I2C, address 0x68)
        imu = BMI160(pi, bus=1, address=0x68)

        # Initialize SSD1306 on bit-bang I2C (e.g., GPIO 23 for SDA, 24 for SCL)
        serial = i2c(port=5, address=0x3C)  # Adjust pins/address as needed
        device = ssd1306(serial, width=128, height=64)
        virtual = viewport(device, width=128, height=64)

        # Sampling parameters
        sample_rate = 100  # Hz (10 ms interval)
        buffer_size = 300  # 3 seconds of data at 100 Hz
        accel_buffer = np.zeros((buffer_size, 3))  # [x, y, z] in gal
        buffer_idx = 0

        print("Seismopi started. Sampling at 100 Hz.")

        while True:
            # Read acceleration
            accel = imu.read_acceleration()  # [x, y, z] in gal
            accel_buffer[buffer_idx % buffer_size] = accel
            buffer_idx += 1

            # Compute MMI when buffer is full
            if buffer_idx >= buffer_size:
                mmi = get_mmi(accel_buffer, sample_rate)
                pga = np.max(np.sqrt(np.sum(accel_buffer**2, axis=1)))  # Peak vector magnitude

                # Update OLED display
                with canvas(virtual) as draw:
                    draw.text((0, 0), f"MMI: {mmi:.1f}", fill="white")
                    draw.text((0, 20), f"PGA: {pga:.1f} gal", fill="white")
                    draw.text((0, 40), "Seismopi Active", fill="white")

            # put the EarthQuake Detected stuff here
            #

            # Maintain 100 Hz sampling (10 ms)
            time.sleep(0.01)


    except KeyboardInterrupt:
        print("Shutting down...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Cleanup
        imu.close()
        pi.stop()

if __name__ == "__main__":
    main()
