# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License

"""
Dialog widget for Langchain + OpenAI completions configs.
"""

# Standard library imports
import logging

# Third party imports
from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QSpinBox,
    QHBoxLayout,
    QVBoxLayout,
)

# Spyder imports
from spyder.api.translations import _

logger = logging.getLogger(__name__)


class LangchainConfigDialog(QDialog):
    def __init__(self, provider, parent=None):
        super().__init__(parent=parent)

        self._provider = provider

        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle(_("Langchain provider configuration"))
        self.setModal(True)

        suggestions_label_text = _("Suggestions number:")
        self.suggestions_spinbox = QSpinBox()
        self.suggestions_spinbox.setRange(1, 10)
        self.suggestions_spinbox.setSingleStep(1)
        self.suggestions_spinbox.setValue(provider.get_conf("suggestions"))

        model_label_text = _("Model name:")
        self.model_combobox = QComboBox()
        self.model_combobox.addItems(["gpt-3.5-turbo", "gpt-4"])
        self.model_combobox.setCurrentText(provider.get_conf("model_name"))

        form_layout = QFormLayout()
        form_layout.addRow(suggestions_label_text, self.suggestions_spinbox)
        form_layout.addRow(model_label_text, self.model_combobox)

        bbox = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Vertical, self
        )
        bbox.accepted.connect(self.accept)
        bbox.rejected.connect(self.reject)
        btn_layout = QVBoxLayout()
        btn_layout.addWidget(bbox)
        btn_layout.addStretch(1)

        layout = QHBoxLayout()
        layout.addLayout(form_layout)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

        self.suggestions_spinbox.setFocus()

    def accept(self):
        self._provider.set_conf("suggestions", self.suggestions_spinbox.value())
        self._provider.set_conf("model_name", self.model_combobox.currentText())
        super().accept()
