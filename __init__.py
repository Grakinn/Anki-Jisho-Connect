from .getgrknmenu import get_grkn_menu
# -*- coding: utf-8 -*-
"""
Anki Add-on: Anki Jisho Connect (v3.8.9)

Features:
- Modeless results window with integrated loading state.
- API requests run in a background thread to prevent UI freezes.
- Window is reused if already open.
"""
import os
import json
import requests
import urllib.parse
from typing import List, Any, Dict, Optional, Tuple

# Anki imports
from aqt import mw
from aqt.qt import (
    QAction, QMenu, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QGridLayout, QCheckBox, QScrollArea, QWidget, QFrame, QInputDialog,
    QLineEdit, Qt, QMessageBox, QIcon, QGroupBox, QSizePolicy,
    QThread, QObject, pyqtSignal, pyqtSlot, QApplication, QPixmap
)
from PyQt6.QtCore import QTimer, QPoint
from PyQt6.QtGui import QCursor
from aqt.utils import showInfo, showWarning
from aqt.gui_hooks import editor_did_init_buttons, theme_did_change
from aqt.theme import theme_manager

def get_themed_icon(icon_name: str) -> QIcon:
    """
    Creates a QIcon from an SVG string, with colors adapted to the current theme.
    """
    icon_svg = ""

    color = theme.TEXT_SECONDARY
    
    if icon_name == "arrow_up":
        icon_svg = f"""
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
            <path fill="{color}" d="M7.41 15.41L12 10.83l4.59 4.58L18 14l-6-6-6 6z"/>
        </svg>
        """
    elif icon_name == "arrow_down":
        icon_svg = f"""
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
            <path fill="{color}" d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6z"/>
        </svg>
        """
    elif icon_name == "remove":

        color = theme.DANGER_TEXT
        icon_svg = f"""
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
            <path fill="{color}" d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
        </svg>
        """

    if not icon_svg:
        return QIcon()

    pixmap = QPixmap()
    pixmap.loadFromData(icon_svg.encode("utf-8"))
    return QIcon(pixmap)

# -------------------------
# Style & Theme
# -------------------------
class LightTheme:
    # Primary Colors
    PRIMARY = "#007aff"
    PRIMARY_HOVER = "#005ecb"
    PRIMARY_TEXT = "#ffffff"

    # Secondary / Accent Colors
    ACCENT_YELLOW = "#ffc107"
    ACCENT_YELLOW_HOVER = "#e0a800"
    ACCENT_YELLOW_TEXT = "#333333"
    
    # Greyscale
    BACKGROUND = "#ffffff"
    BACKGROUND_ALT = "#f0f2f5"
    BACKGROUND_SEARCH = "#f7f7f7"
    BORDER = "#e0e0e0"
    BORDER_LIGHT = "#dddddd"
    BORDER_DARK = "#cccccc"
    
    # Text
    TEXT_PRIMARY = "#222222"
    TEXT_SECONDARY = "#555555"
    TEXT_TERTIARY = "#666666"
    TEXT_DISABLED = "#999999"
    
    # Feedback Colors
    SUCCESS = "#88cc88"
    SUCCESS_TEXT = "#005000"
    INFO = "#88bbff"
    INFO_TEXT = "#004080"
    WARNING = "#dd77ff"
    WARNING_TEXT = "#500080"
    DANGER = "#ffeaea"
    DANGER_TEXT = "#c00000"
    
    # Button / Control
    CONTROL_BG = "transparent"
    CONTROL_BORDER = "#dddddd"
    CONTROL_HOVER_BG = "#e0e0e0"
    CONTROL_HOVER_BORDER = "#cccccc"
    CONTROL_DISABLED_TEXT = "#cccccc"
    CONTROL_DISABLED_BORDER = "#eeeeee"
    
    # Other
    CONFIRM_DISABLED_BG = "#e9e9e9"

class DarkTheme:
    # Primary Colors
    PRIMARY = "#008aff"
    PRIMARY_HOVER = "#006cd1"
    PRIMARY_TEXT = "#ffffff"

    # Secondary / Accent Colors
    ACCENT_YELLOW = "#ffc107"
    ACCENT_YELLOW_HOVER = "#e0a800"
    ACCENT_YELLOW_TEXT = "#333333"
    
    # Greyscale
    BACKGROUND = "#2d2d2d"
    BACKGROUND_ALT = "#252525"
    BACKGROUND_SEARCH = "#3a3a3a"
    BORDER = "#4a4a4a"
    BORDER_LIGHT = "#404040"
    BORDER_DARK = "#555555"
    
    # Text
    TEXT_PRIMARY = "#f0f0f0"
    TEXT_SECONDARY = "#bbbbbb"
    TEXT_TERTIARY = "#999999"
    TEXT_DISABLED = "#777777"
    
    # Feedback Colors
    SUCCESS = "#77b677"
    SUCCESS_TEXT = "#d9f0d9"
    INFO = "#77aadd"
    INFO_TEXT = "#d9e8f7"
    WARNING = "#cc66ef"
    WARNING_TEXT = "#f4d9ff"
    DANGER = "#5c2e2e"
    DANGER_TEXT = "#ffc0c0"
    
    # Button / Control
    CONTROL_BG = "transparent"
    CONTROL_BORDER = "#555555"
    CONTROL_HOVER_BG = "#4f4f4f"
    CONTROL_HOVER_BORDER = "#666666"
    CONTROL_DISABLED_TEXT = "#666666"
    CONTROL_DISABLED_BORDER = "#444444"
    
    # Other
    CONFIRM_DISABLED_BG = "#4a4a4a"

theme = DarkTheme if theme_manager.night_mode else LightTheme

