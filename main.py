import json
import os
import subprocess
import sys
import traceback
from pathlib import Path

if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

if sys.platform == "win32" and getattr(sys, "frozen", False):
    _orig_popen_init = subprocess.Popen.__init__

    def _hidden_popen_init(self, *args, **kwargs):
        kwargs.setdefault("creationflags", 0)
        kwargs["creationflags"] |= subprocess.CREATE_NO_WINDOW
        _orig_popen_init(self, *args, **kwargs)

    subprocess.Popen.__init__ = _hidden_popen_init

import runpod
from PySide6.QtCore import QObject, Qt, Signal, Slot, QThread
from PySide6.QtGui import QClipboard
from PySide6.QtWidgets import (
    QApplication,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

CONFIG_PATH = Path(__file__).parent / "config.json"


def load_config() -> dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {}


def save_config(data: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Worker that runs RunPod API calls off the main thread
# ---------------------------------------------------------------------------

class ApiWorker(QObject):
    finished = Signal(str, object)  # (action_name, result_or_exception)

    def __init__(self, action: str, func, *args):
        super().__init__()
        self._action = action
        self._func = func
        self._args = args

    @Slot()
    def run(self):
        try:
            result = self._func(*self._args)
            self.finished.emit(self._action, result)
        except Exception as exc:
            exc._tb_str = traceback.format_exc()
            self.finished.emit(self._action, exc)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RunPod Pod Manager")
        self.setMinimumSize(680, 520)

        self._threads: list[QThread] = []
        self._selected_pod_id: str | None = None
        self._pods: list[dict] = []

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setSpacing(12)
        root.setContentsMargins(16, 16, 16, 16)

        # --- API Key Section ---
        key_group = QGroupBox("RunPod API Key")
        key_layout = QHBoxLayout(key_group)
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("Paste your RunPod API key here...")
        key_layout.addWidget(self.api_key_input, stretch=1)
        self.connect_btn = QPushButton("Save && Connect")
        self.connect_btn.clicked.connect(self._on_save_connect)
        key_layout.addWidget(self.connect_btn)
        root.addWidget(key_group)

        # --- Pod List Section ---
        pods_group = QGroupBox("Pods")
        pods_layout = QVBoxLayout(pods_group)

        self.pod_table = QTableWidget(0, 4)
        self.pod_table.setHorizontalHeaderLabels(["Name", "ID", "Status", "GPU"])
        self.pod_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.pod_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.pod_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        header = self.pod_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.pod_table.itemSelectionChanged.connect(self._on_table_selection)
        pods_layout.addWidget(self.pod_table)

        manual_row = QHBoxLayout()
        manual_row.addWidget(QLabel("Manual Pod ID:"))
        self.manual_pod_input = QLineEdit()
        self.manual_pod_input.setPlaceholderText("Enter a pod ID to override table selection")
        self.manual_pod_input.textChanged.connect(self._on_manual_id_changed)
        manual_row.addWidget(self.manual_pod_input, stretch=1)
        pods_layout.addLayout(manual_row)

        root.addWidget(pods_group, stretch=1)

        # --- Action Buttons ---
        btn_row = QHBoxLayout()
        self.start_btn = QPushButton("Start Pod")
        self.start_btn.clicked.connect(self._on_start_pod)
        btn_row.addWidget(self.start_btn)
        self.stop_btn = QPushButton("Stop Pod")
        self.stop_btn.clicked.connect(self._on_stop_pod)
        btn_row.addWidget(self.stop_btn)
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self._on_refresh)
        btn_row.addWidget(self.refresh_btn)
        root.addLayout(btn_row)

        # --- SSH Info Section ---
        ssh_group = QGroupBox("SSH Connection Info")
        ssh_layout = QVBoxLayout(ssh_group)

        ip_row = QHBoxLayout()
        ip_row.addWidget(QLabel("IP:"))
        self.ssh_ip_label = QLabel("—")
        self.ssh_ip_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        ip_row.addWidget(self.ssh_ip_label, stretch=1)
        ssh_layout.addLayout(ip_row)

        port_row = QHBoxLayout()
        port_row.addWidget(QLabel("Port:"))
        self.ssh_port_label = QLabel("—")
        self.ssh_port_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        port_row.addWidget(self.ssh_port_label, stretch=1)
        ssh_layout.addLayout(port_row)

        cmd_row = QHBoxLayout()
        cmd_row.addWidget(QLabel("Command:"))
        self.ssh_cmd_label = QLabel("—")
        self.ssh_cmd_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        cmd_row.addWidget(self.ssh_cmd_label, stretch=1)
        self.copy_btn = QPushButton("Copy Command")
        self.copy_btn.clicked.connect(self._on_copy_ssh_cmd)
        cmd_row.addWidget(self.copy_btn)
        ssh_layout.addLayout(cmd_row)

        root.addWidget(ssh_group)

        # --- Status Bar ---
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self._set_controls_enabled(False)
        self._load_saved_key()

    # --- Config helpers ---

    def _load_saved_key(self):
        cfg = load_config()
        key = cfg.get("api_key", "")
        if key:
            self.api_key_input.setText(key)
            self.status_bar.showMessage("API key loaded – connecting...")
            runpod.api_key = key
            self._run_in_thread("get_pods", runpod.get_pods)

    def _get_api_key(self) -> str:
        return self.api_key_input.text().strip()

    # --- Background task launcher ---

    def _run_in_thread(self, action: str, func, *args):
        thread = QThread()
        worker = ApiWorker(action, func, *args)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(lambda a, r: self._on_worker_done(a, r, thread, worker))
        self._threads.append(thread)
        thread.start()

    def _on_worker_done(self, action: str, result, thread: QThread, worker: ApiWorker):
        thread.quit()
        thread.wait()
        if thread in self._threads:
            self._threads.remove(thread)
        worker.deleteLater()
        thread.deleteLater()

        if isinstance(result, Exception):
            tb = getattr(result, "_tb_str", str(result))
            self.status_bar.showMessage(f"Error ({action}): {result}")
            QMessageBox.warning(self, f"API Error – {action}", f"{result}\n\n{tb}")
            self._set_controls_enabled(True)
            return

        if action == "get_pods":
            self._handle_pods_result(result)
        elif action == "get_pod":
            self._handle_pod_detail(result)
        elif action in ("resume_pod", "stop_pod"):
            verb = "started" if action == "resume_pod" else "stopped"
            self.status_bar.showMessage(f"Pod {verb} successfully")
            self._on_refresh()
            return

        self._set_controls_enabled(True)

    # --- Slot handlers ---

    def _on_save_connect(self):
        key = self._get_api_key()
        if not key:
            QMessageBox.warning(self, "Missing Key", "Please enter a RunPod API key.")
            return
        save_config({"api_key": key})
        runpod.api_key = key
        self.status_bar.showMessage("Connecting...")
        self._set_controls_enabled(False)
        self._run_in_thread("get_pods", runpod.get_pods)

    def _on_refresh(self):
        key = self._get_api_key()
        if not key:
            return
        runpod.api_key = key
        self.status_bar.showMessage("Refreshing pods...")
        self._set_controls_enabled(False)
        self._run_in_thread("get_pods", runpod.get_pods)

    def _on_start_pod(self):
        pod_id = self._resolve_pod_id()
        if not pod_id:
            return
        self.status_bar.showMessage(f"Starting pod {pod_id}...")
        self._set_controls_enabled(False)
        self._run_in_thread("resume_pod", runpod.resume_pod, pod_id)

    def _on_stop_pod(self):
        pod_id = self._resolve_pod_id()
        if not pod_id:
            return
        self.status_bar.showMessage(f"Stopping pod {pod_id}...")
        self._set_controls_enabled(False)
        self._run_in_thread("stop_pod", runpod.stop_pod, pod_id)

    def _on_table_selection(self):
        if self.manual_pod_input.text().strip():
            return
        rows = self.pod_table.selectionModel().selectedRows()
        if rows:
            row = rows[0].row()
            self._selected_pod_id = self.pod_table.item(row, 1).text()
            self._update_ssh_for_pod(self._selected_pod_id)

    def _on_manual_id_changed(self, text: str):
        text = text.strip()
        if text:
            self._selected_pod_id = text
            self._update_ssh_for_pod(text)

    def _on_copy_ssh_cmd(self):
        cmd = self.ssh_cmd_label.text()
        if cmd and cmd != "—":
            QApplication.clipboard().setText(cmd)
            self.status_bar.showMessage("SSH command copied to clipboard", 3000)

    # --- Data handlers ---

    def _handle_pods_result(self, pods):
        self._pods = pods if isinstance(pods, list) else []
        self.pod_table.setRowCount(0)
        for pod in self._pods:
            row = self.pod_table.rowCount()
            self.pod_table.insertRow(row)
            self.pod_table.setItem(row, 0, QTableWidgetItem(pod.get("name", "")))
            self.pod_table.setItem(row, 1, QTableWidgetItem(pod.get("id", "")))

            status = pod.get("desiredStatus", "UNKNOWN")
            runtime = pod.get("runtime")
            if runtime and status == "RUNNING":
                display_status = "RUNNING"
            elif status == "RUNNING" and not runtime:
                display_status = "STARTING"
            else:
                display_status = status
            self.pod_table.setItem(row, 2, QTableWidgetItem(display_status))

            machine = pod.get("machine", {}) or {}
            gpu = machine.get("gpuDisplayName", pod.get("gpuDisplayName", ""))
            self.pod_table.setItem(row, 3, QTableWidgetItem(gpu))

        count = len(self._pods)
        self.status_bar.showMessage(f"Loaded {count} pod{'s' if count != 1 else ''}")
        self._set_controls_enabled(True)

    def _handle_pod_detail(self, pod):
        if not pod:
            return
        self._display_ssh_info(pod)
        self._set_controls_enabled(True)

    def _update_ssh_for_pod(self, pod_id: str):
        for pod in self._pods:
            if pod.get("id") == pod_id:
                self._display_ssh_info(pod)
                return
        key = self._get_api_key()
        if key:
            runpod.api_key = key
            self._run_in_thread("get_pod", runpod.get_pod, pod_id)

    def _display_ssh_info(self, pod: dict):
        runtime = pod.get("runtime") or {}
        ports = runtime.get("ports") or []

        ssh_ip = None
        ssh_port = None
        for p in ports:
            if p.get("privatePort") == 22 and p.get("isIpPublic"):
                ssh_ip = p.get("ip")
                ssh_port = p.get("publicPort")
                break

        if ssh_ip and ssh_port:
            self.ssh_ip_label.setText(str(ssh_ip))
            self.ssh_port_label.setText(str(ssh_port))
            self.ssh_cmd_label.setText(f"ssh root@{ssh_ip} -p {ssh_port} -i ~/.ssh/id_ed25519")
        else:
            status = pod.get("desiredStatus", "UNKNOWN")
            note = "(pod not running)" if status != "RUNNING" else "(no public SSH port found)"
            self.ssh_ip_label.setText(f"— {note}")
            self.ssh_port_label.setText("—")
            self.ssh_cmd_label.setText("—")

    # --- UI helpers ---

    def _resolve_pod_id(self) -> str | None:
        manual = self.manual_pod_input.text().strip()
        pod_id = manual or self._selected_pod_id
        if not pod_id:
            QMessageBox.information(self, "No Pod Selected", "Select a pod from the table or enter a Pod ID.")
            return None
        return pod_id

    def _set_controls_enabled(self, enabled: bool):
        self.start_btn.setEnabled(enabled)
        self.stop_btn.setEnabled(enabled)
        self.refresh_btn.setEnabled(enabled)
        self.pod_table.setEnabled(enabled)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
