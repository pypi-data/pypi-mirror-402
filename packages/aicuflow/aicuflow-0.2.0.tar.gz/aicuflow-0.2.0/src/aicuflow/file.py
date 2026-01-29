from .baseobject import AicuBaseObject

class AicuFile(AicuBaseObject):
    """Quicker access to client functions on blobs /files!
    
    file.get() -> get
    file.suggest_plot() -> plot suggestions
    """
    def __init__(self, id: str, **kwargs):
        self._client = None
        super().__init__(id=id, **kwargs)
        self.auto_establish()

    def auto_establish(self):
        """
        It is allowed to have no id but an auto id and flow and filename, then it gets itself.
        """
        if self.id == "auto" and "name" in self and "flow" in self and self._client != None:
            # auto establish id if possible
            matches = [f for f in self._client.list_files(self.flow) if f["name"]==self.name]
            if len(matches) >= 1:
                for k, v in list(dict(matches[0]).items()):
                    self[k] = v
    
    def get(self):
        return self._client.get_file(self["id"])

    def suggest_plot(self):
        return self._client.get_plot_suggestions(self["id"])

    def download(self, local_path=None):
        return self._client.download_file(self["id"], local_path)
    
    def append(self, points):
        response = self._client.send_timeseries_points(self.flow, points, self.name)
        self.auto_establish()
        return response
    
    @classmethod
    def byname(cls, client, flow, name):
        return cls(
            id="auto",
            name=name,
            flow=flow["id"],
            _client=client
        )

file = AicuFile
