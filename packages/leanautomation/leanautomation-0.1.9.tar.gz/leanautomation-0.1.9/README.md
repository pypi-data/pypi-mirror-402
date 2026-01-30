# Lean Automation: A Unified SDK for Microsoft Fabric

The Lean Automation packages provides a unified, cross-experience Microsoft Fabric SDK. The goal of Lean Automation is to simplify the way you work with Fabric APIs and support deployments and automation allowing you to focus on solving your business problems.


## Quickstart
Lean Automation is available on [PyPi](https://pypi.org/project/Lean Automation/) and can be installed via `pip install leanautomation`.

With Lean Automation installed, you first authenticate by creating a Fabric client. You can use either [FabricInteractiveAuth](https://learn.microsoft.com/en-us/python/api/azure-identity/azure.identity.interactivebrowsercredential?view=azure-python) to use your personal credentials or `FabricServicePrincipal` to use a service principal (which is supported for most but not all APIs).

```python
from Lean Automation import auth, FabricClient
from Lean Automation.auth import FabricInteractiveAuth

fc = FabricClient(auth=auth.FabricInteractiveAuth())
for ws in fc.workspace.ls():
    print(f"{ws.name}: Id:{ws.id} Capacity:{ws.capacityId}")
```
You use Service Principals in a similar way by bringing in the app id, secret, and tenant id. Replace the strings below with your service principals information.

```python
from Lean Automation import auth, FabricClient
from Lean Automation.auth import FabricServicePrincipal

auth = FabricServicePrincipal("APP_ID", "APP_SECRET", "TENANT_ID")
fc = FabricClient(auth=auth)
for ws in fc.workspace.ls():
    print(f"{ws.name}: Id:{ws.id} Capacity:{ws.capacityId}")
```

Lean Automation supports many of the Fabric REST APIs and we appreciate contributions to help us close that gap.

Some of our best supported APIs include:

* Data Warehouse
* Data Engineering
* Real-time Intelligence

Lean Automation has been designed to support Fabric deployment and automation and follows a convention to make it easier to discover and connect APIs.

* List items like workspaces, tables: `fc.<item>.ls()` as in `fc.workspace.ls()`
* Create items like lakehouses, event streams: `fc.<item>.create()` as in `fs.lakehouse.create('NameOfLakehouse')`
* Delete items: `fc.<item>.delete()` as in `fc.warehouse.delete(worskspace_id, warehouse_id)`


