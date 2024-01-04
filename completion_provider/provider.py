# -*- coding: utf-8 -*-

# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License

"""Kite completion HTTP client."""

# Standard library imports
import logging
import functools
import os
import os.path as osp

# Qt imports
from qtpy.QtCore import Slot
from qtpy.QtWidgets import QMessageBox

# Local imports
from completion_provider.client import KiteClient
from completion_provider.utils.status import (
    check_if_kite_running, check_if_kite_installed)
from completion_provider.widgets import (KiteStatusWidget)

# Spyder imports
from spyder.api.config.decorators import on_conf_change
from spyder.config.base import _, running_under_pytest, get_module_data_path
from spyder.plugins.completion.api import SpyderCompletionProvider
from spyder.utils.image_path_manager import IMAGE_PATH_MANAGER
from spyder.utils.programs import run_program


logger = logging.getLogger(__name__)


class CompletionProvider(SpyderCompletionProvider):
    COMPLETION_PROVIDER_NAME = 'langchain'
    DEFAULT_ORDER = 1
    SLOW = True
    CONF_DEFAULTS = [
        ('show_onboarding', True),
        ('show_installation_error_message', True)
    ]
    CONF_VERSION = "1.0.0"

    def __init__(self, parent, config):
        super().__init__(parent, config)
        IMAGE_PATH_MANAGER.add_image_path(
            get_module_data_path('kite_provider', relpath='images')
        )
        self.available_languages = []
        self.client = KiteClient(None)
        self.kite_process = None

        # Signals
        self.client.sig_client_started.connect(self.http_client_ready)
        self.client.sig_status_response_ready[str].connect(
            self.set_status)
        self.client.sig_status_response_ready[dict].connect(
            self.set_status)
        self.client.sig_response_ready.connect(
            functools.partial(self.sig_response_ready.emit,
                              self.COMPLETION_PROVIDER_NAME))

        self.client.sig_client_wrong_response.connect(
            self._wrong_response_error)

        # Status bar widget
        self.STATUS_BAR_CLASSES = [
            self.create_statusbar
        ]

        # Config
        self.update_kite_configuration(self.config)

    # ------------------ SpyderCompletionProvider methods ---------------------
    def get_name(self):
        return 'LangChain'

    def send_request(self, language, req_type, req, req_id):
        if language in self.available_languages:
            self.client.sig_perform_request.emit(req_id, req_type, req)
        else:
            self.sig_response_ready.emit(self.COMPLETION_PROVIDER_NAME,
                                         req_id, {})

    def start_completion_services_for_language(self, language):
        return language in self.available_languages

    def start(self):
        try:
            installed, path = check_if_kite_installed()
            if not installed:
                return
            logger.debug('Kite was found on the system: {0}'.format(path))
            running = check_if_kite_running()
            if running:
                return
            logger.debug('Starting Kite service...')
            self.kite_process = run_program(path)
        except OSError:
            installed, path = check_if_kite_installed()
            logger.debug(
                'Error starting Kite service at {path}...'.format(path=path))
            if self.get_conf('show_installation_error_message'):
                err_str = _(
                    "It seems that your Kite installation is faulty. "
                    "If you want to use Kite, please remove the "
                    "directory that appears bellow, "
                    "and try a reinstallation:<br><br>"
                    "<code>{kite_dir}</code>").format(
                        kite_dir=osp.dirname(path)
                    )

                def wrap_message(parent):
                    return QMessageBox.critical(
                        parent, _('Kite error'), err_str
                    )

                self.sig_show_widget.emit(wrap_message)

        finally:
            # Always start client to support possibly undetected Kite builds
            self.client.start()

    def shutdown(self):
        self.client.stop()
        if self.kite_process is not None:
            self.kite_process.kill()

    def on_mainwindow_visible(self):
        self.client.sig_response_ready.connect(self._kite_onboarding)
        self.client.sig_status_response_ready.connect(self._kite_onboarding)
        self.client.sig_onboarding_response_ready.connect(
            self._show_onboarding_file)

    @Slot(list)
    def http_client_ready(self, languages):
        logger.debug('Kite client is available for {0}'.format(languages))
        self.available_languages = languages
        self.sig_provider_ready.emit(self.COMPLETION_PROVIDER_NAME)
        self._kite_onboarding()

    @Slot(str)
    @Slot(dict)
    def set_status(self, status):
        """Show Kite status for the current file."""
        self.sig_call_statusbar.emit(
            KiteStatusWidget.ID, 'set_value', (status,), {})

    def file_opened_closed_or_updated(self, filename, _language):
        """Request status for the given file."""
        self.client.sig_perform_status_request.emit(filename)

    @on_conf_change(
        section='completions', option=('enabled_providers', 'kite'))
    def on_kite_enable_changed(self, value):
        self.sig_call_statusbar.emit(
            KiteStatusWidget.ID, 'set_value', (None,), {})

    @on_conf_change(section='completions', option='enable_code_snippets')
    def on_code_snippets_changed(self, value):
        if running_under_pytest():
            if not os.environ.get('SPY_TEST_USE_INTROSPECTION'):
                return

        self.client.enable_code_snippets = self.get_conf(
            'enable_code_snippets', section='completions')

    @on_conf_change
    def update_kite_configuration(self, config):
        if running_under_pytest():
            if not os.environ.get('SPY_TEST_USE_INTROSPECTION'):
                return

        self._show_onboarding = self.get_conf('show_onboarding')

    def _kite_onboarding(self):
        """Request the onboarding file."""
        # No need to check installed status,
        # since the get_onboarding_file call fails fast.
        if not self._show_onboarding:
            return
        if not self.available_languages:
            return
        # Don't send another request until this request fails.
        self._show_onboarding = False
        self.client.sig_perform_onboarding_request.emit()

    @Slot(str)
    def _show_onboarding_file(self, onboarding_file):
        """
        Opens the onboarding file, which is retrieved
        from the Kite HTTP endpoint. This skips onboarding if onboarding
        is not possible yet or has already been displayed before.
        """
        if not onboarding_file:
            # retry
            self._show_onboarding = True
            return
        self.sig_open_file.emit(onboarding_file)
        self.set_conf('show_onboarding', False)

    @Slot(str, object)
    def _wrong_response_error(self, method, resp):
        err_msg = _(
            "The Kite completion engine returned an unexpected result "
            "for the request <tt>{0}</tt>: <br><br><tt>{1}</tt><br><br>"
            "Please make sure that your Kite installation is correct. "
            "In the meantime, Spyder will disable the Kite client to "
            "prevent further errors. For more information, please "
            "visit the <a href='https://help.kite.com/'>Kite help "
            "center</a>").format(method, resp)

        def wrap_message(parent):
            return QMessageBox.critical(parent, _('Kite error'), err_msg)

        self.sig_show_widget.emit(wrap_message)
        self.sig_disable_provider.emit(self.COMPLETION_PROVIDER_NAME)

    def create_statusbar(self, parent):
        return KiteStatusWidget(parent, self)
