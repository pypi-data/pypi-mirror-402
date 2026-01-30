QuickOPC
========
<a href="https://www.opclabs.com/products/quickopc">
<img align="right" src="https://raw.githubusercontent.com/OPCLabs/QuickOPC/main/Image-Product-QuickOPC-Web.png">
</a>

- NuGet package: [**OpcLabs.QuickOpc**](https://www.nuget.org/packages/OpcLabs.QuickOpc)
- Python package: [**opclabs_quickopc**](https://pypi.org/project/opclabs-quickopc/)

QuickOPC is a suite of OPC Client/Subscriber development components for .NET,
COM and Python. The components are for *OPC Unified Architecture* 
(including *OPC UA PubSub*), *OPC "Classic"* (COM/DCOM-based) and 
*OPC XML-DA* specifications.

Note: For OPC Server development, see [OPC Wizard](https://www.opclabs.com/products/opc-wizard).

QuickOPC is a commercially licensed product. Without a license key, it runs 
in a trial mode. The trial provides valid data to client or subscriber 
applications for 30 minutes; after that period, the component (your app) 
needs to be re-started, and so on. You must also comply with licensing terms 
for 3rd-party material redistributed with QuickOPC. For details, see the 
documentation.

| Ready to purchase? See [full price list](https://www.opclabs.com/purchase/full-price-list), or [contact us](https://www.opclabs.com/home/contact). |
| ------------------------------------------------------------------------ |
| Want a U.S.-based vendor? Get [OPC Data Client](https://softwaretoolbox.com/opc-data-client/opc-ua-da-ae-xmlda-client-development-toolkit) (same product) from Software Toolbox. |

Remember that NuGet or Python packages are primarily a tool for resolving 
build-time dependencies. The amount of functionality that you get through 
QuickOPC NuGet or Python packages is smaller than what QuickOPC can actually 
do for you. If you want a full coverage of the features, you would be better 
off downloading the Setup program from [OPC Labs Web site](https://www.opclabs.com). 
Further below you will find a list of differences between the two 
distribution forms.

QuickOPC requires **.NET Framework** 4.7.2 or **.NET** 8.0 as a minimum. Under 
.NET 8.0+, it is supported on **Linux**, **macOS** and **Microsoft Windows**. 
QuickOPC can also be easily used from **Python**.

PLEASE DO NOT USE PRE-RELEASE PACKAGES UNLESS INSTRUCTED TO DO SO.

Need help, **tech support**, or missing some example? Ask us for it on our 
[Online Forums](https://www.opclabs.com/forum/index)!
You *do not have to own a commercial license* in order to use Online Forums, 
and we *reply to every post*.

Follow us on [X (Twitter)](https://x.com/opclabs) | Follow us on [LinkedIn](https://linkedin.com/company/opc-labs)

List of available NuGet / Python packages
-----------------------------------------
- **OpcLabs.QuickOpc / opclabs_quickopc**: OPC client and subscriber 
components for all environments and project types.
- **OpcLabs.QuickOpc.Forms**: Components that are specific for Windows Forms 
(can be partially used from WPF as well).

- **OpcLabs.ConnectivityStudio.Sample.CS**: Console-based OPC Wizard and QuickOPC 
examples in C# (source code).
- **OpcLabs.ConnectivityStudio.Sample.VB**: Console-based OPC Wizard and QuickOPC 
examples in VB.NET (source code).
  
What is included in the NuGet / Python packages
-----------------------------------------------
- Runtime assemblies for all OPC specifications and programming models.
- OPC browsing dialogs and browsing controls for Windows Forms.
- NuGet: IntelliSense support (XML comments).
- NuGet: LINQPad examples.

What is only available from the [Setup program](https://www.opclabs.com/download)
---------------------------------------------
- Support for COM development (VB6, PHP, Excel, Delphi and similar tools).
- Visual Studio integration, including Live Binding design-time support (codeless creation of OPC applications).
- Complete set of Examples and Demo applications, bonus material.
- OPC Data Access simulation server, various tools.

What is only available from the [Setup program](https://www.opclabs.com/download) or the Web site
-------------------------------------------------------------
[Knowledge Base link - Tool Downloads](https://kb.opclabs.com/Tool_Downloads)
- Various tools, such as Connectivity Explorer, Launcher, OPC UA Demo Publisher, OpcCmd Utility, UA Configuration Tool.
- License Manager (GUI or console-based) utility.

How to start
------------
If you do not mind reading the documentation: [Getting Started with QuickOPC](
https://opclabs.doc-that.com/files/onlinedocs/OPCLabs-ConnectivityStudio/Latest/User%27s%20Guide%20and%20Reference-Connectivity%20Software/webframe.html#Getting%20Started%20with%20QuickOPC.html).
Or, the whole [User's Guide](https://www.opclabs.com/documentation).

Otherwise, just instantiate one of the following objects (depending on the 
OPC specification), and explore its methods:

- `OpcLabs.EasyOpc.DataAccess.EasyDAClient` (for OPC DA, OPC XML-DA Client development)
- `OpcLabs.EasyOpc.AlarmsAndEvents.EasyAEClient` (for OPC A&E Client development)
- `OpcLabs.EasyOpc.UA.EasyUAClient` (for OPC UA Client development)
- `OpcLabs.EasyOpc.UA.PubSub.EasyUASubscriber` (for OPC UA Subscriber development)

Example code
------------
C#:
```csharp
using OpcLabs.EasyOpc.UA;
...

var client = new EasyUAClient();
object value = client.ReadValue(
    "opc.tcp://opcua.demo-this.com:51210/UA/SampleServer",
    "nsu=http://test.org/UA/Data/ ;i=10853");
```

Python:
```python
import opclabs_quickopc
from OpcLabs.EasyOpc.UA import *

client = EasyUAClient()
value = IEasyUAClientExtension.ReadValue(client,
                                         UAEndpointDescriptor('opc.tcp://opcua.demo-this.com:51210/UA/SampleServer'),
                                         UANodeDescriptor('nsu=http://test.org/UA/Data/ ;i=10853'))
```

Examples on GitHub
------------------
As opposed to the sample NuGet packages, the examples on GitHub also include 
Web, Windows Forms, Windows Service and WPF projects.

- In C#: https://github.com/OPCLabs/Examples-ConnectivityStudio-CSharp.
- In Python: https://github.com/OPCLabs/Examples-ConnectivityStudio-Python .
- In VB.NET: https://github.com/OPCLabs/Examples-ConnectivityStudio-VBNET.

QuickOPC examples not using the package technology:

- In Object Pascal (Delphi): https://github.com/OPCLabs/Examples-ConnectivityStudio-OP
- In PowerShell: https://github.com/OPCLabs/Examples-ConnectivityStudio-PowerShell
- In PHP: https://github.com/OPCLabs/Examples-ConnectivityStudio-PHP
- In VB6: https://github.com/OPCLabs/Examples-ConnectivityStudio-VB
- In VBScript: https://github.com/OPCLabs/Examples-ConnectivityStudio-VBScript

***
