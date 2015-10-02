import requests
import os
from application import SystemUtility


class StorageNode(object):
    path = "storage"
    def __init__(self, storage_node):
        #super(Node, StorageNode).__init__(storage_node=storage_node)
        self.storage_node = storage_node

    @property
    def entrypoint(self):
        return os.path.join(SystemUtility.attract_server_endpoint(),
            self.path,
            self.storage_node.properties.backend,
            self.storage_node.properties.project,
            self.storage_node.properties.subdir)

    def browse(self, path=None):
        """Search a storage node for a path, which can point both to a directory
        of to a file.
        """
        if path is None:
            url = self.entrypoint
        else:
            url = os.path.join(self.entrypoint, path)
        r = requests.get(url)
        return r.json()
