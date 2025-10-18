# BMI160.py
# Modified from MPU6050.py by RR-Inyo (https://github.com/RR-Inyo/seismopi)
# Copyright (c) 2021 RR-Inyo (assumed, based on original repository)
# Modifications for BMI160 sensor by Grok, created for personal use or with permission.
# Retains original structure for compatibility with seismopi.py.
# Uses pigpio for I2C communication on Raspberry Pi (i2c-1, address 0x68).

import pigpio
import time
import numpy as np

class BMI160:
    # Register addresses (from BMI160 datasheet)
    REG_ACCEL_CONFIG = 0x40  # Accel data starts here (x, y, z, 6 bytes)
    REG_ACCEL_RANGE = 0x41   # Range selection
    REG_PWR_CONF = 0x7C      # Power control
    REG_PWR_CTRL = 0x7D      # Accelerometer enable
    REG_CHIPID = 0x00        # Chip ID (should be 0xD1 for BMI160)

    def __init__(self, pi, bus=1, address=0x68):
        """
        Initialize BMI160 on I2C bus (default i2c-1, address 0x68).
        pi: pigpio.pi() instance
        bus: I2C bus number (1 for Raspberry Pi default)
        address: I2C address (0x68 if SDO low, 0x69 if high)
        """
        self.pi = pi
        self.bus = bus
        self.address = address
        self.handle = self.pi.i2c_open(self.bus, self.address)
        
        # Verify chip ID
        chip_id = self.pi.i2c_read_byte_data(self.handle, self.REG_CHIPID)
        if chip_id != 0xD1:
            raise RuntimeError(f"BMI160 not detected, chip ID: {chip_id}")

        # Configure sensor
        # Set normal power mode
        self.pi.i2c_write_byte_data(self.handle, self.REG_PWR_CONF, 0x00)
        time.sleep(0.01)
        # Enable accelerometer
        self.pi.i2c_write_byte_data(self.handle, self.REG_PWR_CTRL, 0x04)
        time.sleep(0.01)
        # Set ±2g range (0x03 = ±2g, 16-bit resolution gives 16384 LSB/g)
        self.pi.i2c_write_byte_data(self.handle, self.REG_ACCEL_RANGE, 0x03)
        time.sleep(0.01)

    def read_acceleration(self):
        """
        Read 3-axis acceleration in gal (cm/s^2).
        Returns: NumPy array [x, y, z]
        """
        # Read 6 bytes (x, y, z, 2 bytes each, 16-bit signed)
        data = self.pi.i2c_read_i2c_block_data(self.handle, self.REG_ACCEL_CONFIG, 6)
        if data[0] != 6:
            raise RuntimeError("Failed to read BMI160 acceleration data")

        # Convert to signed 16-bit integers
        x = (data[1][0] | (data[1][1] << 8))
        if x & 0x8000:  # Handle negative values
            x = x - 0x10000
        y = (data[1][2] | (data[1][3] << 8))
        if y & 0x8000:
            y = y - 0x10000
        z = (data[1][4] | (data[1][5] << 8))
        if z & 0x8000:
            z = z - 0x10000

        # Convert to gal (1g = 981 cm/s^2, ±2g range = 16384 LSB/g)
        scale = 981.0 / 16384.0
        return np.array([x * scale, y * scale, z * scale])

    def close(self):
        """Close I2C connection."""
        self.pi.i2c_close(self.handle)