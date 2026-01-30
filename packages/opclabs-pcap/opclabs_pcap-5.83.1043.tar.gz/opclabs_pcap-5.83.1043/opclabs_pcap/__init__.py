
import os
import pythonnet
import sys

# Make sure Python.NET is loaded.
import opclabs_quickopc

# Determine the target network identifier, which is used to construct the assemblies path.
runtimeKind = pythonnet.get_runtime_info().kind
if runtimeKind == '.NET Framework':
    targetFramework = 'net472'
elif runtimeKind == 'CoreCLR':
    targetFramework = 'net8.0'
if targetFramework is None:
    raise RuntimeError('Failed to determine .NET target framework from runtime kind "' + runtimeKind + '".')

filePackageName = 'OpcLabs.Pcap'
packagePath = os.path.dirname(os.path.abspath(__file__))
assembliesPath = os.path.join(packagePath, filePackageName, targetFramework)
#print(assembliesPath)   # for debugging
sys.path.append(assembliesPath)

import clr  # This must come AFTER loading the Python.NET in the specified runtime.

# Reference the .NET assemblies.
clr.AddReference('OpcLabs.Pcap')

