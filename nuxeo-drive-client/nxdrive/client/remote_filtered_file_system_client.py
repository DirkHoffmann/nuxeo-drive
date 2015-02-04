'''
Created on 19 mai 2014

@author: Remi Cattiau
'''
from nxdrive.client.remote_file_system_client import RemoteFileSystemClient
from nxdrive.client.common import DEFAULT_REPOSITORY_NAME
from nxdrive.model import Filter
from nxdrive.logging_config import get_logger

log = get_logger(__name__)


class RemoteFilteredFileSystemClient(RemoteFileSystemClient):
    '''
    classdocs
    '''

    def __init__(self, server_url, user_id, device_id, client_version,
                 session, proxies=None, proxy_exceptions=None,
                 password=None, token=None, repository=DEFAULT_REPOSITORY_NAME,
                 ignored_prefixes=None, ignored_suffixes=None,
                 timeout=20, blob_timeout=None, cookie_jar=None,
                 upload_tmp_dir=None, check_suspended=None):
        '''
        Constructor
        '''
        super(RemoteFilteredFileSystemClient, self).__init__(
            server_url, user_id, device_id,
            client_version, proxies, proxy_exceptions,
            password, token, repository, ignored_prefixes,
            ignored_suffixes, timeout, blob_timeout, cookie_jar,
            upload_tmp_dir, check_suspended)
        self.session = session

    def is_filtered(self, path):
        return Filter.is_filter(self.session, None, path)

    def get_children_info(self, fs_item_id):
        result = super(RemoteFilteredFileSystemClient, self).get_children_info(
                                                                    fs_item_id)
        # Need to filter the children result
        filtered = []
        for item in result:
            if not self.is_filtered(item.path):
                filtered.append(item)
            else:
                log.debug("Filtering item %r", item)
        return filtered

    def get_changes(self, server_binding):
        result = super(RemoteFilteredFileSystemClient, self).get_changes(
                                                                server_binding)
        log.trace("result['hasTooManyChanges'] = %r", result['hasTooManyChanges'])
        # Need to filter the result and add filterevents
        # Force the scan of the server every time now, need to compare to last
        # date filter
        # Need to multiply the last_filter_date by 1000 as the last_sync_date
        # come from nuxeo
        log.trace("server_binding.last_filter_date = %r", server_binding.last_filter_date)
        if server_binding.last_filter_date:
            log.trace("server_binding.last_sync_date = %r", server_binding.last_sync_date)
        if (server_binding.last_filter_date
            and server_binding.last_sync_date < (
                                    server_binding.last_filter_date * 1000)):
            log.trace("server_binding.last_sync_date < (server_binding.last_filter_date * 1000)"
                      " => setting result['hasTooManyChanges'] to True")
            result['hasTooManyChanges'] = True
        return result
