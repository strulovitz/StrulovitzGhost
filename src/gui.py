import sys
import os
import traceback
import json as json_mod
from logger import setup_logging
setup_logging()

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
    QGraphicsView,
    QGraphicsScene,
)
from PyQt6.QtCore import QTimer, Qt, QThread, pyqtSignal, QRectF
from PyQt6.QtGui import QPixmap, QImage, QPainter


SERVER_URL = "http://localhost:5000"


class LayerWindow_(QWidget):
    def __init__(self, image_path, layer_index, saved_state=None):
        super().__init__()
        self.image_path = image_path
        self.layer_index = layer_index
        try:
            self.setWindowTitle(f"Layer {layer_index + 1}")
            self.setWindowFlags(
                Qt.WindowType.Window |
                Qt.WindowType.WindowCloseButtonHint |
                Qt.WindowType.WindowMinimizeButtonHint |
                Qt.WindowType.WindowMaximizeButtonHint
            )
            self.setMinimumSize(150, 100)

            self.view = QGraphicsView()
            self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self.view.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
            self.view.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)

            self.scene = QGraphicsScene()
            self.pixmap_item = self.scene.addPixmap(QPixmap())
            self.view.setScene(self.scene)

            layout = QVBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(self.view)
            self.setLayout(layout)

            self._loading = True
            img = QImage(image_path)
            if not img.isNull():
                self.pixmap_item.setPixmap(QPixmap.fromImage(img))
                r = self.pixmap_item.pixmap().rect()
                self.scene.setSceneRect(QRectF(r))
            else:
                self.setWindowTitle(f"Layer {layer_index + 1} (not found)")

            self.rotation = 0
            self.restore_state(saved_state)
            self._loading = False

            self._save_timer = QTimer()
            self._save_timer.setSingleShot(True)
            self._save_timer.setInterval(200)
            self._save_timer.timeout.connect(self.signal_save)
        except Exception:
            import logging
            logging.error(f"LayerWindow_ init failed: {traceback.format_exc()}")

    def restore_state(self, state):
        if not state:
            self.resize(500, 400)
            self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
            self.zoom_level = self.view.transform().m11()
            return
        if "x" in state and "y" in state:
            self.move(state["x"], state["y"])
        if "w" in state and "h" in state:
            self.resize(state["w"], state["h"])
        self.view.resetTransform()
        zoom = state.get("zoom", 1.0)
        if zoom <= 0:
            zoom = 1.0
        self.zoom_level = zoom
        self.view.scale(zoom, zoom)
        rotation = state.get("rotation", 0)
        self.rotation = rotation % 360
        if rotation:
            self.view.rotate(rotation)
        if "center_x" in state and "center_y" in state:
            self.view.centerOn(state["center_x"], state["center_y"])

    def get_state(self):
        center = self.view.mapToScene(self.view.viewport().rect().center())
        return {
            "x": self.x(), "y": self.y(), "w": self.width(), "h": self.height(),
            "zoom": self.zoom_level,
            "rotation": self.rotation,
            "center_x": center.x(), "center_y": center.y(),
        }

    def wheelEvent(self, event):
        factor = 1.1 if event.angleDelta().y() > 0 else 0.9
        self.view.scale(factor, factor)
        self.zoom_level = self.view.transform().m11()
        self.schedule_save()
        event.accept()

    def closeEvent(self, event):
        self.schedule_save()
        event.accept()


class ViewerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.windows = []
        self.base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "output")
        layout = QVBoxLayout(self)

        title = QLabel("🎬 Scene Viewer")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #4ecca3; padding: 5px;")
        layout.addWidget(title)

        info = QLabel("Select a scene below. Layer windows will open as separate floating windows. Move, resize, or zoom them — all settings auto-save to scene.json.")
        info.setWordWrap(True)
        info.setStyleSheet("color: #aaa; padding: 5px;")
        layout.addWidget(info)

        sel_row = QHBoxLayout()
        self.prev_btn = QPushButton("◀ Prev")
        self.prev_btn.setEnabled(False)
        self.prev_btn.clicked.connect(self.prev_scene)
        sel_row.addWidget(self.prev_btn)

        self.scene_combo = QComboBox()
        self.scene_combo.setMinimumWidth(250)
        self.scene_combo.currentTextChanged.connect(self.on_scene_change)
        sel_row.addWidget(self.scene_combo, 1)

        self.next_btn = QPushButton("Next ▶")
        self.next_btn.setEnabled(False)
        self.next_btn.clicked.connect(self.next_scene)
        sel_row.addWidget(self.next_btn)
        layout.addLayout(sel_row)

        self.launch_btn = QPushButton("🚀 Open Layer Windows")
        self.launch_btn.clicked.connect(self.open_windows)
        self.launch_btn.setMinimumHeight(35)
        layout.addWidget(self.launch_btn)

        self.close_btn = QPushButton("✕ Close All Windows")
        self.close_btn.clicked.connect(self.close_windows)
        self.close_btn.setEnabled(False)
        layout.addWidget(self.close_btn)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #4ecca3; font-weight: bold; padding: 5px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        self.preview_group = QGroupBox("Scene Contents")
        preview_layout = QVBoxLayout()
        self.preview_label = QLabel("")
        self.preview_label.setWordWrap(True)
        self.preview_label.setStyleSheet("color: #ccc; font-size: 11px;")
        preview_layout.addWidget(self.preview_label)
        self.preview_group.setLayout(preview_layout)
        layout.addWidget(self.preview_group)

        layout.addStretch()

        self.scenes = []
        self.refresh_scenes()

    def refresh_scenes(self):
        self.scenes = []
        if os.path.isdir(self.base_dir):
            for entry in sorted(os.listdir(self.base_dir)):
                path = os.path.join(self.base_dir, entry)
                if os.path.isdir(path):
                    pngs = [f for f in os.listdir(path) if f.lower().endswith('.png')]
                    if pngs:
                        self.scenes.append(entry)
        self.scene_combo.clear()
        self.scene_combo.addItems(self.scenes)
        if self.scenes:
            self.scene_combo.setCurrentIndex(0)

    def on_scene_change(self, name):
        if not name:
            self.preview_label.setText("")
            return
        was_open = bool(self.windows)
        if self.windows:
            self.close_windows()
        folder = os.path.join(self.base_dir, name)
        lines = []
        for f in sorted(os.listdir(folder)):
            if f.lower().endswith('.png'):
                size_kb = os.path.getsize(os.path.join(folder, f)) // 1024
                lines.append(f"  📄 {f} ({size_kb} KB)")
        self.preview_label.setText("\n".join(lines))
        self._update_nav()
        if was_open:
            self.open_windows()

    def _update_nav(self):
        name = self.scene_combo.currentText()
        if not self.scenes or not name:
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            return
        try:
            idx = self.scenes.index(name)
        except ValueError:
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            return
        self.prev_btn.setEnabled(idx > 0)
        self.next_btn.setEnabled(idx < len(self.scenes) - 1)

    def prev_scene(self):
        name = self.scene_combo.currentText()
        try:
            idx = self.scenes.index(name)
        except ValueError:
            return
        if idx > 0:
            self.scene_combo.setCurrentText(self.scenes[idx - 1])

    def next_scene(self):
        name = self.scene_combo.currentText()
        try:
            idx = self.scenes.index(name)
        except ValueError:
            return
        if idx < len(self.scenes) - 1:
            self.scene_combo.setCurrentText(self.scenes[idx + 1])

    def open_windows(self):
        try:
            self._open_windows_impl()
        except Exception:
            import logging
            logging.error(f"ViewerWidget open_windows failed: {traceback.format_exc()}")
            self.status_label.setText("❌ Error opening windows — check log file")
            self.close_windows()

    def _open_windows_impl(self):
        name = self.scene_combo.currentText()
        if not name:
            return
        self.close_windows()
        folder = os.path.join(self.base_dir, name)
        saved = {}
        scene_json = os.path.join(folder, "scene.json")
        if os.path.exists(scene_json):
            try:
                with open(scene_json, 'r') as f:
                    saved = json_mod.load(f)
            except (json_mod.JSONDecodeError, IOError):
                pass
        png_files = sorted(
            f for f in os.listdir(folder)
            if f.lower().endswith('.png') and 'composite' not in f.lower()
        )[:6]
        for i, fname in enumerate(png_files):
            path = os.path.join(folder, fname)
            state = saved.get(str(i), None) if saved else None
            w = LayerWindow_(path, i, state)
            w.show()
            w.raise_()
            w.activateWindow()
            self.windows.append(w)
        self.close_btn.setEnabled(True)
        self.launch_btn.setEnabled(False)
        self.status_label.setText(f"✅ {len(self.windows)} windows open — {name}")
        if not hasattr(self, '_auto_save_timer'):
            self._auto_save_timer = QTimer()
            self._auto_save_timer.setInterval(2000)
            self._auto_save_timer.timeout.connect(self.save_all)
        self._auto_save_timer.start()

    def close_windows(self):
        self.save_all()
        if hasattr(self, '_auto_save_timer'):
            self._auto_save_timer.stop()
        for w in self.windows:
            w.close()
        self.windows.clear()
        self.close_btn.setEnabled(False)
        self.launch_btn.setEnabled(True)
        self.status_label.setText("")

    def save_all(self):
        if not self.windows:
            return
        name = self.scene_combo.currentText()
        if not name:
            return
        state = {}
        for i, w in enumerate(self.windows):
            state[str(i)] = w.get_state()
        scene_json = os.path.join(self.base_dir, name, "scene.json")
        try:
            with open(scene_json, 'w') as f:
                json_mod.dump(state, f, indent=2)
        except IOError:
            pass

    def closeEvent(self, event):
        self.close_windows()
        event.accept()


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
        self.mode_combo.addItems(["Client", "Boss", "Worker", "Viewer"])
        self.mode_combo.currentTextChanged.connect(self.switch_mode)
        top_bar.addWidget(self.mode_combo)
        layout.addLayout(top_bar)

        self.stack = QStackedWidget()
        self.client_widget = ClientWidget()
        self.boss_widget = BossWidget()
        self.worker_widget = WorkerWidget()
        self.viewer_widget = ViewerWidget()
        self.stack.addWidget(self.client_widget)
        self.stack.addWidget(self.boss_widget)
        self.stack.addWidget(self.worker_widget)
        self.stack.addWidget(self.viewer_widget)
        layout.addWidget(self.stack)

    def switch_mode(self, mode):
        if mode == "Client":
            self.stack.setCurrentWidget(self.client_widget)
        elif mode == "Boss":
            self.stack.setCurrentWidget(self.boss_widget)
            self.boss_widget.refresh()
        elif mode == "Worker":
            self.stack.setCurrentWidget(self.worker_widget)
        elif mode == "Viewer":
            self.stack.setCurrentWidget(self.viewer_widget)
            self.viewer_widget.refresh_scenes()

    def get_server(self):
        return self.server_input.text().rstrip("/")


class ClientWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        info = QLabel("Paste the FULL scene description below as one paragraph. The Boss will auto-split it into 6 depth layers using AI.")
        info.setWordWrap(True)
        info.setStyleSheet("color: #888; font-size: 11px; padding-bottom: 8px;")
        layout.addWidget(info)

        layout.addWidget(QLabel("Scene Description:"))
        self.desc_input = QTextEdit()
        self.desc_input.setMinimumHeight(250)
        self.desc_input.setPlaceholderText("e.g. The group camps in a moonlit forest clearing. Stars fill the sky above snow-capped mountains. Ancient oak trees surround them. Tiefling sharpens her sword on a rock. Dragonborn studies his spellbook. Dwarf and Halfling argue over a crackling campfire. Elf and Human gossip on a fallen log, backs turned...")
        layout.addWidget(self.desc_input, stretch=1)

        style_row = QHBoxLayout()
        style_row.addWidget(QLabel("Style (optional):"))
        self.style_input = QLineEdit()
        self.style_input.setPlaceholderText("Ghibli animation (default) — change for oil painting, pixel art, etc...")
        style_row.addWidget(self.style_input)
        layout.addLayout(style_row)

        layout.addWidget(QLabel("Global Negative Prompt (optional, applies to all layers):"))
        self.client_neg_input = QTextEdit()
        self.client_neg_input.setPlaceholderText("e.g. no text, no watermarks, no nudity, no modern objects, no cars...")
        self.client_neg_input.setMaximumHeight(80)
        layout.addWidget(self.client_neg_input)

        btn_row = QHBoxLayout()
        self.submit_btn = QPushButton("Submit New Scene")
        self.submit_btn.clicked.connect(self.submit_question)
        btn_row.addWidget(self.submit_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        layout.addWidget(QLabel("Your Scenes:"))
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
        style = self.style_input.text().strip() or "Ghibli animation"
        desc = f"Style: {style}\n\n{desc}"
        global_neg = self.client_neg_input.toPlainText().strip()
        if global_neg:
            desc = f"[GLOBAL NEGATIVE PROMPT: {global_neg}]\n\n{desc}"
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
                self.client_neg_input.clear()
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

        llm_info = QLabel(
            "LLM Setup: Install Ollama (ollama.com) or LM Studio (lmstudio.ai), "
            "then pull a model: ollama pull qwen3:27b"
        )
        llm_info.setWordWrap(True)
        llm_info.setStyleSheet("color: #888; font-size: 11px;")
        left.addWidget(llm_info)

        layout.addLayout(left)

        right = QVBoxLayout()

        self.detail_group = QGroupBox("Question Detail")
        detail_layout = QVBoxLayout()
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setMinimumHeight(120)
        self.detail_text.setMaximumHeight(200)
        self.detail_text.setPlaceholderText("Select a question...")
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
        self.llm_model = QLineEdit("qwen3:14b")
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
        self.tasks_list.itemClicked.connect(self.on_task_select)
        tasks_layout.addWidget(self.tasks_list)

        self.boss_neg_label = QLabel("Edit Prompt & Negative Prompt (click a task first):")
        self.boss_neg_label.setStyleSheet("color: #e94560; font-size: 11px; margin-top: 4px;")
        tasks_layout.addWidget(self.boss_neg_label)

        self.boss_prompt_input = QTextEdit()
        self.boss_prompt_input.setMaximumHeight(80)
        self.boss_prompt_input.setPlaceholderText("Select a task to edit its prompt...")
        tasks_layout.addWidget(self.boss_prompt_input)

        self.boss_neg_input = QTextEdit()
        self.boss_neg_input.setMaximumHeight(80)
        self.boss_neg_input.setPlaceholderText("Select a task to edit its negative prompt...")
        tasks_layout.addWidget(self.boss_neg_input)

        boss_btn_row = QHBoxLayout()
        self.boss_update_btn = QPushButton("Update Task")
        self.boss_update_btn.clicked.connect(self.update_task)
        self.boss_update_btn.setEnabled(False)
        boss_btn_row.addWidget(self.boss_update_btn)
        boss_btn_row.addStretch()
        tasks_layout.addLayout(boss_btn_row)

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
        self.detail_text.setPlainText(
            f"#{q['id']} [{q['status']}]\nStyle: {q.get('style', 'none')}\n\n{q['description']}"
        )
        self.load_tasks(q)

    def load_tasks(self, q):
        self.tasks_list.clear()
        self.boss_prompt_input.clear()
        self.boss_neg_input.clear()
        self.boss_update_btn.setEnabled(False)
        if q.get("tasks"):
            for t in q["tasks"]:
                neg = t.get("negative_prompt", "")
                neg_str = f" | ❌ {neg[:40]}..." if neg else ""
                text = f"Layer {t['layer_number']}: [{t['status']}] {t['prompt'][:60]}...{neg_str}"
                item = QListWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, t)
                self.tasks_list.addItem(item)

    def on_task_select(self, item):
        t = item.data(Qt.ItemDataRole.UserRole)
        if not t:
            return
        self.boss_prompt_input.setPlainText(t.get("prompt") or "")
        self.boss_neg_input.setPlainText(t.get("negative_prompt") or "")
        self.boss_update_btn.setEnabled(True)

    def update_task(self):
        item = self.tasks_list.currentItem()
        if not item:
            return
        t = item.data(Qt.ItemDataRole.UserRole)
        if not t:
            return
        tid = t["id"]
        new_prompt = self.boss_prompt_input.toPlainText().strip() or ""
        new_neg = self.boss_neg_input.toPlainText().strip() or ""
        try:
            r = requests.put(
                f"{self.get_server()}/api/task/{tid}",
                json={"prompt": new_prompt, "negative_prompt": new_neg},
                timeout=10,
            )
            if r.ok:
                self.split_status.setText(f"Layer {t['layer_number']} updated ✅")
                self.refresh()
            else:
                self.split_status.setText(f"Update error: {r.json().get('error', r.text)}")
        except Exception as e:
            self.split_status.setText(f"Update error: {e}")

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
    progress_msg_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, prompt, method, output_dir, num_steps=15, key_color="green", negative_prompt=None):
        super().__init__()
        self.prompt = prompt
        self.method = method
        self.output_dir = output_dir
        self.num_steps = num_steps
        self.key_color = key_color
        self.negative_prompt = negative_prompt

    def run(self):
        try:
            from generator import generate_image
            from chroma_key import chroma_key

            os.makedirs(self.output_dir, exist_ok=True)
            base_name = f"generated_layer_{int(time.time())}"
            green_path = os.path.join(self.output_dir, f"{base_name}_green.png")
            final_path = os.path.join(self.output_dir, f"{base_name}.png")

            def progress_cb(msg, pct):
                self.progress_signal.emit(pct)
                self.progress_msg_signal.emit(msg)

            # Step 1: generate on green screen (no rembg)
            self.progress_msg_signal.emit("Generating image...")
            result = generate_image(
                self.prompt, green_path, method=self.method,
                width=768, height=576, num_steps=self.num_steps,
                remove_bg=False, negative_prompt=self.negative_prompt,
                progress_callback=progress_cb,
            )
            if not result:
                self.error_signal.emit("Generation failed")
                return

            # Step 2: chroma-key green to transparent
            self.progress_msg_signal.emit("Removing background...")
            self.progress_signal.emit(92)
            chroma_key(green_path, final_path, self.key_color)

            # Clean up green intermediate
            try:
                os.remove(green_path)
            except OSError:
                pass

            self.progress_signal.emit(100)
            self.progress_msg_signal.emit("Done!")
            self.finished_signal.emit(final_path)
        except Exception as e:
            self.error_signal.emit(str(e))