# -------------------------
# Translation System
# -------------------------
TRANSLATIONS = {
    "en": {
        # Config Dialog
        "settings_title": "GRKN Anki Jisho Connect Settings",
        "language": "Language:",
        "main_settings": "Main Settings",
        "note_type": "Note Type:",
        "search_field": "Search Field:",
        "fill_mode": "Fill Mode:",
        "fill_mode_replace": "Replace content",
        "fill_mode_append": "Append to content",
        "field_mapping": "Field Mapping (Jisho → Anki)",
        "add_mapping": "+ Add Mapping",
        "disable_warning": "Disable multi-word selection warning",
        "remove_pos_ending": "Remove 'with x ending' from Part of speech",
        "save_and_close": "Save and Close",
        "warning_fill_mappings": "Fill all mapping pairs before saving.",
        "info_settings_saved": "Settings saved!",

        # Results Dialog
        "results_title": "GRKN Anki Jisho Connect Result",
        "search_placeholder": "Enter any Japanese text or English word...",
        "search_button": "Search",
        "confirm_entry": "Confirm Entry",
        "loading_message": "Looking for results...",
        "loading_message_term": "Looking for '{term}'...",
        "no_results": "Sorry, nothing was found for '{term}'.",
        "other_forms": "Other forms:",
        "multi_word_warning_title": "You selected definitions from multiple words.",
        "multi_word_warning_body": "Meanings from multiple words will be added to the note.",
        "ok_dont_warn_again": "OK, don't warn me again",
        "info_fields_filled": "Fields filled successfully!",
        "button_ok": "OK",          
        "button_cancel": "Cancel",

        # Main Flow
        "input_dialog_title": "Search Jisho",
        "input_dialog_label": "Search term:",
        "editor_button_tooltip": "Search Jisho (Ctrl+Shift+J)",
        "warning_no_mappings": "No field mappings are configured. Please configure at least one mapping in the settings.",
    },
    "pt": {
        # Config Dialog
        "settings_title": "Configurações da GRKN Anki Jisho Connect",
        "language": "Idioma:",
        "main_settings": "Configurações Principais",
        "note_type": "Tipo de Nota:",
        "search_field": "Campo de Busca:",
        "fill_mode": "Modo de Preenchimento:",
        "fill_mode_replace": "Substituir conteúdo",
        "fill_mode_append": "Adicionar ao conteúdo",
        "field_mapping": "Mapeamento de Campos (Jisho → Anki)",
        "add_mapping": "+ Adicionar Mapeamento",
        "disable_warning": "Desativar aviso de seleção de múltiplas palavras",
        "remove_pos_ending": "Remover 'with x ending' de Classe Gramatical",
        "save_and_close": "Salvar e Fechar",
        "warning_fill_mappings": "Preencha todos os pares de mapeamento antes de salvar.",
        "info_settings_saved": "Configurações salvas!",

        # Results Dialog
        "results_title": "Resultado da GRKN Anki Jisho Connect",
        "search_placeholder": "Digite um texto em japonês ou uma palavra em inglês...",
        "search_button": "Buscar",
        "confirm_entry": "Confirmar Entrada",
        "loading_message": "Procurando resultados...",
        "loading_message_term": "Procurando por '{term}'...",
        "no_results": "Desculpe, não foi encontrado nada para '{term}'.",
        "other_forms": "Outras formas:",
        "multi_word_warning_title": "Você selecionou definições de múltiplas palavras.",
        "multi_word_warning_body": "Os significados de múltiplas palavras serão adicionados à nota.",
        "ok_dont_warn_again": "OK, não me avise novamente",
        "info_fields_filled": "Campos preenchidos com sucesso!",
        "button_ok": "OK",           
        "button_cancel": "Cancelar", 
        
        # Main Flow
        "input_dialog_title": "Buscar no Jisho",
        "input_dialog_label": "Termo de busca:",
        "editor_button_tooltip": "Buscar no Jisho (Ctrl+Shift+J)",
        "warning_no_mappings": "Nenhum mapeamento de campo está configurado. Por favor, configure ao menos um nas configurações.",
    }
}

current_language = "en"

def _(key: str) -> str:
    """Gets the translated string for the current language, falling back to English."""
    return TRANSLATIONS.get(current_language, {}).get(key, TRANSLATIONS["en"].get(key, key))

def set_language(lang_code: str):
    """Sets the global add-on language."""
    global current_language
    current_language = lang_code if lang_code in TRANSLATIONS else "en"

# -------------------------
# Global References
# -------------------------
ADDON_FOLDER = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(ADDON_FOLDER, "config.json")
_jisho_dialog_ref: Optional['ResultsDialog'] = None
_config_dialog_ref: Optional['ConfigDialog'] = None
_active_jisho_workers: List[Tuple[QThread, 'JishoFetchWorker']] = []

def update_theme():
    """Update the theme for all open windows when Anki's theme changes."""
    global theme
    theme = DarkTheme if theme_manager.night_mode else LightTheme
    
    if _jisho_dialog_ref and _jisho_dialog_ref.isVisible():
        _jisho_dialog_ref.restyle()
        
    if _config_dialog_ref and _config_dialog_ref.isVisible():
        _config_dialog_ref.restyle()

theme_did_change.append(update_theme)

# -------------------------
# Settings
# -------------------------
DEFAULT_CONFIG = {
    "language": "en",  
    "card_type": "",
    "search_field": "N/A",
    "mappings": {},
    "fill_mode": "replace",
    "disable_multi_word_warning": False,
    "remove_pos_ending": True
}

def load_config() -> Dict[str, Any]:
    """Load settings from file or return defaults."""
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            for key, value in DEFAULT_CONFIG.items():
                config.setdefault(key, value)
            return config
    except (json.JSONDecodeError, OSError):
        return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()

set_language(load_config().get("language", "en"))

def save_config(config: Dict[str, Any]):
    """Save settings to file."""
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

# -------------------------
# Settings Dialog
# -------------------------

