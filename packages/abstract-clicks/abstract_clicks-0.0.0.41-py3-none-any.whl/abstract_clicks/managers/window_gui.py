#!/usr/bin/env python3
"""Window Manager GUI
====================
A PyQt5 front‑end that wraps the *abstract_clicks* window‑handling utilities.

Capabilities
------------
* **Search** existing windows by partial title (live filter).
* **Filter or Select‑All by type** (Browser / Editor / Terminal / Other).
* **Checkbox list** lets you pick individual windows.
* **Close Selected** gracefully closes every checked window – with a quick
  confirmation if we suspect the document has unsaved changes.

This version fixes the *TypeError: unhashable type 'QListWidgetItem'* by
**embedding the window‑info dict in the QListWidgetItem via `Qt.UserRole`**
instead of storing an external dict keyed by the (unhashable) widget.
"""

from __future__ import annotations

import os
import platform
import subprocess
import sys
from typing import Any, Dict, List

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QLineEdit,
)

# ---------------------------------------------------------------------------
# abstract_clicks plumbing ---------------------------------------------------
# Import the singleton titleManager so we can query stored window metadata.
# If you prefer the WindowManager wrapper, change here accordingly.
# ---------------------------------------------------------------------------
try:
    from abstract_clicks.managers.windowManager.get_existing_browser_info import (
        titleManager,
    )
except ImportError:
    # Fallback: allow the GUI to run (with empty list) if libs are missing
    class _DummyMgr:  # type: ignore
        def get_all_titles(self) -> Dict[str, Dict[str, Any]]:
            return {}

        def delete_title(self, title: str) -> bool:  # noop
            return False

    titleManager = _DummyMgr  # type: ignore


# ---------------------------------------------------------------------------
# Helper functions -----------------------------------------------------------
# ---------------------------------------------------------------------------

def _classify_type(title: str) -> str:
    """Crude heuristic to label window *type* for filtering."""
    t = title.lower()
    if any(b in t for b in ("chrome", "firefox", "edge", "safari")):
        return "Browser"
    if any(e in t for e in ("code", "sublime", "pycharm", "notepad", "vim")):
        return "Editor"
    if any(tn in t for tn in ("terminal", "xterm", "cmd", "powershell")):
        return "Terminal"
    return "Other"


def _possibly_unsaved(title: str) -> bool:
    """Return *True* if the title hints that the doc may be unsaved."""
    # Many editors add a leading “*” or trailing “●”/"•" or prepend “Untitled”.
    return any(s in title for s in ("*", "●", "•", "untitled"))


def _close_window(win: Dict[str, Any]) -> None:
    """Attempt to close a window given its info dict."""

    wid = win.get("window_id")
    pid = win.get("pid")
    if not wid and not pid:
        return  # nothing we can do

    system = platform.system()

    try:
        if system == "Linux" and wid:
            subprocess.run(["xdotool", "windowclose", str(wid)])
        elif system == "Windows" and wid:
            import ctypes
            import win32con  # type: ignore
            hwnd = int(wid)
            ctypes.windll.user32.PostMessageW(hwnd, win32con.WM_CLOSE, 0, 0)
        elif system == "Darwin" and pid:
            script = f'osascript -e "tell application id {pid} to quit"'
            subprocess.run(script, shell=True)
    except Exception as exc:  # pragma: no cover – best‑effort only
        print(f"Error closing window {win}: {exc}")


# ---------------------------------------------------------------------------
# Main GUI class -------------------------------------------------------------
# ---------------------------------------------------------------------------

class WindowManagerGUI(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.wm = titleManager()  # singleton
        self.setWindowTitle("Window Manager")
        self.resize(620, 480)

        self._build_ui()
        self._refresh_list()

    # ---------------- UI setup ----------------
    def _build_ui(self) -> None:
        """Assemble widgets and layout."""
        layout = QVBoxLayout(self)

        # --- search/filter row ---
        top_row = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search window titles…")
        self.search_edit.textChanged.connect(lambda _: self._apply_filter())
        top_row.addWidget(QLabel("Search:"))
        top_row.addWidget(self.search_edit)

        self.type_filter = QComboBox()
        self.type_filter.addItems(["All", "Browser", "Editor", "Terminal", "Other"])
        self.type_filter.currentIndexChanged.connect(lambda _: self._apply_filter())
        top_row.addWidget(QLabel("Type:"))
        top_row.addWidget(self.type_filter)

        sel_all_btn = QPushButton("Select‑All (type)")
        sel_all_btn.clicked.connect(self._select_all_type)
        top_row.addWidget(sel_all_btn)

        layout.addLayout(top_row)

        # --- list widget ---
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget, stretch=1)

        # --- action buttons ---
        action_row = QHBoxLayout()
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_list)
        action_row.addWidget(refresh_btn)

        close_btn = QPushButton("Close Selected")
        close_btn.clicked.connect(self._close_selected)
        action_row.addWidget(close_btn)

        layout.addLayout(action_row)

    # ---------------- data handling ----------------
    def _refresh_list(self) -> None:
        """(Re)load window data from titleManager and repopulate list."""
        self._all_windows: List[Dict[str, Any]] = list(
            self.wm.get_all_titles().values()  # type: ignore[attr-defined]
        )
        self._apply_filter()

    def _apply_filter(self) -> None:
        """Filter _all_windows by search text and type combo, then populate."""
        text = self.search_edit.text().lower()
        type_req = self.type_filter.currentText()

        filtered: List[Dict[str, Any]] = []
        for win in self._all_windows:
            title = win.get("title") or win.get("browser_title") or ""
            if text and text not in title.lower():
                continue
            if type_req != "All" and _classify_type(title) != type_req:
                continue
            filtered.append(win)

        self._populate_list(filtered)

    def _populate_list(self, wins: List[Dict[str, Any]]) -> None:
        self.list_widget.clear()
        for win in wins:
            title = win.get("title") or win.get("browser_title") or "Untitled"
            label = f"{title}  (PID: {win.get('pid', '–')})"
            item = QListWidgetItem(label)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            item.setData(Qt.UserRole, win)  # attach dict directly – FIXED
            self.list_widget.addItem(item)

    # ---------------- interactions ----------------
    def _select_all_type(self) -> None:
        req_type = self.type_filter.currentText()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            win: Dict[str, Any] = item.data(Qt.UserRole)
            if req_type == "All" or _classify_type(win.get("title", "")) == req_type:
                item.setCheckState(Qt.Checked)

    def _gather_checked(self) -> List[Dict[str, Any]]:
        checked: List[Dict[str, Any]] = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.Checked:
                win: Dict[str, Any] = item.data(Qt.UserRole)
                checked.append(win)
        return checked

    def _close_selected(self) -> None:
        wins = self._gather_checked()
        if not wins:
            QMessageBox.information(self, "Nothing selected", "No windows are checked.")
            return

        maybe_unsaved = [w for w in wins if _possibly_unsaved(w.get("title", ""))]
        if maybe_unsaved:
            titles = "\n".join(w.get("title", "") for w in maybe_unsaved)
            resp = QMessageBox.question(
                self,
                "Unsaved Changes?",
                "The following look unsaved:\n\n" + titles + "\n\nClose anyway?",
            )
            if resp != QMessageBox.Yes:
                return  # abort

        for win in wins:
            _close_window(win)
        self._refresh_list()
 

# ---------------------------------------------------------------------------
# Entrypoint -----------------------------------------------------------------
# ---------------------------------------------------------------------------

def main() -> None:
    app = QApplication(sys.argv)
    gui = WindowManagerGUI()
    gui.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
