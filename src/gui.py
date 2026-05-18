import sys
import os
import time
import requests
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QComboBox,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QStackedWidget,
    QGroupBox,
    QMessageBox,
    QSplitter,
    QFileDialog,
)
from PyQt6.QtCore import QTimer, Qt, QThread, pyqtSignal


SERVER_URL = "http://localhost:5000"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Strulovitz Ghost 👻")
        self.setMinimumSize(900, 650)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("Server:"))
        self.server_input = QLineEdit(SERVER_URL)
        self.server_input.setMaximumWidth(300)
        top_bar.addWidget(self.server_input)
        top_bar.addStretch()
        top_bar.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Client", "Boss", "Worker"])
        self.mode_combo.currentTextChanged.connect(self.switch_mode)
        top_bar.addWidget(self.mode_combo)
        layout.addLayout(top_bar)

        self.stack = QStackedWidget()
        self.client_widget = ClientWidget()
        self.boss_widget = BossWidget()
        self.worker_widget = WorkerWidget()
        self.stack.addWidget(self.client_widget)
        self.stack.addWidget(self.boss_widget)
        self.stack.addWidget(self.worker_widget)
        layout.addWidget(self.stack)

    def switch_mode(self, mode):
        if mode == "Client":
            self.stack.setCurrentWidget(self.client_widget)
        elif mode == "Boss":
            self.stack.setCurrentWidget(self.boss_widget)
            self.boss_widget.refresh()
        elif mode == "Worker":
            self.stack.setCurrentWidget(self.worker_widget)

    def get_server(self):
        return self.server_input.text().rstrip("/")


class ClientWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Scene Description:"))
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Paste the DM's scene description here...")
        layout.addWidget(self.desc_input)

        style_row = QHBoxLayout()
        style_row.addWidget(QLabel("Style (optional):"))
        self.style_input = QLineEdit()
        self.style_input.setPlaceholderText("e.g. Ghibli animation, oil painting, pixel art...")
        style_row.addWidget(self.style_input)
        layout.addLayout(style_row)

        btn_row = QHBoxLayout()
        self.submit_btn = QPushButton("Submit Question")
        self.submit_btn.clicked.connect(self.submit_question)
        btn_row.addWidget(self.submit_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        layout.addWidget(QLabel("Your Questions:"))
        self.question_list = QListWidget()
        self.question_list.itemDoubleClicked.connect(self.open_question)
        layout.addWidget(self.question_list)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh)
        layout.addWidget(self.refresh_btn)

    def get_server(self):
        return self.window().get_server()

    def submit_question(self):
        desc = self.desc_input.toPlainText().strip()
        if not desc:
            self.status_label.setText("Please enter a description.")
            return
        style = self.style_input.text().strip() or None
        try:
            r = requests.post(
                f"{self.get_server()}/api/question",
                json={"description": desc, "style": style},
                timeout=10,
            )
            if r.ok:
                data = r.json()
                self.status_label.setText(f"Submitted! ID: {data['id']} ✅")
                self.desc_input.clear()
                self.style_input.clear()
                self.refresh()
            else:
                self.status_label.setText(f"Error: {r.json().get('error', r.text)}")
        except Exception as e:
            self.status_label.setText(f"Connection error: {e}")

    def refresh(self):
        self.question_list.clear()
        try:
            r = requests.get(f"{self.get_server()}/api/questions", timeout=10)
            if r.ok:
                for q in r.json():
                    style_str = f" [🎨 {q['style']}]" if q.get("style") else ""
                    text = f"#{q['id']} [{q['status']}]{style_str}: {q['description'][:80]}..."
                    item = QListWidgetItem(text)
                    item.setData(Qt.ItemDataRole.UserRole, q)
                    self.question_list.addItem(item)
        except Exception:
            pass

    def open_question(self, item):
        q = item.data(Qt.ItemDataRole.UserRole)
        if not q:
            return
        detail = QMessageBox(self)
        detail.setWindowTitle(f"Question #{q['id']}")
        msg = f"Status: {q['status']}\nStyle: {q.get('style', 'none')}\n\n{q['description']}"
        if q.get("tasks"):
            for t in q["tasks"]:
                msg += f"\n\nLayer {t['layer_number']}: {t['status']}"
                if t.get("result_filename"):
                    msg += f" — {t['result_filename']}"
        detail.setText(msg)
        detail.exec()


class BossWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)

        left = QVBoxLayout()
        left.addWidget(QLabel("Pending Questions:"))
        self.question_list = QListWidget()
        self.question_list.currentItemChanged.connect(self.on_question_select)
        left.addWidget(self.question_list)

        refresh_row = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh)
        refresh_row.addWidget(self.refresh_btn)

        self.llm_label = QLabel("LLM: checking...")
        refresh_row.addWidget(self.llm_label)
        refresh_row.addStretch()
        left.addLayout(refresh_row)
        layout.addLayout(left)

        right = QVBoxLayout()

        self.detail_group = QGroupBox("Question Detail")
        detail_layout = QVBoxLayout()
        self.detail_text = QLabel("Select a question...")
        self.detail_text.setWordWrap(True)
        detail_layout.addWidget(self.detail_text)
        self.detail_group.setLayout(detail_layout)
        right.addWidget(self.detail_group)

        split_group = QGroupBox("Split into Layers")
        split_layout = QVBoxLayout()
        llm_row = QHBoxLayout()
        llm_row.addWidget(QLabel("LLM:"))
        self.llm_combo = QComboBox()
        self.llm_combo.addItems(["ollama", "lmstudio"])
        llm_row.addWidget(self.llm_combo)
        llm_row.addWidget(QLabel("Model:"))
        self.llm_model = QLineEdit("qwen3")
        llm_row.addWidget(self.llm_model)
        split_layout.addLayout(llm_row)

        self.split_btn = QPushButton("Auto-Split with LLM")
        self.split_btn.clicked.connect(self.auto_split)
        split_layout.addWidget(self.split_btn)

        self.split_status = QLabel("")
        split_layout.addWidget(self.split_status)
        split_group.setLayout(split_layout)
        right.addWidget(split_group)

        tasks_group = QGroupBox("Layer Tasks")
        tasks_layout = QVBoxLayout()
        self.tasks_list = QListWidget()
        tasks_layout.addWidget(self.tasks_list)
        tasks_group.setLayout(tasks_layout)
        right.addWidget(tasks_group)

        layout.addLayout(right)

        self.current_question = None

    def get_server(self):
        return self.window().get_server()

    def refresh(self):
        self.question_list.clear()
        try:
            r = requests.get(f"{self.get_server()}/api/questions", timeout=10)
            if r.ok:
                for q in r.json():
                    style_str = f" [🎨 {q['style']}]" if q.get("style") else ""
                    text = f"#{q['id']} [{q['status']}]{style_str}"
                    item = QListWidgetItem(text)
                    item.setData(Qt.ItemDataRole.UserRole, q)
                    self.question_list.addItem(item)
        except Exception:
            pass
        self.check_llm()

    def check_llm(self):
        try:
            r = requests.get(
                f"{self.get_server()}/api/health/llm?provider=ollama", timeout=5
            )
            if r.ok and r.json().get("available"):
                self.llm_label.setText("LLM: ✅ ready")
                self.llm_label.setStyleSheet("color: #4caf50")
            else:
                self.llm_label.setText("LLM: ❌ not available")
                self.llm_label.setStyleSheet("color: #e94560")
        except Exception:
            self.llm_label.setText("LLM: ❌ server error")
            self.llm_label.setStyleSheet("color: #e94560")

    def on_question_select(self):
        item = self.question_list.currentItem()
        if not item:
            return
        q = item.data(Qt.ItemDataRole.UserRole)
        self.current_question = q
        self.detail_text.setText(
            f"#{q['id']} [{q['status']}]\nStyle: {q.get('style', 'none')}\n\n{q['description']}"
        )
        self.load_tasks(q)

    def load_tasks(self, q):
        self.tasks_list.clear()
        if q.get("tasks"):
            for t in q["tasks"]:
                text = f"Layer {t['layer_number']}: [{t['status']}] {t['prompt'][:60]}..."
                self.tasks_list.addItem(text)

    def auto_split(self):
        if not self.current_question:
            self.split_status.setText("Select a question first.")
            return
        qid = self.current_question["id"]
        provider = self.llm_combo.currentText()
        model = self.llm_model.text()
        self.split_status.setText("Splitting with LLM...")
        self.split_btn.setEnabled(False)
        try:
            r = requests.post(
                f"{self.get_server()}/api/question/{qid}/split",
                json={"provider": provider, "model": model},
                timeout=180,
            )
            if r.ok:
                data = r.json()
                self.split_status.setText(f"Split complete! {len(data.get('tasks', []))} layers created ✅")
                self.refresh()
            else:
                err = r.json().get("error", r.text)
                self.split_status.setText(f"Error: {err}")
        except Exception as e:
            self.split_status.setText(f"Error: {e}")
        self.split_btn.setEnabled(True)


