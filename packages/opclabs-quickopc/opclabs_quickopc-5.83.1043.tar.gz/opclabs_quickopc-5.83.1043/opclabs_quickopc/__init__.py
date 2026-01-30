
import clr_loader
import os
import platform
import pythonnet
import sys

# The Python.NET bootstrapper code. In the "core" package only.

# Load Python.NET into the specified runtime, if not loaded yet.
if pythonnet.get_runtime_info() is None:
    pythonnetRuntime = os.getenv('PYTHONNET_RUNTIME')
    if (platform.system() != 'Windows') or (pythonnetRuntime == 'coreclr'):
        runtimeName = 'Microsoft.AspNetCore.App'
        candidates = [rt for rt in clr_loader.find_runtimes() if rt.name == runtimeName]
        candidates.sort(key=lambda spec: spec.version, reverse=True)
        if not candidates:
            raise RuntimeError("Failed to find a suitable .NET runtime with name '" + runtimeName + "'.")
        runtimeSpec = candidates[0]
        #print('runtimeSpec:', runtimeSpec)  # for debugging
        pythonnet.load('coreclr', runtime_spec=runtimeSpec)
    else:
        pythonnet.load()

# End of Python.NET bootstrapper code.



# Determine the target network identifier, which is used to construct the assemblies path.
runtimeKind = pythonnet.get_runtime_info().kind
if runtimeKind == '.NET Framework':
    targetFramework = 'net472'
elif runtimeKind == 'CoreCLR':
    targetFramework = 'net8.0'
if targetFramework is None:
    raise RuntimeError('Failed to determine .NET target framework from runtime kind "' + runtimeKind + '".')

filePackageName = 'OpcLabs.QuickOpc'
packagePath = os.path.dirname(os.path.abspath(__file__))
assembliesPath = os.path.join(packagePath, filePackageName, targetFramework)
#print('assembliesPath:', assembliesPath)   # for debugging
sys.path.append(assembliesPath)

import clr  # This must come AFTER loading the Python.NET in the specified runtime.

# Reference the .NET assemblies.
# Source correlation: {3AB6A4D7-52E9-4514-B400-40F29AF98E65}
clr.AddReference('OpcLabs.BaseLib')
clr.AddReference('OpcLabs.BaseLibComponents')
clr.AddReference('OpcLabs.BaseLibForms')
#clr.AddReference('OpcLabs.EasyOpc')    # not needed yet
clr.AddReference('OpcLabs.EasyOpcClassic')
clr.AddReference('OpcLabs.EasyOpcClassicComponents')
clr.AddReference('OpcLabs.EasyOpcClassicCore')
clr.AddReference('OpcLabs.EasyOpcForms')
clr.AddReference('OpcLabs.EasyOpcUA')
clr.AddReference('OpcLabs.EasyOpcUAComponents')