class ConfigDialog(QDialog):
    """Dialog for configuring the add-on."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GRKN Anki Jisho Connect Settings")
        self.setMinimumWidth(500)
        
        self.config = load_config()
        self.mapping_rows_data = [] 

        self._setup_ui()

        self.restyle()

        self._connect_signals()

        self._load_initial_data()

    def _setup_ui(self):
        """Constrói a interface gráfica uma única vez."""
        main_layout = QVBoxLayout(self)
        self.setLayout(main_layout)
        main_layout.setSpacing(15)

        # --- Seletor de Idioma ---
        lang_layout = QHBoxLayout()
        self.lang_label = QLabel()
        lang_layout.addWidget(self.lang_label)
        self.lang_dropdown = QComboBox()
        self.lang_dropdown.addItems(["English", "Português"])
        self.lang_map = {0: "en", 1: "pt"}
        lang_layout.addWidget(self.lang_dropdown)
        main_layout.addLayout(lang_layout)

        # --- Grupo de Configurações Principais ---
        self.main_config_group = QGroupBox()
        main_config_layout = QGridLayout(self.main_config_group)
        main_config_layout.setSpacing(10)
        
        self.note_type_label = QLabel()
        main_config_layout.addWidget(self.note_type_label, 0, 0)
        self.card_type_dropdown = QComboBox()
        self.card_type_names = sorted(mw.col.models.all_names())
        self.card_type_dropdown.addItems([""] + self.card_type_names)
        main_config_layout.addWidget(self.card_type_dropdown, 0, 1)

        self.search_field_label = QLabel()
        main_config_layout.addWidget(self.search_field_label, 1, 0)
        self.search_field_dropdown = QComboBox()
        main_config_layout.addWidget(self.search_field_dropdown, 1, 1)

        self.fill_mode_label = QLabel()
        main_config_layout.addWidget(self.fill_mode_label, 2, 0)
        self.fill_mode_dropdown = QComboBox()
        main_config_layout.addWidget(self.fill_mode_dropdown, 2, 1)
        
        main_layout.addWidget(self.main_config_group)

        # --- Grupo de Mapeamento de Campos ---
        self.mapping_group = QGroupBox()
        mapping_group_layout = QVBoxLayout(self.mapping_group)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(100)
        scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        scroll_content = QWidget()
        scroll_content.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self.mapping_grid_layout = QGridLayout(scroll_content)
        self.mapping_grid_layout.setSpacing(5)
        scroll_area.setWidget(scroll_content)
        
        mapping_group_layout.addWidget(scroll_area)

        self.add_btn = QPushButton()
        self.add_btn.setStyleSheet("padding: 5px;")
        mapping_group_layout.addWidget(self.add_btn)
        
        main_layout.addWidget(self.mapping_group)

        # --- Opções Adicionais e Botão Salvar ---
        self.warn_checkbox = QCheckBox()
        self.remove_pos_checkbox = QCheckBox()
        self.save_button = QPushButton()
        self.save_button.setStyleSheet("padding: 8px; font-weight: bold;")
        
        main_layout.addWidget(self.warn_checkbox)
        main_layout.addWidget(self.remove_pos_checkbox)
        main_layout.addWidget(self.save_button)

        self.scroll_area = scroll_area

        self._retranslate_ui()

    def _retranslate_ui(self):
        """Atualiza todo o texto da UI para o idioma atual."""
        self.setWindowTitle(_("settings_title"))
        self.lang_label.setText(_("language"))
        
        self.main_config_group.setTitle(_("main_settings"))
        self.note_type_label.setText(_("note_type"))
        self.search_field_label.setText(_("search_field"))
        self.fill_mode_label.setText(_("fill_mode"))
        
        current_fill_mode_index = self.fill_mode_dropdown.currentIndex()
        self.fill_mode_dropdown.clear()
        self.fill_mode_dropdown.addItems([_("fill_mode_replace"), _("fill_mode_append")])
        if current_fill_mode_index != -1:
            self.fill_mode_dropdown.setCurrentIndex(current_fill_mode_index)
        
        self.mapping_group.setTitle(_("field_mapping"))
        self.add_btn.setText(_("add_mapping"))
        self.warn_checkbox.setText(_("disable_warning"))
        self.remove_pos_checkbox.setText(_("remove_pos_ending"))
        self.save_button.setText(_("save_and_close"))

    def _language_changed(self):
        """Chamado quando o idioma é alterado no dropdown."""
        lang_code = self.lang_map.get(self.lang_dropdown.currentIndex(), "en")
        set_language(lang_code)
        
        self._retranslate_ui()
        
        if _jisho_dialog_ref and _jisho_dialog_ref.isVisible():
            _jisho_dialog_ref._retranslate_ui()

    def restyle(self):
        """Aplica/atualiza estilos com base no tema, SEM recriar os widgets."""
        icon_path = os.path.join(ADDON_FOLDER, "jisho_icon.svg")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        group_box_style = f"""
            QGroupBox {{
                border: 1px solid {theme.BORDER_DARK};
                border-radius: 4px;
                margin-top: 9px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 4px;
                left: 8px;
            }}
        """
        self.main_config_group.setStyleSheet(group_box_style)
        self.mapping_group.setStyleSheet(group_box_style)

        self.scroll_area.setStyleSheet(f"QScrollArea {{ border: 1px solid {theme.BORDER_LIGHT}; border-radius: 4px; }}")

        self._rebuild_mapping_grid()

    def _connect_signals(self):
        """Conecta todos os sinais aos seus slots."""
        self.lang_dropdown.currentIndexChanged.connect(self._language_changed)
        self.card_type_dropdown.currentIndexChanged.connect(self.update_fields)
        self.add_btn.clicked.connect(self.add_mapping_row)
        self.save_button.clicked.connect(self.save_config_clicked)

    def _load_initial_data(self):
        """Carrega os dados da configuração na interface."""
        lang_code = self.config.get("language", "en")
        lang_index = 0
        for index, code in self.lang_map.items():
            if code == lang_code:
                lang_index = index
                break
        self.lang_dropdown.setCurrentIndex(lang_index)

        self.card_type_dropdown.setCurrentText(self.config.get("card_type", ""))
        self.fill_mode_dropdown.setCurrentIndex(1 if self.config.get("fill_mode") == "append" else 0)
        self.warn_checkbox.setChecked(self.config.get("disable_multi_word_warning", False))
        self.remove_pos_checkbox.setChecked(self.config.get("remove_pos_ending", True))
        
        self.update_fields() 
        self.load_mapping_rows()

    def _clear_layout(self, layout):
        """Remove todos os widgets de um layout."""
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _rebuild_mapping_grid(self):
        """Limpa e recria o grid de mapeamento com base em self.mapping_rows_data."""
        self._clear_layout(self.mapping_grid_layout)
        
        jisho_options = ["", "Word", "Reading", "Meaning", "Part of speech", "Info", "Tags", "Other forms", "JLPT Level", "Wanikani Level", "Is_Common"]
        reorder_button_style = f"..." 
        remove_button_style = f"..." 

        for row_index, row_data in enumerate(self.mapping_rows_data):
            left_value, right_value = row_data['jisho'], row_data['field']

            up_btn = QPushButton(icon=get_themed_icon("arrow_up"))
            up_btn.setFixedSize(30, 30)
            up_btn.setStyleSheet(reorder_button_style)
            
            down_btn = QPushButton(icon=get_themed_icon("arrow_down"))
            down_btn.setFixedSize(30, 30)
            down_btn.setStyleSheet(reorder_button_style)
            
            left_combo = QComboBox(); left_combo.addItems(jisho_options)
            arrow_label = QLabel("→"); arrow_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            right_combo = QComboBox(); right_combo.addItems([""] + self.current_field_names)
            
            remove_btn = QPushButton(icon=get_themed_icon("remove"))
            remove_btn.setFixedSize(30, 30)
            remove_btn.setStyleSheet(remove_button_style)

            left_combo.setCurrentText(left_value)
            right_combo.setCurrentText(right_value)

            up_btn.clicked.connect(lambda _, idx=row_index: self._move_row(idx, -1))
            down_btn.clicked.connect(lambda _, idx=row_index: self._move_row(idx, 1))
            remove_btn.clicked.connect(lambda _, idx=row_index: self._remove_row(idx))

            left_combo.currentTextChanged.connect(lambda text, idx=row_index: self.mapping_rows_data[idx].update({"jisho": text}))
            right_combo.currentTextChanged.connect(lambda text, idx=row_index: self.mapping_rows_data[idx].update({"field": text}))
            
            self.mapping_grid_layout.addWidget(up_btn, row_index, 0)
            self.mapping_grid_layout.addWidget(down_btn, row_index, 1)
            self.mapping_grid_layout.addWidget(left_combo, row_index, 2)
            self.mapping_grid_layout.addWidget(arrow_label, row_index, 3)
            self.mapping_grid_layout.addWidget(right_combo, row_index, 4)
            self.mapping_grid_layout.addWidget(remove_btn, row_index, 5)

        self.mapping_grid_layout.setColumnStretch(2, 1)
        self.mapping_grid_layout.setColumnStretch(4, 1)

        for i in range(len(self.mapping_rows_data)):
            self.mapping_grid_layout.setRowStretch(i, 0)
        self.mapping_grid_layout.setRowStretch(len(self.mapping_rows_data), 1)

        self._update_button_states()

    def add_mapping_row(self):
        """Adiciona um novo mapeamento à lista de dados e reconstrói o grid."""
        self.mapping_rows_data.append({"jisho": "", "field": ""})
        self._rebuild_mapping_grid()

    def _remove_row(self, index):
        """Remove uma linha da lista de dados e reconstrói o grid."""
        if 0 <= index < len(self.mapping_rows_data):
            del self.mapping_rows_data[index]
            self._rebuild_mapping_grid()
            
    def _move_row(self, index, direction):
        """Move uma linha, reconstrói o grid e agenda o posicionamento do cursor."""
        if not (0 <= index < len(self.mapping_rows_data)):
            return
        
        new_index = index + direction
        if not (0 <= new_index < len(self.mapping_rows_data)):
            return

        self.mapping_rows_data.insert(new_index, self.mapping_rows_data.pop(index))

        self._rebuild_mapping_grid()

        target_column = 0 if direction == -1 else 1
        
        target_item = self.mapping_grid_layout.itemAtPosition(new_index, target_column)

        if target_item and target_item.widget():
            target_button = target_item.widget()

            QTimer.singleShot(0, lambda: self._position_cursor_on_widget(target_button))

    def _position_cursor_on_widget(self, widget):
        """Calcula o centro de um widget e posiciona o cursor do mouse sobre ele."""
        if not widget:
            return

        button_center = widget.rect().center()

        global_pos = widget.mapToGlobal(button_center)

        QCursor.setPos(global_pos)

    def _update_button_states(self):
        """Habilita/desabilita botões de mover com base na posição."""
        count = self.mapping_grid_layout.rowCount() -1 
        for i in range(count):
            up_btn_item = self.mapping_grid_layout.itemAtPosition(i, 0)
            down_btn_item = self.mapping_grid_layout.itemAtPosition(i, 1)
            if up_btn_item and down_btn_item:
                up_btn_item.widget().setEnabled(i > 0)
                down_btn_item.widget().setEnabled(i < count - 1)

    def update_fields(self):
        """Atualiza a lista de campos com base no tipo de nota selecionado."""
        model_name = self.card_type_dropdown.currentText()
        self.current_field_names = []
        if model_name:
            model = mw.col.models.by_name(model_name)
            if model:
                self.current_field_names = [fld["name"] for fld in model["flds"]]
        
        self.search_field_dropdown.clear()
        self.search_field_dropdown.addItems(self.current_field_names)
        
        saved_search = self.config.get("search_field", "")
        if saved_search in self.current_field_names:
            self.search_field_dropdown.setCurrentText(saved_search)

        self._rebuild_mapping_grid()

    def load_mapping_rows(self):
        """Carrega os mapeamentos da config para a lista de dados."""
        mappings = self.config.get("mappings", [])
        
        if isinstance(mappings, dict):
            self.mapping_rows_data = [{"jisho": jisho, "field": field} for field, jisho in mappings.items()]
        elif isinstance(mappings, list):
            self.mapping_rows_data = mappings
        else:
            self.mapping_rows_data = []

        self._rebuild_mapping_grid()

    def save_config_clicked(self):
        """Valida e salva a configuração."""
        for mapping in self.mapping_rows_data:
            if not mapping["jisho"] or not mapping["field"]:
                showWarning(_("warning_fill_mappings"))
                return
        
        lang_code = self.lang_map.get(self.lang_dropdown.currentIndex(), "en")
        self.config.update({
            "language": lang_code,
            "card_type": self.card_type_dropdown.currentText(),
            "search_field": self.search_field_dropdown.currentText(),
            "mappings": self.mapping_rows_data,
            "fill_mode": "append" if self.fill_mode_dropdown.currentIndex() == 1 else "replace",
            "disable_multi_word_warning": self.warn_checkbox.isChecked(),
            "remove_pos_ending": self.remove_pos_checkbox.isChecked()
        })
        save_config(self.config)
        showInfo(_("info_settings_saved"))
        self.close()

# -------------------------
# Jisho API & Worker
# -------------------------
def fetch_from_jisho(term: str) -> Optional[List[Dict[str, Any]]]:
    """Fetch results from Jisho API."""
    if not term:
        return None
    try:
        url = f"https://jisho.org/api/v1/search/words?keyword={urllib.parse.quote(term)}"
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return data.get("data") if data.get("meta", {}).get("status") == 200 else None
    except requests.RequestException as e:
        showWarning(f"Error fetching from Jisho: {e}")
        return None

class JishoFetchWorker(QObject):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, term: str):
        super().__init__()
        self.term = term

    @pyqtSlot()
    def run(self):
        try:
            entries = fetch_from_jisho(self.term)
            self.finished.emit(entries or [])
        except Exception as e:
            self.error.emit(str(e))

# -------------------------
# Results Dialog
# -------------------------
class ResultsDialog(QDialog):
    """Dialog to display Jisho search results."""
    def __init__(self, initial_term: str, on_select):
        super().__init__()
        self.is_loading = False
        self.on_select = on_select
        self.initial_term = initial_term
        self.entry_widgets = []
        self.setWindowTitle("GRKN Anki Jisho Connect Result")
        self.setMinimumSize(700, 750)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)

        self.restyle()

        if self.initial_term:
            self.perform_search(self.initial_term)

    def restyle(self):
        """Re-applies all styles to the dialog based on the current theme."""

        search_text = self.search_box.text() if hasattr(self, "search_box") else self.initial_term

        while self.layout().count():
            item = self.layout().takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        self.setStyleSheet(f"""
            ResultsDialog {{
                background-color: {theme.BACKGROUND};
            }}
            QCheckBox {{
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
            }}
            QLabel {{
                font-family: "Segoe UI", "Helvetica", "Arial", sans-serif;
                color: {theme.TEXT_PRIMARY};
            }}
        """)
        icon_path = os.path.join(ADDON_FOLDER, "jisho_icon.svg")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.layout().setAlignment(Qt.AlignmentFlag.AlignTop)
        
        search_widget = QWidget()
        search_widget.setObjectName("searchWidget")
        search_widget.setStyleSheet(f"""
            #searchWidget {{
                background-color: {theme.BACKGROUND_SEARCH};
                border-bottom: 1px solid {theme.BORDER};
                padding: 8px 12px;
            }}
            QLineEdit {{
                font-size: 14px;
                padding: 8px;
                border: 1px solid {theme.BORDER_DARK};
                border-radius: 4px;
                background-color: {theme.BACKGROUND};
                color: {theme.TEXT_PRIMARY};
            }}
            QPushButton {{
                font-size: 14px;
                padding: 8px 16px;
                background-color: {theme.PRIMARY};
                color: {theme.PRIMARY_TEXT};
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {theme.PRIMARY_HOVER};
            }}
        """)
        search_layout = QHBoxLayout(search_widget)
        self.search_box = QLineEdit(search_text)

        self.search_box.setPlaceholderText(_("search_placeholder"))
        self.search_box.returnPressed.connect(self.perform_search)
        search_layout.addWidget(self.search_box)

        self.search_button = QPushButton(_("search_button"))
        self.search_button.clicked.connect(self.perform_search)
        search_layout.addWidget(self.search_button)
        self.layout().addWidget(search_widget)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")
        self.layout().addWidget(scroll_area)
        
        results_container = QWidget()
        results_container.setObjectName("resultsContainer")
        results_container.setStyleSheet(f"#resultsContainer {{ background-color: {theme.BACKGROUND_ALT}; }}")
        self.results_layout = QVBoxLayout(results_container)
        self.results_layout.setContentsMargins(15, 15, 15, 15)
        self.results_layout.setSpacing(15)
        self.results_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_area.setWidget(results_container)

        self.confirm_btn = QPushButton(_("confirm_entry"))
        self.confirm_btn.setEnabled(False)
        self.confirm_btn.clicked.connect(self.confirm_selection)
        self.confirm_btn.setObjectName("confirmButton")
        self.layout().addWidget(self.confirm_btn)

        current_entries = [item["entry_data"] for item in self.entry_widgets]
        self.clear_results(rebuild=False)
        if current_entries:
            for entry in current_entries:
                self.create_entry_widget(entry)
            self.results_layout.addStretch()
        
        self.update_confirm_button_state()

        self._retranslate_ui()

    def _retranslate_ui(self):
        """Atualiza o texto da UI sem recriar os widgets."""
        self.setWindowTitle(_("results_title"))
        if hasattr(self, "search_box"):
            self.search_box.setPlaceholderText(_("search_placeholder"))
        if hasattr(self, "search_button"):
            self.search_button.setText(_("search_button"))
        if hasattr(self, "confirm_btn"):
            if not self.is_loading:
                self.confirm_btn.setText(_("confirm_entry"))

    def show_loading_state(self, message: str = "") -> None:
        """Mostra uma mensagem de carregamento na área de resultados."""
        self.is_loading = True
        effective_message = message or _("loading_message")
        self.clear_results()
        loading_label = QLabel(f"<h3>{effective_message}</h3>")
        loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.results_layout.addWidget(loading_label)
        self.results_layout.addStretch()
        self.search_box.setEnabled(False)
        self.confirm_btn.setEnabled(False)
        self.search_button.setEnabled(False)
        self.confirm_btn.setText(_("loading_message"))
        QApplication.processEvents()

    def hide_loading_state(self) -> None:
        """Reabilita os controles após a busca."""
        self.is_loading = False
        self.search_box.setEnabled(True)
        self.confirm_btn.setEnabled(True)
        self.search_button.setEnabled(True)
        self.confirm_btn.setText(_("confirm_entry"))

    def perform_search(self, term: Optional[str] = None):
        """Perform a Jisho search and display results using a worker thread."""
        search_term = term if isinstance(term, str) else self.search_box.text()
        if not search_term:
            return

        self.show_loading_state(_("loading_message_term").format(term=search_term))

        thread = QThread()
        worker = JishoFetchWorker(search_term)
        worker.moveToThread(thread)

        def on_finished(entries: list):
            self.hide_loading_state()
            self.clear_results()

            if not entries:
                no_results_label = QLabel(f"<h3>{_('no_results').format(term=search_term)}</h3>")
                no_results_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.results_layout.addWidget(no_results_label)
            else:
                for entry in entries:
                    self.create_entry_widget(entry)

                self.results_layout.addStretch()

            worker.deleteLater()
            thread.quit()
            thread.wait()
            thread.deleteLater()

        def on_error(err_msg: str):
            self.hide_loading_state()
            self.clear_results()
            showWarning(f"Erro na busca: {err_msg}")
            worker.deleteLater()
            thread.quit()
            thread.wait()
            thread.deleteLater()

        worker.finished.connect(on_finished)
        worker.error.connect(on_error)
        thread.started.connect(worker.run)

        global _active_jisho_workers
        _active_jisho_workers.append((thread, worker))

        def cleanup():
            item_to_remove = None
            for item in _active_jisho_workers:
                if item[0] == thread:
                    item_to_remove = item
                    break
            if item_to_remove:
                _active_jisho_workers.remove(item_to_remove)
        
        thread.finished.connect(cleanup)
        
        thread.start()

    def _create_tag_widget(self, text: str, bg_color: str, fg_color: str) -> QWidget:
        """Create a styled tag widget."""
        tag_widget = QWidget()
        tag_widget.setAutoFillBackground(True)
        qss = f"""
            QWidget {{
                background-color: {bg_color};
                color: {fg_color};
                padding: 0 15px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 600;
                border: 1px solid {bg_color};
            }}
        """
        tag_widget.setStyleSheet(qss)
        tag_layout = QHBoxLayout(tag_widget)
        tag_layout.setContentsMargins(0, 0, 0, 0)
        tag_layout.setSpacing(0)
        tag_label = QLabel(text)
        tag_label.setStyleSheet(f"color: {fg_color}; background: transparent;") 
        tag_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tag_layout.addWidget(tag_label)
        tag_widget.setFixedHeight(24)
        return tag_widget

    def create_entry_widget(self, entry: Dict[str, Any]):
        """Create a card widget for a Jisho entry."""
        if not entry.get("japanese"):
            return
        entry_card = QFrame()
        entry_card.setObjectName("entryCard")
        entry_card.setStyleSheet(f"""
            #entryCard {{
                background-color: {theme.BACKGROUND};
                border: 1px solid {theme.BORDER};
                border-radius: 8px;
            }}
        """)
        layout = QVBoxLayout(entry_card)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        word = entry["japanese"][0].get("word", "")
        reading = entry["japanese"][0].get("reading", "")
        header_layout = QHBoxLayout()
        header_layout.setSpacing(5)
        word_label = QLabel(word or reading)
        word_label.setStyleSheet(f"font-size: 32px; font-weight: 600; color: {theme.TEXT_PRIMARY};")
        header_layout.addWidget(word_label, alignment=Qt.AlignmentFlag.AlignBottom)
        if word and reading and word != reading:
            reading_label = QLabel(reading)
            reading_label.setStyleSheet(f"font-size: 18px; color: {theme.TEXT_SECONDARY}; padding-bottom: 3px;")
            header_layout.addWidget(reading_label, alignment=Qt.AlignmentFlag.AlignBottom)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        tags_layout = QHBoxLayout()
        tags_layout.setSpacing(7)
        # Exibe is_common, JLPT e Wanikani se existirem
        if entry.get("is_common"):
            tags_layout.addWidget(self._create_tag_widget("common word", theme.SUCCESS, theme.SUCCESS_TEXT))
        if entry.get("jlpt"):
            for tag in entry.get("jlpt", []):
                tags_layout.addWidget(self._create_tag_widget(tag, theme.INFO, theme.INFO_TEXT))
        if entry.get("tags"):
            for tag in entry.get("tags", []):
                if "wanikani" in tag:
                    tags_layout.addWidget(self._create_tag_widget(tag, theme.WARNING, theme.WARNING_TEXT))
        tags_layout.addStretch()
        layout.addLayout(tags_layout)
        sense_checkboxes = []
        sense_tag_checkboxes = []
        for i, sense in enumerate(entry.get("senses", [])):
            sense_widget = QWidget()
            sense_hlayout = QHBoxLayout(sense_widget)
            sense_hlayout.setContentsMargins(0, 0, 0, 0)
            sense_hlayout.setSpacing(8)
            sense_hlayout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            cb = QCheckBox()
            cb.stateChanged.connect(self.update_confirm_button_state)
            sense_checkboxes.append(cb)
            sense_hlayout.addWidget(cb, alignment=Qt.AlignmentFlag.AlignTop)

            vbox = QVBoxLayout()
            vbox.setContentsMargins(0, 0, 0, 0)
            vbox.setSpacing(2)

            # 1. Parts of Speech
            pos = ", ".join(sense.get("parts_of_speech", []))
            if pos:
                pos_label = QLabel(f"<i style='color: {theme.TEXT_TERTIARY};'>{pos}</i>")
                vbox.addWidget(pos_label)

            # 2. English Definitions
            defs = "; ".join(sense.get("english_definitions", []))
            def_label = QLabel(f"<b>{i+1}.</b> {defs}")
            def_label.setWordWrap(True)
            vbox.addWidget(def_label)

            # 3. Tags + Info (texto estilizado, mesma linha, alinhados à esquerda)
            all_tags_info = []
            if sense.get("tags"):
                all_tags_info.extend(sense["tags"])
            if sense.get("info"):
                all_tags_info.extend(sense["info"])
            
            if all_tags_info:
                combined_text = ", ".join([item.replace('\n', ' ').replace('\r', '') for item in all_tags_info])
                tag_info_label = QLabel(combined_text)
                tag_info_label.setStyleSheet(f"color: {theme.TEXT_SECONDARY}; font-style: italic; font-size: 12px;")
                tag_info_label.setWordWrap(True)
                tag_info_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
                vbox.addWidget(tag_info_label)

            sense_hlayout.addLayout(vbox, 1)
            layout.addWidget(sense_widget)
            
        other_forms_checkboxes = []
        if other_forms := [f for f in entry.get("japanese", [])[1:] if f.get("word") or f.get("reading")]:
            other_forms_label = QLabel(f"<b style='font-size: 14px; margin-top: 10px;'>{_('other_forms')}</b>")
            layout.addWidget(other_forms_label)
            for form in other_forms:
                cb = QCheckBox(f"{form.get('word', '')} [{form.get('reading', '')}]")
                cb.stateChanged.connect(self.update_confirm_button_state)
                other_forms_checkboxes.append(cb)
                layout.addWidget(cb)
        self.results_layout.addWidget(entry_card)
        self.entry_widgets.append({
            "widget": entry_card,
            "sense_checkboxes": sense_checkboxes,
            "sense_tag_checkboxes": sense_tag_checkboxes,
            "other_forms_checkboxes": other_forms_checkboxes,
            "entry_data": entry
        })

    def update_confirm_button_state(self):
        """Update confirm button state based on selection."""
        any_checked = any(cb.isChecked() for item in self.entry_widgets for key in ("sense_checkboxes", "other_forms_checkboxes") for cb in item.get(key, []))
        self.confirm_btn.setEnabled(any_checked)
        if any_checked:
            base_style = f"""
                QPushButton {{
                    margin: 12px; padding: 12px; font-size: 16px; font-weight: bold; border-radius: 6px;
                    border: 1px solid {theme.PRIMARY_HOVER};
                }}
                QPushButton:hover {{
                    background-color: {theme.PRIMARY_HOVER};
                }}
            """
            checked_entry_indices = {i for i, item in enumerate(self.entry_widgets) if any(cb.isChecked() for cb in item.get("sense_checkboxes", []))}
            if len(checked_entry_indices) > 1:
                self.confirm_btn.setStyleSheet(base_style + f"""
                    QPushButton {{
                        background-color: {theme.ACCENT_YELLOW};
                        color: {theme.ACCENT_YELLOW_TEXT};
                        border-color: {theme.ACCENT_YELLOW_HOVER};
                    }}
                    QPushButton:hover {{
                        background-color: {theme.ACCENT_YELLOW_HOVER};
                    }}
                """)
            else:
                self.confirm_btn.setStyleSheet(base_style + f"""
                    QPushButton {{
                        background-color: {theme.PRIMARY};
                        color: {theme.PRIMARY_TEXT};
                    }}
                """)
        else:
            self.confirm_btn.setStyleSheet(f"""
                QPushButton {{
                    margin: 12px; padding: 12px; font-size: 16px; font-weight: bold;
                    border-radius: 6px;
                    background-color: {theme.CONFIRM_DISABLED_BG};
                    color: {theme.TEXT_DISABLED};
                    border: 1px solid {theme.BORDER_LIGHT};
                }}
            """)

    def confirm_selection(self):
        """Handle confirm button click and fill note fields."""
        config = load_config()
        mappings = config.get("mappings", [])
        if not mappings:
            showWarning(_("warning_no_mappings"))
            return
        checked_entries_indices = [i for i, item in enumerate(self.entry_widgets) if any(cb.isChecked() for cb in item.get("sense_checkboxes", []))]
        if not config.get("disable_multi_word_warning", False) and len(checked_entries_indices) > 1:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setText(_("multi_word_warning_title"))
            msg_box.setInformativeText(_("multi_word_warning_body"))

            ok_button = msg_box.addButton(_("button_ok"), QMessageBox.ButtonRole.AcceptRole)
            cancel_button = msg_box.addButton(_("button_cancel"), QMessageBox.ButtonRole.RejectRole)
            dont_warn_again_button = msg_box.addButton(_("ok_dont_warn_again"), QMessageBox.ButtonRole.ActionRole)

            msg_box.exec() 

            clicked = msg_box.clickedButton()

            if clicked == cancel_button:
                return 
            
            if clicked == dont_warn_again_button:
                config["disable_multi_word_warning"] = True
                save_config(config)
        any_inserted = False
        for item in self.entry_widgets:
            selected_senses = [item["entry_data"]["senses"][i] for i, cb in enumerate(item.get("sense_checkboxes", [])) if cb.isChecked()]
            selected_other_forms = [cb.text() for cb in item.get("other_forms_checkboxes", []) if cb.isChecked()]
            if selected_senses or selected_other_forms:
                self.on_select(item["entry_data"], selected_senses, selected_other_forms)
                any_inserted = True
        if any_inserted:
            showInfo(_("info_fields_filled"))
            try:
                mw.reset()
            except Exception:
                pass
        self.close()

    def clear_results(self, rebuild: bool = True):
        """Clear all result widgets and stretch items from the layout."""

        if hasattr(self, "results_layout") and self.results_layout:
            while (item := self.results_layout.takeAt(0)):
                if (widget := item.widget()):
                    widget.deleteLater()
        
        if rebuild:
            self.entry_widgets.clear()
            self.update_confirm_button_state() 

# -------------------------
# Apply Mappings & Fill Note
# -------------------------
def apply_mappings_and_fill(note, entry: Dict[str, Any], selected_senses, selected_other_forms):
    """Apply mappings and fill note fields."""
    config = load_config()
    mappings = config.get("mappings", [])
    fill_mode = config.get("fill_mode", "replace")

    def set_field(field_name: str, value: str):
        if not value or field_name not in note:
            return
        # Lógica de preenchimento (append/replace)
        current_content = note[field_name]
        if fill_mode == 'append' and current_content and value not in current_content:
            # Para evitar duplicatas e espaços desnecessários
            if current_content.endswith(' '):
                note[field_name] += value
            else:
                note[field_name] += f" {value}"
        else:
            note[field_name] = value

    first_jap = entry["japanese"][0]
    field_values = {}

    import re
    for mapping in mappings:
        field_name = mapping.get("field", "")
        map_type = mapping.get("jisho", "")
        if not field_name or not map_type:
            continue

        value = ""
        if map_type == "Part of speech":
            # Coleta as 'parts of speech' mantendo a ordem e removendo duplicatas
            ordered_pos = []
            remove_ending = config.get("remove_pos_ending", True)
            for s in selected_senses:
                for pos in s.get("parts_of_speech", []):
                    if remove_ending:
                        pos = re.sub(r" with '.*?' ending", "", pos)
                    if pos not in ordered_pos:
                        ordered_pos.append(pos)
            value = "; ".join(ordered_pos)
        elif map_type == "Meaning":
            value = " | ".join(["; ".join(s.get("english_definitions", [])) for s in selected_senses])
        elif map_type == "Info":
            ordered_info = []
            for s in selected_senses:
                for info in s.get("info", []):
                    if info not in ordered_info:
                        ordered_info.append(info)
            value = "; ".join(ordered_info)
        elif map_type == "Tags":
            ordered_tags = []
            for s in selected_senses:
                for tag in s.get("tags", []):
                    if tag not in ordered_tags:
                        ordered_tags.append(tag)
            value = "; ".join(ordered_tags)
        elif map_type == "Other forms":
            value = ", ".join(selected_other_forms) if selected_other_forms else ""
        elif map_type == "Word":
            value = first_jap.get("word", "")
        elif map_type == "Reading":
            value = first_jap.get("reading", "")
        elif map_type == "JLPT Level":
            value = ", ".join(entry.get("jlpt", [])) if entry.get("jlpt") else ""
        elif map_type == "Wanikani Level":
            # Esta lógica já estava correta, buscando apenas as tags de "wanikani" no nível principal.
            value = ", ".join([tag for tag in entry.get("tags", []) if "wanikani" in tag]) if entry.get("tags") else ""
        elif map_type == "Is_Common":
            value = "common word" if entry.get("is_common") else ""

        if value:
            field_values.setdefault(field_name, []).append(value)

    for field_name, values in field_values.items():
        print(f"Preenchendo campo {field_name} com valores: {values}")
        final_text = "; ".join(v for v in values if v)
        set_field(field_name, final_text)

    try:
        if note.id == 0:
            # Nova nota - adicionar à coleção
            mw.col.add_note(note, mw.col.decks.current()['id'])
        else:
            # Nota existente - atualizar
            mw.col.update_note(note)
    except Exception as e:
        showWarning(f"Error saving note: {str(e)}")

# -------------------------
# Main Lookup Flow & Hooks
# -------------------------
def start_lookup_for_note(note):
    """Start lookup for a note or open config dialog."""
    global _config_dialog_ref, _jisho_dialog_ref

    if not note:
        if _config_dialog_ref and _config_dialog_ref.isVisible():
            _config_dialog_ref.raise_()
            _config_dialog_ref.activateWindow()
        else:
            dlg = ConfigDialog()
            _config_dialog_ref = dlg
            dlg.exec()
        return
    
    config = load_config()
    search_field = config.get("search_field", "N/A")
    term = note[search_field] if search_field in note else ""
    if not term:
        term, ok = QInputDialog.getText(mw, _("input_dialog_title"), _("input_dialog_label"))
        if not ok or not term:
            return
    
    if _jisho_dialog_ref and _jisho_dialog_ref.isVisible():
        _jisho_dialog_ref.search_box.setText(term)
        _jisho_dialog_ref.perform_search()
        _jisho_dialog_ref.raise_()
        _jisho_dialog_ref.activateWindow()
    else:
        dlg = ResultsDialog(term, lambda entry, senses, forms: apply_mappings_and_fill(note, entry, senses, forms))
        _jisho_dialog_ref = dlg
        dlg.show()

def add_jisho_editor_button(buttons: List[Any], editor: Any):
    """Add Jisho button to Anki editor."""
    icon_path = os.path.join(ADDON_FOLDER, "jisho_icon.svg")
    if not os.path.exists(icon_path):
        os.makedirs(os.path.dirname(icon_path), exist_ok=True)
        svg = """
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'>
  <rect width='24' height='24' rx='5' fill='#3ec97a'/>
  <text x='12' y='16' font-family='Segoe UI, Arial, sans-serif' font-size='13' fill='white' text-anchor='middle' font-weight='bold' letter-spacing='1'>JI</text>
</svg>
"""
        with open(icon_path, "w", encoding="utf-8") as f:
            f.write(svg)
    btn = editor.addButton(icon=icon_path, cmd="jisho_search", tip=_("editor_button_tooltip"), func=lambda e: start_lookup_for_note(e.note), keys="Ctrl+Shift+J")
    buttons.append(btn)
    return buttons

def setup_menu_action():
    """Add GRKN Anki Jisho Connect Settings to shared GRKN menu (creates if needed)."""
    action = QAction(_("settings_title"), mw)
    
    def show_dialog():
        global _config_dialog_ref
        if _config_dialog_ref and _config_dialog_ref.isVisible():
            _config_dialog_ref.raise_()
            _config_dialog_ref.activateWindow()
        else:
            dlg = ConfigDialog()
            _config_dialog_ref = dlg
            dlg.exec()

    action.triggered.connect(show_dialog)
    grkn_menu = get_grkn_menu(mw)
    if grkn_menu:
        grkn_menu.addAction(action)
    else:
        mw.form.menuTools.addAction(action)

editor_did_init_buttons.append(add_jisho_editor_button)
setup_menu_action()
