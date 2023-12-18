# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License

"""
Status widget for Kite completions.
"""

# Standard library imports
import logging

# Spyder imports
from spyder.api.widgets.status import StatusBarWidget
from spyder.config.base import _
from spyder.utils.icon_manager import ima

# Local imports
from kite_provider.utils.status import (
    check_if_kite_installed, NOT_INSTALLED)

logger = logging.getLogger(__name__)


class KiteStatusWidget(StatusBarWidget):
    """Status bar widget for Kite completions status."""
    BASE_TOOLTIP = _("Kite completions status")
    DEFAULT_STATUS = _('not reachable')
    ID = 'kite_status'

    def __init__(self, parent, provider):
        self.provider = provider
        self.tooltip = self.BASE_TOOLTIP
        super().__init__(parent)
        is_installed, _ = check_if_kite_installed()
        self.setVisible(is_installed)

    def set_value(self, value):
        """Return Kite completions state."""
        kite_enabled = self.provider.get_conf(('enabled_providers', 'kite'),
                                              default=True,
                                              section='completions')

        if (value is not None and 'short' in value):
            self.tooltip = value['long']
            value = value['short']
        elif value is not None:
            self.setVisible(True)
            if value == NOT_INSTALLED:
                return
        elif value is None:
            value = self.DEFAULT_STATUS
            self.tooltip = self.BASE_TOOLTIP
        self.update_tooltip()
        self.setVisible(value != NOT_INSTALLED and kite_enabled)
        value = "Kite: {0}".format(value)
        super(KiteStatusWidget, self).set_value(value)

    def get_tooltip(self):
        """Reimplementation to get a dynamic tooltip."""
        return self.tooltip

    def get_icon(self):
        return ima.icon('kite')
