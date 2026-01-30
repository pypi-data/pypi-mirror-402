
from leanautomation.core.workspace.workspace import _WorkspaceClient
from leanautomation.admin.workspace.adminworkspace import _AdminWorkspaceClient
from leanautomation.admin.tenant import _TenantClient
from leanautomation.core.capacity import _CapacityClient
from leanautomation.dataengineering.notebook import _NotebookClient
from leanautomation.dataengineering.sqlendpoints import _SQLEndpointClient
from leanautomation.datafactory.datapipeline import _DatapipelineClient
from leanautomation.datawarehouse.mirroredwarehouse import _MirroredWarehouseClient
from leanautomation.datawarehouse.warehouse import _WarehouseClient
from leanautomation.dataengineering.lakehouse import _LakehouseClient
from leanautomation.powerbi.dashboard import _DashboardClient
from leanautomation.powerbi.datamart import _DatamartClient
from leanautomation.powerbi.paginatedreport import _PaginatedReportClient
from leanautomation.powerbi.report import _ReportClient
from leanautomation.powerbi.semanticmodel import _SemanticModelClient
from leanautomation.realtimeintelligence.eventhouse import _EventhouseClient
from leanautomation.realtimeintelligence.eventstream import _EvenstreamClient
from leanautomation.realtimeintelligence.kqldatabase import _KQLDatabaseClient
from leanautomation.realtimeintelligence.kqlqueryset import _KQLQuerySetClient
from leanautomation.admin.domain import _DomainClient





class FabricClient():
    def __init__(self, auth, **kwargs):
        self._auth = auth
        self._base_url = kwargs.get("base_url") if "base_url" in kwargs else "https://api.fabric.microsoft.com/v1/"
        self.workspace = _WorkspaceClient(auth=auth, base_url=self._base_url)
        self.capacity = _CapacityClient(auth=auth, base_url=self._base_url)
        self.admin_workspaceclient = _AdminWorkspaceClient(auth=auth, base_url=self._base_url)
        self.warehouse = _WarehouseClient(auth=auth, base_url=self._base_url)
        self.lakehouse = _LakehouseClient(auth=auth, base_url=self._base_url)
        self.mirroredwarehouse = _MirroredWarehouseClient(auth=auth, base_url=self._base_url)
        self.semanticmodel = _SemanticModelClient(auth=auth, base_url=self._base_url)
        self.dashboardclient = _DashboardClient(auth=auth, base_url=self._base_url)
        self.datamartclient = _DatamartClient(auth=auth, base_url=self._base_url)
        self.paginatedreportclient = _PaginatedReportClient(auth=auth, base_url=self._base_url)
        self.sqlendpoint = _SQLEndpointClient(auth=auth, base_url=self._base_url)
        self.report = _ReportClient(auth=auth, base_url=self._base_url)
        self.eventhouse = _EventhouseClient(auth=auth, base_url=self._base_url)
        self.eventstream = _EvenstreamClient(auth=auth, base_url=self._base_url)
        self.kqldatabase = _KQLDatabaseClient(auth=auth, base_url=self._base_url)
        self.kqlqueryset = _KQLQuerySetClient(auth=auth, base_url=self._base_url)
        self.datapipeline = _DatapipelineClient(auth=auth, base_url=self._base_url)
        self.notebook = _NotebookClient(auth=auth, base_url=self._base_url)
        self.tenant = _TenantClient(auth=auth, base_url=self._base_url)
        self.domain = _DomainClient(auth=auth, base_url=self._base_url)

