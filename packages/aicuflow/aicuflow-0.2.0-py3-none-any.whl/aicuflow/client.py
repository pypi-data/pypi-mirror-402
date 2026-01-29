import os
import mimetypes
import requests
import webbrowser

from .flow import AicuFlow
from .file import AicuFile

class AicuClient:
    """Aicuflow client

    This allows you to run basic functions,
    connectiong to the aicuflow public api.

    docs at https://aicuflow.com/docs/library/python
    """

    def __init__(self, token=None, email=None, password=None, base_url=None, verbose=False, dev=False):
        """Initialise the aicuflow client

        :param token: optional bearer token to sign in
        :param email: the email of a user to sign in
        :param password: the password of a user to sign in
        :param base_url: optional base url of the api
        :param verbose: optional weather to print more
        :param dev: optional when true default dev-backend url is set else prod

        :returns: aicuflow client
        """
        self.base_url = base_url if base_url else ("https://dev-backend.aicuflow.com" if dev else "https://prod-backend.aicuflow.com")
        self.session = requests.Session()
        self.verbose = verbose

        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        elif email and password:
            self._login(email, password)
        else:
            raise ValueError("Provide token or email+password")

    # core base fkts

    def _login(self, email, password):
        """Login to the URLS."""
        r = self.session.post(
            f"{self.base_url}/user/auth/login/",
            json={
                "email": email,
                "keep_me_logged_in": True,
                "password": password,
            },
        )
        if self.verbose:
            print(r)
            print(r.json())
        #r.raise_for_status()
        token = r.json()["data"]["accesstoken"]
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def _get(self, path):
        """Get an url with the current headers."""
        r = self.session.get(f"{self.base_url}{path}")
        r.raise_for_status()
        return r.json()

    def _post(self, path, payload):
        """Post to an url with the current headers."""
        r = self.session.post(f"{self.base_url}{path}", json=payload)
        r.raise_for_status()
        return r.json()
    
    # user / client based getters

    def get_settings(self):
        """Fetch the current users settings.

        Returns: a json object.
        """
        try:
            return self._get(f"/user/profile/")["data"]
        except:
            return None
    
    def get_subscription(self):
        """Fetch the current users subscription.

        Returns: a json object containing id, subscription_template, latest_usage and more useful keys.
        """
        try:
            return self._get("/subscriptions/me/")["data"]
        except:
            return None

    def list_flows(self):
        """Fetch the current users flows.

        Returns: list of all flows with id and owner, agent id, props
        """
        try:
            return [AicuFlow(**f, _client=self) for f in self._get("/flows/?page=1&page_size=100")["data"]]
        except:
            return None
        
    def list_templates(self):
        """Fetch all templates

        Returns: list of templates
        """
        try:
            return self._get(f"/templates/")["data"]
        except:
            return None
    
    def list_nodetypes(self):
        """Fetch all node types

        Returns: list of node types
        """
        try:
            return self._get(f"/node/nodes/")
        except:
            return None
    
    def list_integrations(self):
        """Fetch all integration types

        Returns: list of integration types
        """
        try:
            return self._get(f"/data/connectors/")["data"]
        except:
            return None

    # core utility

    def ensure_flow_by_title(self, title):
        """Ensure a flow title exists in the user

        Returns: that specific flow
        """
        flows = self.list_flows()
        matches = [f for f in flows if title == f["title"]]
        if len(matches) >= 1: # at least one
            return matches[0]
        else: # else create
            return self.create_flow(title)
    
    # flow id needing getters

    def get_flow(self, flow_id):
        """Fetch flow details

        Param flow_id: the flow
        
        Returns: list of params
        """
        try:
            return self._get(f"/flows/{flow_id}/")["data"]
        except:
            return None
        
    def open_flow(self, flow_id):
        """Open flow in browser

        Param flow_id: the flow
        
        Returns: webbrowser status
        """
        return webbrowser.open(f"aicuflow.com/flows/{flow_id}/editor")
    
    def list_annotations(self, flow_id):
        """Fetch all annotations within a flow

        Param flow_id: the flow
        
        Returns: list of annotations
        """
        try:
            return self._get(f"/annotations/?flow={flow_id}")["data"]
        except:
            return None
    
    def list_nodes(self, flow_id):
        """Fetch all nodes within a flow

        Param flow_id: the flow
        
        Returns: list of nodes
        """
        try:
            return self._get(f"/node/user-nodes/by-flow/{flow_id}/")["data"]
        except:
            return None

    def list_edges(self, flow_id):
        """Fetch all edges within a flow

        Param flow_id: the flow
        
        Returns: list of edges
        """
        try:
            return self._get(f"/node/edges/?flow={flow_id}")["data"]
        except:
            return None
            
    def list_files(self, flow_id):
        """Fetch all files within a flow

        Param flow_id: the flow
        
        Returns: list of files
        """
        try:
            return [
                AicuFile(**f, _client=self)
                for f in self._get(f"/data/folders/hierarchy/?flow={flow_id}&page=1&page_size=100&sort_by=created_at&sort_order=desc")["data"]["blobs"]
            ]
        except:
            return None
            
    def list_plots(self, flow_id):
        """Fetch all plots within a flow

        Param flow_id: the flow
        
        Returns: list of plots
        """
        try:
            return self._get(f"/plot/user-plot/?flow_id={flow_id}&cursor=0&limit=100")["data"]
        except:
            return None
            
    def list_connections(self, flow_id):
        """Fetch all integration connections within a flow

        Param flow_id: the flow
        
        Returns: list of integration connections
        """
        try:
            return self._get(f"/data/user-connectors/?flow={flow_id}")["data"]
        except:
            return None
            
    def list_syncjobs(self, flow_id):
        """Fetch all syncjobs within a flow

        Param flow_id: the flow
        
        Returns: list of syncjobs
        """
        try:
            return self._get(f"/data/sync-jobs/?flow={flow_id}")["data"]
        except:
            return None
        
    def list_deployments(self, flow_id):
        """Fetch all deployments within a flow

        Param flow_id: the flow
        
        Returns: list of deployments
        """
        try:
            return self._get(f"/node/deployments/?flow_id={flow_id}")["data"]
        except:
            return None
        
    def list_shares(self, flow_id):
        """Fetch all shares / collaborators within a flow

        Param flow_id: the flow
        
        Returns: list of  shares / collaborators
        """
        try:
            return self._get(f"/collaborators/{flow_id}/list/?include_pending=true")["data"]
        except:
            return None

    list_collabs = list_shares
    list_collaborators = list_shares
    
    def delete_flow(self, flow_id):
        """Delete a flow.

        Returns: Boolean, true if it worked
        """
        return self.session.delete(f"{self.base_url}/flows/{flow_id}/").status_code in (200, 201, 202, 203, 204)
    
    # blob based getters

    def get_plot_suggestions(self, blob_id):
        """Fetch plotsuggestions for a blob

        Param blob_id: the blob
        
        Returns: list of suggestions
        """
        try:
            return self._get(f"/plot/user-plot/plot-suggestions/?blob_id={blob_id}&max_suggestions=10&top_n_columns=10")["data"]
        except:
            return None

    def get_file(self, blob_id):
        """Fetch blob data

        Param blob_id: the blob
        
        Returns: blob data
        """
        try:
            return self._get(f"/data/blobs/{blob_id}/load/?page=1&page_size=100")["data"]
        except:
            return None
    
    def download_file(self, blob_id, local_path=None):
        """Download a file

        - gets the metadata
        - downloads the presigned aws url

        Returns: file name
        """
        
        # 1) fetch blob metadata (expects presigned download url in response)
        blob = self.get_file(blob_id)

        download_url = blob.get("url")
        
        if not download_url:
            raise RuntimeError("No download URL in blob response")

        filename = (
            local_path
            or blob.get("original_filename")
            or blob.get("name")
            or blob_id
        )

        # 2) stream download
        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            with open(filename, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)

        return filename
    
    def upload_file(self, flow_id, file_path):
        """Fetch all files within a flow
    
        Param flow_id: the flow
        
        Returns: list of files
        """
        
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        content_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
        
        if self.verbose:
            print(file_name, file_size, content_type)
        
        # 1) request presigned URL via self._post
        resp = self._post(
            "/data/blob-upload/",
            {
                "file_name": file_name,
                "file_size": file_size,
                "content_type": content_type,
                "flow_id": flow_id,
            }
        )
    
        blob = resp["data"]["files"][0]
        presigned_url = blob["presigned_url"]
        object_key = blob["object_key"]
        blob_id = blob["blob_id"]
        
        if self.verbose:
            print(blob, presigned_url, object_key, blob_id)
        
        # 2) upload to S3 (plain requests, auth not needed)
        with open(file_path, "rb") as f:
            r = requests.put(presigned_url, data=f, headers={"Content-Type": content_type})
            r.raise_for_status()
        
        # 3) finalize blob creation via self._post
        resp = self._post(
            "/data/blob-upload/create-blob/",
            {
                "object_key": object_key,
                "file_name": file_name,
                "name": file_name,
                "blob_id": blob_id,
                "flow_id": flow_id,
                "source": "upload",
                "unify": True,
            }
        )
        
        return resp["data"]
    
    def send_timeseries_points(self, flow_id, points, file_name="py-data-posts.arrow"):
        """Stream data to a file on storage (for time series)

        The file (identified by name) is auto-created or appended in the aicuflow file manager.
        Then they can be used in the platform.

        Returns: None
        """
        if self.verbose:
            print("Sending...")
        self._post(
            f"/data/write-values/?filename={file_name}&flow={flow_id}",
            points
        )

    def delete_file(self, blob_id):
        """Delete a file.

        Returns: Boolean, true if it worked
        """
        return self.session.delete(f"{self.base_url}/data/blobs/{blob_id}/").status_code in (200, 201, 202, 203, 204)

    def create_flow(self, name="new flow", descr="description"):
        """Create a new flow

        Returns: flow props
        """
        return AicuFlow(
            **self._post(
                f"/flows/",
                {
                    "title": name,
                    "description": descr,
                    "is_global":False,
                    "is_template":False
                }
            )["data"],
            _client=self
        )

client = AicuClient