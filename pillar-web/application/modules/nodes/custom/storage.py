import requests
import os
from application import system_util
from application import cache


class StorageNode(object):
    path = "storage"
    def __init__(self, storage_node):
        #super(Node, StorageNode).__init__(storage_node=storage_node)
        self.storage_node = storage_node

    @property
    def entrypoint(self):
        return os.path.join(system_util.pillar_server_endpoint(),
            self.path,
            self.storage_node.properties.backend,
            self.storage_node.properties.project,
            self.storage_node.properties.subdir)

    @cache.memoize(timeout=3600)
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
