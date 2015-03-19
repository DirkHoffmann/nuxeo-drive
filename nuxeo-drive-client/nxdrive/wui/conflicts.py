'''
Created on 10 mars 2015

@author: Remi Cattiau
'''
from nxdrive.logging_config import get_logger
from nxdrive.wui.dialog import WebDialog, WebDriveApi
from nxdrive.wui.translator import Translator
from PySide import QtCore

log = get_logger(__name__)


class WebConflictsApi(WebDriveApi):
    def __init__(self, application, engine, dlg=None):
        super(WebConflictsApi, self).__init__(application, dlg)
        self._manager = application.manager
        self._application = application
        self._dialog = dlg
        self._engine = engine

    def set_engine(self, engine):
        self._engine = engine

    @QtCore.Slot(result=str)
    def get_errors(self):
        return super(WebConflictsApi, self).get_errors(self._engine._uid)

    @QtCore.Slot(result=str)
    def get_conflicts(self):
        return super(WebConflictsApi, self).get_conflicts(self._engine._uid)

    @QtCore.Slot(int)
    def resolve_with_local(self, state_id):
        try:
            self._engine.resolve_with_local(state_id)
        except Exception as e:
            log.exception(e)

    @QtCore.Slot(int)
    def resolve_with_remote(self, state_id):
        try:
            self._engine.resolve_with_remote(state_id)
        except Exception as e:
            log.exception(e)

    @QtCore.Slot(int)
    def resolve_with_duplicate(self, state_id):
        try:
            self._engine.resolve_with_duplicate(state_id)
        except Exception as e:
            log.exception(e)

    @QtCore.Slot(int)
    def retry_pair(self, state_id):
        try:
            self._engine.retry_pair(int(state_id))
        except Exception as e:
            log.exception(e)

    @QtCore.Slot(str, result=str)
    def open_local(self, path):
        return super(WebConflictsApi, self).open_local(self._engine._uid, path)

    @QtCore.Slot(str, result=str)
    def open_remote(self, remote_ref):
        remote_ref = str(remote_ref)
        log.debug("Should open this : %s", remote_ref)
        try:
            self._engine.open_edit(remote_ref)
        except Exception as e:
            log.exception(e)
        return ""

    def _export_state(self, state):
        if state is None:
            return None
        result = super(WebConflictsApi, self)._export_state(state)
        result["last_contributor"] = state.last_remote_modifier
        date_time = self.get_date_from_sqlite(state.last_remote_updated)
        result["last_remote_update"] = Translator.format_datetime(date_time)
        date_time = self.get_date_from_sqlite(state.last_local_updated)
        result["last_local_update"] = Translator.format_datetime(date_time)
        return result


class WebConflictsDialog(WebDialog):
    def set_engine(self, engine):
        self._api.set_engine(engine)
