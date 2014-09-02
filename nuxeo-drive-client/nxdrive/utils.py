import os
import stat
import sys
import re
import locale
import mimetypes
import shutil
from shutil import rmtree as shutil_rmtree
from Crypto.Cipher import AES
from Crypto import Random
from nxdrive.logging_config import get_logger


log = get_logger(__name__)


WIN32_SUFFIX = os.path.join('library.zip', 'nxdrive')
OSX_SUFFIX = "Contents/Resources/lib/python2.7/site-packages.zip/nxdrive"

ENCODING = locale.getpreferredencoding()
DEFAULT_ENCODING = 'utf-8'

WIN32_PATCHED_MIME_TYPES = {
    'image/pjpeg': 'image/jpeg',
    'image/x-png': 'image/png',
    'image/bmp': 'image/x-ms-bmp',
    'audio/x-mpg': 'audio/mpeg',
    'video/x-mpeg2a': 'video/mpeg',
    'application/x-javascript': 'application/javascript',
    'application/x-mspowerpoint.12':
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
}


def normalized_path(path):
    """Return absolute, normalized file path."""
    if isinstance(path, bytes):
        # Decode path with local encoding when not already decoded explicitly
        # by the caller
        path = path.decode(ENCODING)

    # XXX: we could os.path.normcase as well under Windows but it might be the
    # source of unexpected troubles so not doing it for now.
    return os.path.normpath(os.path.abspath(os.path.expanduser(path)))


def safe_long_path(path):
    """Utility to prefix path with the long path marker for Windows

    http://msdn.microsoft.com/en-us/library/aa365247.aspx#maxpath

    """
    if sys.platform == 'win32':
        if isinstance(path, bytes):
            # Decode path with local encoding when not already decoded
            # explicitly  by the caller
            path = unicode(path.decode(ENCODING))
        path = u"\\\\?\\" + path
    return path


def find_resource_dir(directory, default_path):
    """Find the FS path of a directory in various OS binary packages"""
    import nxdrive
    nxdrive_path = os.path.dirname(nxdrive.__file__)

    app_resources = '/Contents/Resources/'
    cxfreeze_suffix = os.path.join('library.zip', 'nxdrive')

    dir_path = default_path
    if app_resources in nxdrive_path:
        # OSX frozen distribution, bundled as an app
        dir_path = re.sub(app_resources + ".*", app_resources + directory,
                             nxdrive_path)

    elif nxdrive_path.endswith(cxfreeze_suffix):
        # cx_Freeze frozen distribution of nxdrive, data is out of the zip
        dir_path = nxdrive_path.replace(cxfreeze_suffix, directory)

    if not os.path.exists(dir_path):
        log.warning("Could not find the resource directory at: %s",
                    dir_path)
        return None

    return dir_path


def find_exe_path():
    """Introspect the Python runtime to find the frozen Windows exe"""
    import nxdrive
    nxdrive_path = os.path.realpath(os.path.dirname(nxdrive.__file__))

    # Detect frozen win32 executable under Windows
    if nxdrive_path.endswith(WIN32_SUFFIX):
        exe_path = nxdrive_path.replace(WIN32_SUFFIX, 'ndrivew.exe')
        if os.path.exists(exe_path):
            return exe_path

    # Detect OSX frozen app
    if nxdrive_path.endswith(OSX_SUFFIX):
        exe_path = nxdrive_path.replace(OSX_SUFFIX,
                                        "Contents/MacOS/Nuxeo Drive")
        if os.path.exists(exe_path):
            return exe_path

    # Fall-back to the regular method that should work both the ndrive script
    return sys.argv[0]


def update_win32_reg_key(reg, path, attributes=()):
    """Helper function to create / set a key with attribute values"""
    import _winreg
    key = _winreg.CreateKey(reg, path)
    _winreg.CloseKey(key)
    key = _winreg.OpenKey(reg, path, 0, _winreg.KEY_WRITE)
    for attribute, type_, value in attributes:
        _winreg.SetValueEx(key, attribute, 0, type_, value)
    _winreg.CloseKey(key)


def force_decode(string, codecs=['utf8', 'cp1252']):
    for codec in codecs:
        try:
            return string.decode(codec)
        except:
            pass
    log.debug("Cannot decode string '%s' with any of the given codecs: %r",
              string, codecs)
    return ''


def encrypt(plaintext, secret, lazy=True):
    """Symetric encryption using AES"""
    secret = _lazysecret(secret) if lazy else secret
    iv = Random.new().read(AES.block_size)
    encobj = AES.new(secret, AES.MODE_CFB, iv)
    return iv + encobj.encrypt(plaintext)


def decrypt(ciphertext, secret, lazy=True):
    """Symetric decryption using AES"""
    secret = _lazysecret(secret) if lazy else secret
    iv = ciphertext[:AES.block_size]
    ciphertext = ciphertext[AES.block_size:]
    encobj = AES.new(secret, AES.MODE_CFB, iv)
    return encobj.decrypt(ciphertext)


def _lazysecret(secret, blocksize=32, padding='}'):
    """Pad secret if not legal AES block size (16, 24, 32)"""
    if len(secret) > blocksize:
        return secret[:-(len(secret) - blocksize)]
    if not len(secret) in (16, 24, 32):
        return secret + (blocksize - len(secret)) * padding
    return secret


def guess_mime_type(filename):
    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type:
        if sys.platform == 'win32':
            # Patch bad Windows MIME types
            # See https://jira.nuxeo.com/browse/NXP-11660
            # and http://bugs.python.org/issue15207
            mime_type = _patch_win32_mime_type(mime_type)
        log.trace("Guessed mime type '%s' for '%s'", mime_type, filename)
        return mime_type
    else:
        log.trace("Could not guess mime type for '%s', returing"
            " 'application/octet-stream'", filename)
        return "application/octet-stream"


def _patch_win32_mime_type(mime_type):
    patched_mime_type = WIN32_PATCHED_MIME_TYPES.get(mime_type)
    return patched_mime_type if patched_mime_type else mime_type


def deprecated(func):
    """"This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emitted
    when the function is used."""
    def new_func(*args, **kwargs):
        log.warning("Call to deprecated function {}.".format(func.__name__))
        return func(*args, **kwargs)
    new_func.__name__ = func.__name__
    new_func.__doc__ = func.__doc__
    new_func.__dict__.update(func.__dict__)
    return new_func


def _remove_readonly(func, path, _):
    """Clear the readonly bit and reattempt the removal."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


def rmtree_readonly(path, ignore_errors=False, onerror=None):
    shutil_rmtree(path, onerror=_remove_readonly)


def patch_shutil_rmtree():
    """Patch shutil.rmtree to handle readonly files under Windows.

    See http://bugs.python.org/issue19643 and
    http://hg.python.org/cpython/rev/31d63ea5dffa
    """
    shutil.rmtree = rmtree_readonly