class GenerateThread(QThread):
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, prompt, method, output_dir):
        super().__init__()
        self.prompt = prompt
        self.method = method
        self.output_dir = output_dir

    def run(self):
        try:
            from generator import generate_image

            os.makedirs(self.output_dir, exist_ok=True)
            filename = f"generated_layer_{int(time.time())}.png"
            output_path = os.path.join(self.output_dir, filename)

            self.progress_signal.emit(10)
            result = generate_image(
                self.prompt, output_path, method=self.method,
                width=768, height=576, num_steps=20,
            )
            if result:
                self.progress_signal.emit(100)
                self.finished_signal.emit(result)
            else:
                self.error_signal.emit("Generation failed")
        except Exception as e:
            self.error_signal.emit(str(e))


class WorkerWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        config_row = QHBoxLayout()
        config_row.addWidget(QLabel("Worker ID:"))
        self.worker_id = QLineEdit("worker-1")
        config_row.addWidget(self.worker_id)

        config_row.addWidget(QLabel("Method:"))
        self.method_combo = QComboBox()
        self.method_combo.addItems(["diffusers", "comfyui"])
        config_row.addWidget(self.method_combo)

        config_row.addStretch()
        self.poll_toggle = QPushButton("Start Polling")
        self.poll_toggle.setCheckable(True)
        self.poll_toggle.clicked.connect(self.toggle_polling)
        config_row.addWidget(self.poll_toggle)
        layout.addLayout(config_row)

        self.status_label = QLabel("Not polling")
        layout.addWidget(self.status_label)

        tasks_group = QGroupBox("Available Tasks")
        tasks_layout = QVBoxLayout()
        self.tasks_list = QListWidget()
        self.tasks_list.itemDoubleClicked.connect(self.claim_task)
        tasks_layout.addWidget(self.tasks_list)
        tasks_group.setLayout(tasks_layout)
        layout.addWidget(tasks_group)

        active_group = QGroupBox("Active Task")
        active_layout = QVBoxLayout()
        self.active_task_label = QLabel("No active task")
        active_layout.addWidget(self.active_task_label)
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        active_layout.addWidget(self.progress)

        gen_row = QHBoxLayout()
        self.generate_btn = QPushButton("Generate with Qwen AI")
        self.generate_btn.clicked.connect(self.generate_image)
        self.generate_btn.setEnabled(False)
        gen_row.addWidget(self.generate_btn)

        self.upload_btn = QPushButton("Upload Result PNG")
        self.upload_btn.clicked.connect(self.upload_result)
        self.upload_btn.setEnabled(False)
        gen_row.addWidget(self.upload_btn)
        gen_row.addStretch()
        active_layout.addLayout(gen_row)
        active_group.setLayout(active_layout)
        layout.addWidget(active_group)

        self.poll_timer = QTimer()
        self.poll_timer.timeout.connect(self.poll_tasks)
        self.active_task = None
        self.generated_path = None
        self.gen_thread = None

    def get_server(self):
        return self.window().get_server()

    def toggle_polling(self):
        if self.poll_toggle.isChecked():
            self.poll_timer.start(5000)
            self.poll_toggle.setText("Stop Polling")
            self.status_label.setText("Polling for tasks...")
            self.poll_tasks()
        else:
            self.poll_timer.stop()
            self.poll_toggle.setText("Start Polling")
            self.status_label.setText("Not polling")

    def poll_tasks(self):
        try:
            r = requests.get(
                f"{self.get_server()}/api/tasks?status=pending", timeout=10
            )
            if r.ok:
                tasks = r.json()
                self.tasks_list.clear()
                for t in tasks:
                    text = f"Task #{t['id']} — Layer {t['layer_number']}: {t['prompt'][:80]}..."
                    item = QListWidgetItem(text)
                    item.setData(Qt.ItemDataRole.UserRole, t)
                    self.tasks_list.addItem(item)
                self.status_label.setText(f"Polling... ({len(tasks)} tasks available)")
        except Exception as e:
            self.status_label.setText(f"Poll error: {e}")

    def claim_task(self, item):
        t = item.data(Qt.ItemDataRole.UserRole)
        if not t:
            return
        try:
            r = requests.post(
                f"{self.get_server()}/api/task/{t['id']}/claim",
                json={"worker_id": self.worker_id.text()},
                timeout=10,
            )
            if r.ok:
                self.active_task = r.json()
                self.active_task_label.setText(
                    f"Task #{self.active_task['id']} — Layer {self.active_task['layer_number']}\n"
                    f"Prompt: {self.active_task['prompt']}"
                )
                self.generate_btn.setEnabled(True)
                self.progress.setVisible(True)
                self.progress.setValue(0)
                self.status_label.setText("Task claimed! Click Generate with Qwen AI.")
                self.tasks_list.clear()
            else:
                err = r.json().get("error", r.text)
                self.status_label.setText(f"Claim error: {err}")
        except Exception as e:
            self.status_label.setText(f"Claim error: {e}")

    def generate_image(self):
        if not self.active_task:
            return
        method = self.method_combo.currentText()
        self.generate_btn.setEnabled(False)
        self.status_label.setText(f"Generating with Qwen ({method})... this may take a few minutes")
        self.progress.setValue(0)

        output_dir = os.path.join(os.path.dirname(__file__), "output")
        self.gen_thread = GenerateThread(
            self.active_task["prompt"], method, output_dir
        )
        self.gen_thread.progress_signal.connect(self.on_gen_progress)
        self.gen_thread.finished_signal.connect(self.on_gen_finished)
        self.gen_thread.error_signal.connect(self.on_gen_error)
        self.gen_thread.start()

    def on_gen_progress(self, val):
        self.progress.setValue(val)

    def on_gen_finished(self, path):
        self.generated_path = path
        self.progress.setValue(100)
        self.upload_btn.setEnabled(True)
        self.generate_btn.setEnabled(True)
        self.status_label.setText(f"Generated! ✅ Click Upload Result PNG.")

    def on_gen_error(self, err):
        self.status_label.setText(f"Generation error: {err}")
        self.generate_btn.setEnabled(True)
        self.progress.setVisible(False)

    def upload_result(self):
        filepath = self.generated_path
        if not filepath or not self.active_task:
            filepath, _ = QFileDialog.getOpenFileName(
                self, "Select PNG Result", "", "PNG Images (*.png)"
            )
        if not filepath:
            return
        try:
            with open(filepath, "rb") as f:
                r = requests.post(
                    f"{self.get_server()}/api/task/{self.active_task['id']}/result",
                    files={"image": f},
                    timeout=30,
                )
            if r.ok:
                self.status_label.setText("Uploaded! ✅")
                self.active_task = None
                self.generated_path = None
                self.active_task_label.setText("No active task")
                self.upload_btn.setEnabled(False)
                self.generate_btn.setEnabled(False)
                self.progress.setVisible(False)
            else:
                err = r.json().get("error", r.text)
                self.status_label.setText(f"Upload error: {err}")
        except Exception as e:
            self.status_label.setText(f"Upload error: {e}")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    dark_style = """
    QMainWindow, QWidget {
        background-color: #1a1a2e;
        color: #eee;
    }
    QTextEdit, QLineEdit, QComboBox, QListWidget {
        background-color: #0f3460;
        color: #eee;
        border: 1px solid #333;
        border-radius: 6px;
        padding: 4px;
    }
    QPushButton {
        background-color: #e94560;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 6px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #c73652;
    }
    QPushButton:disabled {
        background-color: #555;
        color: #999;
    }
    QPushButton:checked {
        background-color: #4ecca3;
    }
    QGroupBox {
        border: 1px solid #333;
        border-radius: 8px;
        margin-top: 10px;
        padding-top: 15px;
    }
    QGroupBox::title {
        color: #e94560;
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px;
    }
    QLabel {
        color: #eee;
    }
    QListWidget::item:selected {
        background-color: #e94560;
    }
    QProgressBar {
        border: 1px solid #333;
        border-radius: 4px;
        text-align: center;
    }
    QProgressBar::chunk {
        background-color: #4ecca3;
        border-radius: 3px;
    }
    """

    app.setStyleSheet(dark_style)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
