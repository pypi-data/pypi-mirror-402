from .baseobject import AicuBaseObject

class AicuFlow(AicuBaseObject):
    """Quicker access to client functions!
    
    flow.get() -> metadata
    flow.open() -> browser
    flow.notes() -> annotations
    flow.nodes() -> nodes
    flow.edges() -> edges
    flow.files() -> files
    flow.plots() -> plots
    flow.integrations() -> integrations
    flow.syncjobs() -> syncjobs
    flow.deployments() -> deployments
    flow.shares() -> shares
    flow.delete() -> deleted
    """
    def __init__(self, id: str, **kwargs):
        super().__init__(id=id, **kwargs)

    def get(self):
        return self._client.get_flow(self["id"])

    def open(self):
        return self._client.open_flow(self["id"])

    def notes(self):
        return self._client.list_annotations(self["id"])
        
    def nodes(self):
        return self._client.list_nodes(self["id"])
        
    def edges(self):
        return self._client.list_edges(self["id"])
        
    def files(self):
        return self._client.list_files(self["id"])
        
    def plots(self):
        return self._client.list_plots(self["id"])
        
    def integrations(self):
        return self._client.list_connections(self["id"])
        
    def syncjobs(self):
        return self._client.list_syncjobs(self["id"])
        
    def deployments(self):
        return self._client.list_deployments(self["id"])
        
    def shares(self):
        return self._client.list_shares(self["id"])
        
    def delete(self):
        return self._client.delete_flow(self["id"])

flow = AicuFlow