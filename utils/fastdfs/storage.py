from django.core.files.storage import Storage

from dailyfresh.settings import NGINX_URL, CLIENT_PATH
from fdfs_client.client import Fdfs_client


class FDFSStorage(Storage):
    def __init__(self, nginx_url=None, client_path=None):
        if nginx_url is None:
            self.nginx_url = NGINX_URL
        if client_path is None:
            self.client_path = CLIENT_PATH

    def _open(self, name, mode='rb'):
        pass

    def _save(self, name, content):
        client = Fdfs_client(self.client_path)
        res = client.upload_by_buffer(content.read())
        # return dict
        # {
        #     'Group name': group_name,
        #     'Remote file_id': remote_file_id,
        #     'Status': 'Upload successed.',
        #     'Local file name': '',
        #     'Uploaded size': upload_size,
        #     'Storage IP': storage_ip
        # }
        if res.get("Status") != "Upload successed.":
            raise Exception("文件未上传成功")
        return res.get("Remote file_id")

    def exists(self, name):
        return False

    def url(self, name):
        return self.nginx_url + name