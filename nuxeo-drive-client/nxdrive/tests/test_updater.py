import unittest

from esky import Esky
import esky.finder
from nxdrive.updater import AppUpdater
from nxdrive.updater import MissingUpdateSiteInfo
from nxdrive.updater import MissingCompatibleVersion
from nxdrive.updater import UPDATE_STATUS_UPGRADE_NEEDED
from nxdrive.updater import UPDATE_STATUS_DOWNGRADE_NEEDED
from nxdrive.updater import UPDATE_STATUS_UPDATE_AVAILABLE
from nxdrive.updater import UPDATE_STATUS_UP_TO_DATE
from nxdrive.updater import UPDATE_STATUS_MISSING_INFO
from nxdrive.updater import UPDATE_STATUS_MISSING_VERSION
from nxdrive.logging_config import configure


def configure_logger():
    configure(
        file_level='DEBUG',
        console_level='DEBUG',
        command_name='test',
    )

configure_logger()


class MockEsky(Esky):
    """Mock Esky subclass using a LocalVersionFinder."""

    def __init__(self, appdir_or_exe, version_finder=None):
        super(MockEsky, self).__init__(appdir_or_exe,
                                       version_finder=version_finder)
        self.set_local_version_finder(version_finder)

    def set_local_version_finder(self, version_finder):
        if version_finder is not None:
            if isinstance(version_finder, basestring):
                kwds = {"download_url": version_finder}
                version_finder = esky.finder.LocalVersionFinder(**kwds)
        self.version_finder = version_finder


class TestUpdater(unittest.TestCase):

    def setUp(self):
        appdir = 'nxdrive/tests/resources/esky_app'
        version_finder = 'nxdrive/tests/resources/esky_versions'
        self.esky_app = MockEsky(appdir, version_finder=version_finder)
        self.updater = AppUpdater(esky_app=self.esky_app,
                                  local_update_site=True)

    def test_get_active_version(self):
        # Active version is None because Esky instance is built from a
        # directory, see Esky._init_from_appdir
        self.assertIsNone(self.updater.get_active_version())

    def test_get_current_latest_version(self):
        self.assertEquals(self.updater.get_current_latest_version(),
                          '1.3.0424')

    def test_find_versions(self):
        versions = self.updater.find_versions()
        self.assertEquals(versions, ['1.3.0524', '1.4.0622'])

    def test_get_server_min_version(self):
        # Unexisting version
        self.assertRaises(MissingUpdateSiteInfo,
                          self.updater.get_server_min_version, '4.6.2012')
        self.assertEquals(self.updater.get_server_min_version('1.3.0424'),
                          '5.8')
        self.assertEquals(self.updater.get_server_min_version('1.3.0524'),
                          '5.9.1')
        self.assertEquals(self.updater.get_server_min_version('1.4.0622'),
                          '5.9.2')

    def test_get_client_min_version(self):
        # Unexisting version
        self.assertRaises(MissingUpdateSiteInfo,
                          self.updater.get_client_min_version, '5.6')
        self.assertEquals(self.updater.get_client_min_version('5.8'),
                          '1.2.0110')
        self.assertEquals(self.updater.get_client_min_version('5.9.1'),
                          '1.3.0424')
        self.assertEquals(self.updater.get_client_min_version('5.9.2'),
                          '1.3.0424')
        self.assertEquals(self.updater.get_client_min_version('5.9.3'),
                          '1.4.0622')
        self.assertEquals(self.updater.get_client_min_version('5.9.4'),
                          '1.5.0715')

    def test_get_latest_compatible_version(self):
        # No update info available for server version
        self.assertRaises(MissingUpdateSiteInfo,
                          self.updater.get_latest_compatible_version, '5.6')
        # No compatible client version with server version
        self.assertRaises(MissingCompatibleVersion,
                         self.updater.get_latest_compatible_version, '5.9.4')
        # Compatible versions
        self.assertEqual(self.updater.get_latest_compatible_version('5.9.3'),
                         '1.4.0622')
        self.assertEqual(self.updater.get_latest_compatible_version('5.9.2'),
                         '1.4.0622')
        self.assertEqual(self.updater.get_latest_compatible_version('5.9.1'),
                         '1.3.0524')
        self.assertEqual(self.updater.get_latest_compatible_version('5.8'),
                         '1.3.0424')

    def test_get_update_status(self):
        # No update info available (missing client version info)
        status = self.updater.get_update_status('1.2.0207', '5.9.3')
        self.assertEquals(status, (UPDATE_STATUS_MISSING_INFO, None))

        # No update info available (missing server version info)
        status = self.updater.get_update_status('1.3.0424', '5.6')
        self.assertEquals(status, (UPDATE_STATUS_MISSING_INFO, None))

        # No compatible client version with server version
        status = self.updater.get_update_status('1.4.0622', '5.9.4')
        self.assertEquals(status, (UPDATE_STATUS_MISSING_VERSION, None))

        # Upgraded needed
        status = self.updater.get_update_status('1.3.0424', '5.9.3')
        self.assertEquals(status, (UPDATE_STATUS_UPGRADE_NEEDED, '1.4.0622'))
        status = self.updater.get_update_status('1.3.0524', '5.9.3')
        self.assertEquals(status, (UPDATE_STATUS_UPGRADE_NEEDED, '1.4.0622'))

        # Downgrade needed
        status = self.updater.get_update_status('1.3.0524', '5.8')
        self.assertEquals(status, (UPDATE_STATUS_DOWNGRADE_NEEDED, '1.3.0424'))
        status = self.updater.get_update_status('1.4.0622', '5.8')
        self.assertEquals(status, (UPDATE_STATUS_DOWNGRADE_NEEDED, '1.3.0424'))
        status = self.updater.get_update_status('1.4.0622', '5.8')
        self.assertEquals(status, (UPDATE_STATUS_DOWNGRADE_NEEDED, '1.3.0424'))
        status = self.updater.get_update_status('1.4.0622', '5.9.1')
        self.assertEquals(status, (UPDATE_STATUS_DOWNGRADE_NEEDED, '1.3.0524'))

        # Upgrade available
        status = self.updater.get_update_status('1.3.0424', '5.9.1')
        self.assertEquals(status,
                          (UPDATE_STATUS_UPDATE_AVAILABLE, '1.3.0524'))
        status = self.updater.get_update_status('1.3.0424', '5.9.2')
        self.assertEquals(status,
                          (UPDATE_STATUS_UPDATE_AVAILABLE, '1.4.0622'))
        status = self.updater.get_update_status('1.3.0524', '5.9.2')
        self.assertEquals(status,
                          (UPDATE_STATUS_UPDATE_AVAILABLE, '1.4.0622'))
        status = self.updater.get_update_status('1.3.0524', '5.9.3')

        # Up-to-date
        status = self.updater.get_update_status('1.3.0424', '5.8')
        self.assertEquals(status,
                          (UPDATE_STATUS_UP_TO_DATE, None))
        status = self.updater.get_update_status('1.3.0524', '5.9.1')
        self.assertEquals(status,
                          (UPDATE_STATUS_UP_TO_DATE, None))
        status = self.updater.get_update_status('1.4.0622', '5.9.2')
        self.assertEquals(status,
                          (UPDATE_STATUS_UP_TO_DATE, None))
        status = self.updater.get_update_status('1.4.0622', '5.9.3')
        self.assertEquals(status,
                          (UPDATE_STATUS_UP_TO_DATE, None))
