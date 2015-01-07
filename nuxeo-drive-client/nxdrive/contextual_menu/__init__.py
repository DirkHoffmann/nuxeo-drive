import sys
from nxdrive.logging_config import get_logger
from nxdrive.utils import version_compare
from nxdrive.utils import find_exe_path
from nxdrive.utils import update_win32_reg_key

log = get_logger(__name__)

REG_KEY = 'Software\\Classes\\*\\shell\\Nuxeo drive\\command'
METADATA_VIEW_SERVER_MIN_VERSION = '6.0'


def register_contextual_menu(controller):
    # Register contextual menu if metadata view is available server-side.
    # For now let's consider that it is the case if all server bindings have a server version greater or equal than the
    # minimum required.
    # Yet we should unregister contextual menu when binding a non compliant server, in fact ideally only display
    # the menu for files under a local folder bound to a compliant server.
    server_bindings = controller.list_server_bindings(controller.get_session())
    if server_bindings:
        for sb in server_bindings:
            if version_compare(sb.server_version, METADATA_VIEW_SERVER_MIN_VERSION) < 0:
                return
        if sys.platform == 'win32':
            register_contextual_menu_win32()


def register_contextual_menu_win32():
    """Register ndrive as a Windows explorer contextual menu entry"""
    import _winreg

    # TODO: better understand why / how this works.
    # See https://jira.nuxeo.com/browse/NXDRIVE-120
    app_name = "None"
    args = " metadata --file \"%1\""
    exe_path = find_exe_path() + args
    if exe_path is None:
        log.warning('Not a frozen windows exe: '
                    'skipping startup application registration')
        return

    log.debug("Registering '%s' application %s to registry key %s",
              app_name, exe_path, REG_KEY)
    reg = _winreg.ConnectRegistry(None, _winreg.HKEY_CURRENT_USER)
    update_win32_reg_key(
        reg, REG_KEY,
        [(app_name, _winreg.REG_SZ, exe_path)],
    )