class DownloadThread(QThread):
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, model_type):
        super().__init__()
        self.model_type = model_type

    def run(self):
        try:
            from downloader import (
                download_diffusers_4bit,
                download_comfyui_gguf,
            )

            def progress_cb(msg, pct):
                self.progress_signal.emit(f"{msg} ({pct}%)" if pct >= 0 else msg)

            if self.model_type == "diffusers":
                result = download_diffusers_4bit(progress_callback=progress_cb)
            elif self.model_type == "comfyui":
                result = download_comfyui_gguf(progress_callback=progress_cb)
            else:
                self.error_signal.emit(f"Unknown model type: {self.model_type}")
                return

            if result:
                self.finished_signal.emit(f"{self.model_type} model ready! ✅")
            else:
                self.error_signal.emit("Download failed after retries. Check internet connection.")
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

        config_row.addWidget(QLabel("Key Color:"))
        self.key_combo = QComboBox()
        self.key_combo.addItems(["green", "red", "blue"])
        self.key_combo.setToolTip("Chroma-key color for background removal")
        config_row.addWidget(self.key_combo)

        self.dl_diffusers_btn = QPushButton("Download Diffusers Model")
        self.dl_diffusers_btn.clicked.connect(lambda: self.download_model("diffusers"))
        config_row.addWidget(self.dl_diffusers_btn)

        self.dl_comfy_btn = QPushButton("Download ComfyUI Model")
        self.dl_comfy_btn.clicked.connect(lambda: self.download_model("comfyui"))
        config_row.addWidget(self.dl_comfy_btn)

        config_row.addStretch()
        self.poll_toggle = QPushButton("Start Polling")
        self.poll_toggle.setCheckable(True)
        self.poll_toggle.clicked.connect(self.toggle_polling)
        config_row.addWidget(self.poll_toggle)
        layout.addLayout(config_row)

        self.status_label = QLabel("Not polling")
        layout.addWidget(self.status_label)

        tasks_group = QGroupBox("Available Tasks (click to claim)")
        tasks_layout = QVBoxLayout()
        self.tasks_list = QListWidget()
        self.tasks_list.itemClicked.connect(self.claim_task)
        tasks_layout.addWidget(self.tasks_list)
        tasks_group.setLayout(tasks_layout)
        layout.addWidget(tasks_group)

        active_group = QGroupBox("Active Task")
        active_layout = QVBoxLayout()
        self.active_task_label = QTextEdit()
        self.active_task_label.setMaximumHeight(120)
        self.active_task_label.setPlaceholderText("No active task")
        active_layout.addWidget(self.active_task_label)

        self.neg_label = QLabel("Negative Prompt (editable):")
        self.neg_label.setStyleSheet("color: #e94560; font-size: 11px; margin-top: 6px;")
        self.neg_label.setVisible(False)
        active_layout.addWidget(self.neg_label)
        self.neg_input = QTextEdit()
        self.neg_input.setPlaceholderText("No negative prompt — edit here to exclude things from this layer...")
        self.neg_input.setMinimumHeight(60)
        self.neg_input.setMaximumHeight(120)
        self.neg_input.setVisible(False)
        active_layout.addWidget(self.neg_input)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        active_layout.addWidget(self.progress)

        self.image_preview = QLabel()
        self.image_preview.setVisible(False)
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setMaximumHeight(300)
        self.image_preview.setStyleSheet("border: 1px solid #333; border-radius: 6px; padding: 4px;")
        active_layout.addWidget(self.image_preview)

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

    def download_model(self, model_type):
        self.dl_diffusers_btn.setEnabled(False)
        self.dl_comfy_btn.setEnabled(False)
        self.status_label.setText(f"Downloading {model_type} model... (may take several minutes)")

        self.dl_thread = DownloadThread(model_type)
        self.dl_thread.progress_signal.connect(self.on_dl_progress)
        self.dl_thread.finished_signal.connect(self.on_dl_finished)
        self.dl_thread.error_signal.connect(self.on_dl_error)
        self.dl_thread.start()

    def on_dl_progress(self, msg):
        self.status_label.setText(msg)

    def on_dl_finished(self, msg):
        self.status_label.setText(msg)
        self.dl_diffusers_btn.setEnabled(True)
        self.dl_comfy_btn.setEnabled(True)

    def on_dl_error(self, msg):
        self.status_label.setText(f"Download error: {msg}")
        self.dl_diffusers_btn.setEnabled(True)
        self.dl_comfy_btn.setEnabled(True)

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
                neg = self.active_task.get("negative_prompt") or ""
                self.active_task_label.setPlainText(
                    f"Task #{self.active_task['id']} — Layer {self.active_task['layer_number']}\n"
                    f"Prompt: {self.active_task['prompt']}"
                )
                self.neg_label.setVisible(True)
                self.neg_input.setPlainText(neg)
                self.neg_input.setVisible(True)
                self.generate_btn.setEnabled(True)
                self.progress.setVisible(True)
                self.progress.setValue(0)
                self.image_preview.setVisible(False)
                self.status_label.setText("Task claimed! Edit negative prompt if needed, then Generate.")
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
        self.neg_input.setVisible(False)
        self.neg_label.setVisible(False)
        self.image_preview.setVisible(False)
        self.status_label.setText(f"Generating with Qwen ({method})... this may take a few minutes")
        self.progress.setValue(0)

        output_dir = os.path.join(os.path.dirname(__file__), "output")
        self.gen_thread = GenerateThread(
            self.active_task_label.toPlainText().strip() or self.active_task["prompt"],
            method, output_dir, num_steps=15,
            key_color=self.key_combo.currentText(),
            negative_prompt=self.neg_input.toPlainText().strip() or None,
        )
        self.gen_thread.progress_signal.connect(self.on_gen_progress)
        self.gen_thread.progress_msg_signal.connect(lambda m: self.status_label.setText(m))
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
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            scaled = pixmap.scaledToWidth(500, Qt.TransformationMode.SmoothTransformation)
            self.image_preview.setPixmap(scaled)
            self.image_preview.setVisible(True)

    def on_gen_error(self, err):
        self.status_label.setText(f"Generation error: {err}")
        self.generate_btn.setEnabled(False)
        self.upload_btn.setEnabled(False)
        self.progress.setVisible(False)
        self.image_preview.setVisible(False)
        self.neg_input.setVisible(False)
        self.neg_label.setVisible(False)
        if self.active_task:
            try:
                requests.post(
                    f"{self.get_server()}/api/task/{self.active_task['id']}/reset",
                    timeout=5,
                )
            except Exception:
                pass
        self.active_task = None
        self.generated_path = None
        self.active_task_label.setPlainText("No active task — failed task returned to queue")
        self.poll_tasks()

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
                self.active_task_label.setPlainText("No active task")
                self.upload_btn.setEnabled(False)
                self.generate_btn.setEnabled(False)
                self.progress.setVisible(False)
                self.image_preview.setVisible(False)
                self.neg_input.setVisible(False)
                self.neg_label.setVisible(False)
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
