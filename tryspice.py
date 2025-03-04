import sys
print("*****************************")
print(sys.path)
print("*****************************")


import spiceypy as spice

"""Prints the TOOLKIT version
"""
print(spice.tkvrsn('TOOLKIT'))
