# This is an example program of how to use the Vaunix LPS-802 DLL
# from python to control a single LPS device

from ctypes import *
import os

this_dir = os.path.abspath("C:\LPS64 SDK")  # <-- Path to file here
# ATTENTION!
# Copy a file containing VNX_dps64.dll to your computer from the USB stick!
# Add the path to the file containing VNX_dps64.dll to line 7!
vnx = cdll.LoadLibrary(os.path.join(this_dir, "VNX_dps64.dll"))
vnx.fnLPS_SetTestMode(False)  # Use actual devices
DeviceIDArray = c_int * 20
Devices = DeviceIDArray()  # This array will hold the list of device handles
# returned by the DLL

# GetNumDevices will determine how many LPS devices are available
numDevices = vnx.fnLPS_GetNumDevices()
print(str(numDevices), ' device(s) found')

# GetDevInfo generates a list, stored in the devices array, of
# every availible LPS device attached to the system
# GetDevInfo will return the number of device handles in the array
dev_info = vnx.fnLPS_GetDevInfo(Devices)
print('GetDevInfo returned', str(dev_info))

# GetSerialNumber will return the devices serial number
ser_num = vnx.fnLPS_GetSerialNumber(Devices[0])
print('Serial number:', str(ser_num))

# InitDevice wil prepare the device for operation
init_dev = vnx.fnLPS_InitDevice(Devices[0])
print('InitDevice returned', str(init_dev))

print()

# These functions will get the working frequency range of the LPS device
# and those frequencies will be turned into MHz
min_freq = vnx.fnLPS_GetMinWorkingFrequency(Devices[0])
max_freq = vnx.fnLPS_GetMaxWorkingFrequency(Devices[0])
min_working_freq_in_MHz = int(min_freq / 10)
max_working_freq_in_MHz = int(max_freq / 10)
print('Minimum working frequency for LPS device in MHz:', min_working_freq_in_MHz)
print('Maximum working frequency for LPS device in MHz:', max_working_freq_in_MHz)

# These functions get the minimum and maximum phase shift for the LPS device
max_angle = vnx.fnLPS_GetMaxPhaseShift(Devices[0])
min_angle = vnx.fnLPS_GetMinPhaseShift(Devices[0])
# This function gives the smallest increment by which the phase shift can be changed
min_step = vnx.fnLPS_GetMinPhaseStep(Devices[0])
print('Minimum phase shift that the Lab Brick is capable of, in degrees:', min_angle)
print('Maximum phase shift that the Lab Brick is capable of, in degrees:', max_angle)
print('Smallest phase shift increment that the Lab Brick is capable of, in degrees:', min_step)

# This is where the user can enter in the working frequency and phase shift for the LPS device
print('Enter desired output frequency in GHz and desired phase shift separated by space:', end='')
freq, angle = input().split()
angle = float(angle)
freq = float(freq)
freq = freq * 1000

# This prevents the user from entering an working frequency outside of
# the devices range
while freq > max_working_freq_in_MHz or freq < min_working_freq_in_MHz:
    print('Enter a value between', min_working_freq_in_MHz / 1000, 'and', max_working_freq_in_MHz / 1000, ': ', end='')
    freq = float(input())
    freq = freq * 1000

Hz = freq * 1000000
frequency = Hz / 100000

# This sets the working frequency for the LPS device
result = vnx.fnLPS_SetWorkingFrequency(Devices[0], int(frequency))
if result != 0:
    print('SetFrequency returned error', result)

print()

# Tis loop prevents the user from entering an angle outside of the device's range
while angle > max_angle or angle < min_angle:
    print('Enter a value between', min_angle, 'and', max_angle, ': ', end='')
    angle = float(input())

# This sets the phase shift for the LPS device
result_1 = vnx.fnLPS_SetPhaseAngle(Devices[0], int(angle))
if result_1 != 0:
    print('SetPhaseAngle returned error', result_1)

print()

# These two functions get the working frequency and the phase shift of the LPS device
result = vnx.fnLPS_GetWorkingFrequency(Devices[0])
if result < 0:
    print('GetWorkingFrequency returned an error', result)
result_1 = vnx.fnLPS_GetPhaseAngle(Devices[0])
if result_1 < 0:
    print('GetPhaseAngle returned an error', result_1)

freq = ((result * 100000) / 1000000) / 1000
angle = result_1

print('Working frequency in GHz for the LPS device:', freq)
print('Phase shift for LPS device:', angle)

# This function closes the device
# You should always close the device when finished with it
closedev = vnx.fnLPS_CloseDevice(Devices[0])
if closedev != 0:
    print('CloseDevice returned an error', closedev)
