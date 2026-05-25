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
    QTabWidget,
    QCheckBox,
    QSlider,
)
from PyQt6.QtCore import QTimer, Qt, QThread, pyqtSignal, QRectF
from PyQt6.QtGui import QPixmap, QImage, QPainter, QShortcut, QKeySequence


SERVER_URL = "http://localhost:5000"


from itg_splitter import split_image_into_n_layers
from itg_judge import judge_layer_quality, determine_z_order
from itg_combine import reduce_to_6_layers
from itg_logger import itg_log, itg_error


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

            from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene
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
            self.zoom_level = 1.0
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
            self.zoom_level = 1.0
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
        self.zoom_level *= factor
        self.schedule_save()
        event.accept()

    def closeEvent(self, event):
        self.schedule_save()
        event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_R:
            self.view.rotate(90)
            self.rotation = (self.rotation + 90) % 360
            self.schedule_save()
        else:
            super().keyPressEvent(event)

    def moveEvent(self, event):
        super().moveEvent(event)
        self.schedule_save()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.schedule_save()

    def schedule_save(self):
        if hasattr(self, '_save_timer'):
            self._save_timer.start()

    def signal_save(self):
        viewer = self.window()
        if hasattr(viewer, '_auto_save_timer'):
            pass


class ViewerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.windows = []
        self.base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "output")
        layout = QVBoxLayout(self)

        title = QLabel("Scene Viewer")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #4ecca3; padding: 5px;")
        layout.addWidget(title)

        info = QLabel("Select a scene below. Layer windows open as separate floating windows. Move, resize, zoom, or rotate -- all settings auto-save to scene.json.")
        info.setWordWrap(True)
        info.setStyleSheet("color: #aaa; padding: 5px;")
        layout.addWidget(info)

        hint = QLabel("Wheel=zoom | Drag=pan | R=rotate 90° | Move/resize windows freely")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("color: gray; font-size: 10px; padding: 3px;")
        layout.addWidget(hint)

        sel_row = QHBoxLayout()
        self.prev_btn = QPushButton("Prev")
        self.prev_btn.setEnabled(False)
        self.prev_btn.clicked.connect(self.prev_scene)
        sel_row.addWidget(self.prev_btn)

        self.scene_combo = QComboBox()
        self.scene_combo.setMinimumWidth(250)
        self.scene_combo.currentTextChanged.connect(self.on_scene_change)
        sel_row.addWidget(self.scene_combo, 1)

        self.next_btn = QPushButton("Next")
        self.next_btn.setEnabled(False)
        self.next_btn.clicked.connect(self.next_scene)
        sel_row.addWidget(self.next_btn)
        layout.addLayout(sel_row)

        self.launch_btn = QPushButton("Open Layer Windows")
        self.launch_btn.clicked.connect(self.open_windows)
        self.launch_btn.setMinimumHeight(35)
        layout.addWidget(self.launch_btn)

        self.close_btn = QPushButton("Close All Windows")
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

        QShortcut(QKeySequence(Qt.Key.Key_Left), self, activated=self.prev_scene)
        QShortcut(QKeySequence(Qt.Key.Key_Right), self, activated=self.next_scene)

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
                lines.append(f"  {f} ({size_kb} KB)")
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
            self.status_label.setText("Error opening windows -- check log file")
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
        self.status_label.setText(f"{len(self.windows)} windows open -- {name}")
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


# ─── Shared TTG Worker / Support Classes ────────────────────────────────

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

            self.progress_msg_signal.emit("Removing background...")
            self.progress_signal.emit(92)
            chroma_key(green_path, final_path, self.key_color)

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
            from downloader import download_diffusers_4bit, download_comfyui_gguf

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
                self.finished_signal.emit(f"{self.model_type} model ready!")
            else:
                self.error_signal.emit("Download failed after retries.")
        except Exception as e:
            self.error_signal.emit(str(e))


# ─── TTG Tab Widgets (existing, cleaned up) ─────────────────────────────

class ClientWidget_TTG(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self._mw = main_window
        layout = QVBoxLayout(self)

        info = QLabel("Paste the FULL scene description below as one paragraph. The Boss will auto-split it into 6 depth layers using AI.")
        info.setWordWrap(True)
        info.setStyleSheet("color: #888; font-size: 11px; padding-bottom: 8px;")
        layout.addWidget(info)

        layout.addWidget(QLabel("Scene Description:"))
        self.desc_input = QTextEdit()
        self.desc_input.setMinimumHeight(250)
        self.desc_input.setPlaceholderText("e.g. The group camps in a moonlit forest clearing...")
        layout.addWidget(self.desc_input, stretch=1)

        style_row = QHBoxLayout()
        style_row.addWidget(QLabel("Style (optional):"))
        self.style_input = QLineEdit()
        self.style_input.setPlaceholderText("Ghibli animation (default)")
        style_row.addWidget(self.style_input)
        layout.addLayout(style_row)

        layout.addWidget(QLabel("Global Negative Prompt (applies to all layers):"))
        self.client_neg_input = QTextEdit()
        self.client_neg_input.setPlaceholderText("e.g. no text, no watermarks, no modern objects...")
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

        self.download_btn = QPushButton("Download All Layers")
        self.download_btn.clicked.connect(self.download_all_layers)
        self.download_btn.setEnabled(False)
        self.download_btn.setToolTip("Download all completed layers as layer1.png through layer6.png")
        layout.addWidget(self.download_btn)

        self.question_list.itemClicked.connect(self._on_client_select)
        self._selected_client_q = None

    def _on_client_select(self):
        item = self.question_list.currentItem()
        if item:
            q = item.data(Qt.ItemDataRole.UserRole)
            self._selected_client_q = q
            self.download_btn.setEnabled(q.get("status") == "completed" and q.get("tasks"))

    def download_all_layers(self):
        q = self._selected_client_q
        if not q or not q.get("tasks"):
            return
        folder = QFileDialog.getExistingDirectory(self, "Save layers to...")
        if not folder:
            return
        try:
            tasks = sorted(q["tasks"], key=lambda t: t.get("layer_number", 0))
            count = 0
            for t in tasks:
                fname = t.get("result_filename")
                if not fname:
                    continue
                r = requests.get(f"{self.get_server()}/api/result/{fname}", timeout=30)
                if r.ok:
                    layer = t.get("layer_number", count + 1)
                    outpath = os.path.join(folder, f"layer{layer}.png")
                    with open(outpath, "wb") as f:
                        f.write(r.content)
                    count += 1
            self.status_label.setText(f"Downloaded {count} layers to {folder}")
        except Exception as e:
            self.status_label.setText(f"Download error: {e}")

    def get_server(self):
        return self._mw.get_server()

    def submit_question(self):
        desc = self.desc_input.toPlainText().strip()
        if not desc:
            self.status_label.setText("Please enter a description.")
            return
        style = self.style_input.text().strip() or "Ghibli animation"
        full_desc = f"Style: {style}\n\n{desc}"
        global_neg = self.client_neg_input.toPlainText().strip()
        if global_neg:
            full_desc = f"[GLOBAL NEGATIVE PROMPT: {global_neg}]\n\n{full_desc}"
        try:
            r = requests.post(
                f"{self.get_server()}/api/question",
                json={"type": "TTG", "description": full_desc, "style": style, "global_negative_prompt": global_neg or None},
                timeout=10,
            )
            if r.ok:
                data = r.json()
                self.status_label.setText(f"Submitted! ID: {data['id']}")
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
            r = requests.get(f"{self.get_server()}/api/questions?type=TTG", timeout=10)
            if r.ok:
                for q in r.json():
                    text = f"#{q['id']} [{q['status']}]: {q.get('description','')[:80]}..."
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
        msg = f"Status: {q['status']}\nStyle: {q.get('style', 'none')}\n\n{q.get('description','')}"
        if q.get("tasks"):
            for t in q["tasks"]:
                msg += f"\n\nLayer {t.get('layer_number','?')}: {t['status']}"
                if t.get("result_filename"):
                    msg += f" -- {t['result_filename']}"
        detail.setText(msg)
        detail.exec()


class BossWidget_TTG(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self._mw = main_window
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

        llm_info = QLabel("LLM Setup: Install Ollama (ollama.com) or LM Studio (lmstudio.ai), then pull a model: ollama pull qwen3:14b")
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
        self.llm_model = QComboBox()
        self.llm_model.setEditable(True)
        self.llm_model.setMinimumWidth(180)
        self.llm_model.setToolTip("Select a model or type a custom name")
        llm_row.addWidget(self.llm_model)
        self.refresh_models_btn = QPushButton("Detect Models")
        self.refresh_models_btn.clicked.connect(self.detect_models)
        self.refresh_models_btn.setToolTip("Auto-detect available models from Ollama and LM Studio")
        llm_row.addWidget(self.refresh_models_btn)
        split_layout.addLayout(llm_row)
        self.split_btn = QPushButton("Auto-Split with LLM")
        self.split_btn.clicked.connect(self.auto_split)
        split_layout.addWidget(self.split_btn)
        pilot_row = QHBoxLayout()
        self.auto_pilot_cb = QCheckBox("Auto-Pilot")
        self.auto_pilot_cb.setToolTip("Auto-detect new pending scenes and split them without manual input")
        self.auto_pilot_cb.toggled.connect(self.toggle_auto_pilot)
        pilot_row.addWidget(self.auto_pilot_cb)
        self.pilot_status = QLabel("")
        pilot_row.addWidget(self.pilot_status)
        pilot_row.addStretch()
        split_layout.addLayout(pilot_row)
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
        tasks_layout.addWidget(self.boss_prompt_input)
        self.boss_neg_input = QTextEdit()
        self.boss_neg_input.setMaximumHeight(80)
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
        self.boss_poll_timer = QTimer()
        self.boss_poll_timer.timeout.connect(self._boss_poll)
        self._splitting_now = False
        self._split_ids = set()

    def get_server(self):
        return self._mw.get_server()

    def refresh(self):
        self.question_list.clear()
        try:
            r = requests.get(f"{self.get_server()}/api/questions?type=TTG", timeout=10)
            if r.ok:
                for q in r.json():
                    text = f"#{q['id']} [{q['status']}]"
                    item = QListWidgetItem(text)
                    item.setData(Qt.ItemDataRole.UserRole, q)
                    self.question_list.addItem(item)
        except Exception:
            pass
        self.check_llm()
        if self.llm_model.count() == 0:
            self.detect_models()

    def check_llm(self):
        try:
            r = requests.get(f"{self.get_server()}/api/health/llm?provider=ollama", timeout=5)
            if r.ok and r.json().get("available"):
                self.llm_label.setText("LLM: ready")
                self.llm_label.setStyleSheet("color: #4caf50")
            else:
                self.llm_label.setText("LLM: not available")
                self.llm_label.setStyleSheet("color: #e94560")
        except Exception:
            self.llm_label.setText("LLM: server error")
            self.llm_label.setStyleSheet("color: #e94560")

    def on_question_select(self):
        item = self.question_list.currentItem()
        if not item:
            return
        q = item.data(Qt.ItemDataRole.UserRole)
        self.current_question = q
        self.detail_text.setPlainText(f"#{q['id']} [{q['status']}]\nStyle: {q.get('style', 'none')}\n\n{q.get('description','')}")
        self.load_tasks(q)

    def load_tasks(self, q):
        self.tasks_list.clear()
        self.boss_prompt_input.clear()
        self.boss_neg_input.clear()
        self.boss_update_btn.setEnabled(False)
        if q.get("tasks"):
            for t in q["tasks"]:
                neg = t.get("negative_prompt", "")
                neg_str = f" | NEG: {neg[:40]}..." if neg else ""
                text = f"Layer {t.get('layer_number','?')}: [{t['status']}] {t.get('prompt','')[:60]}...{neg_str}"
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
            r = requests.put(f"{self.get_server()}/api/task/{tid}", json={"prompt": new_prompt, "negative_prompt": new_neg}, timeout=10)
            if r.ok:
                self.split_status.setText(f"Layer {t.get('layer_number','?')} updated")
                self.refresh()
            else:
                self.split_status.setText(f"Error: {r.json().get('error', r.text)}")
        except Exception as e:
            self.split_status.setText(f"Error: {e}")

    def detect_models(self):
        provider = self.llm_combo.currentText()
        self.llm_model.clear()
        self.split_status.setText("Detecting models...")
        try:
            if provider == "ollama":
                r = requests.get("http://localhost:11434/api/tags", timeout=5)
                if r.ok:
                    models = [m["name"] for m in r.json().get("models", [])]
                    if models:
                        self.llm_model.addItems(sorted(models))
                        self.split_status.setText(f"Found {len(models)} Ollama models")
                    else:
                        self.split_status.setText("No Ollama models found. Run: ollama pull <model>")
                        self.llm_model.setEditText("qwen3:14b")
                else:
                    self.split_status.setText("Ollama not reachable")
                    self.llm_model.setEditText("qwen3:14b")
            else:
                r = requests.get("http://localhost:1234/v1/models", timeout=5)
                if r.ok:
                    models = [m["id"] for m in r.json().get("data", [])]
                    if models:
                        self.llm_model.addItems(sorted(models))
                        self.split_status.setText(f"Found {len(models)} LM Studio models")
                    else:
                        self.split_status.setText("No LM Studio models loaded")
                        self.llm_model.setEditText("qwen3:14b")
                else:
                    self.split_status.setText("LM Studio not reachable")
                    self.llm_model.setEditText("qwen3:14b")
        except Exception as e:
            self.split_status.setText(f"Detection error: {e}")
            self.llm_model.setEditText("qwen3:14b")

    def auto_split(self):
        if not self.current_question:
            self.split_status.setText("Select a question first.")
            return
        qid = self.current_question["id"]
        provider = self.llm_combo.currentText()
        model = self.llm_model.currentText()
        self.split_status.setText(f"Splitting with {model}...")
        self.split_btn.setEnabled(False)
        try:
            r = requests.post(f"{self.get_server()}/api/question/{qid}/split", json={"provider": provider, "model": model}, timeout=180)
            if r.ok:
                data = r.json()
                self.split_status.setText(f"Split complete! {len(data.get('tasks', []))} layers created")
                self.refresh()
            else:
                self.split_status.setText(f"Error: {r.json().get('error', r.text)}")
        except Exception as e:
            self.split_status.setText(f"Error: {e}")
        self.split_btn.setEnabled(True)

    def toggle_auto_pilot(self, checked):
        if checked:
            self.boss_poll_timer.start(3000)
            self.pilot_status.setText("ON — watching for new scenes...")
            self.pilot_status.setStyleSheet("color: #4caf50; font-weight: bold;")
            self._boss_poll()
        else:
            self.boss_poll_timer.stop()
            self.pilot_status.setText("")
            self._splitting_now = False

    def _boss_poll(self):
        if self._splitting_now:
            return
        try:
            r = requests.get(f"{self.get_server()}/api/questions?type=TTG&status=pending", timeout=10)
            if r.ok:
                questions = r.json()
                new_pending = [q for q in questions if q["id"] not in self._split_ids]
                if new_pending:
                    q = new_pending[0]
                    self._split_ids.add(q["id"])
                    self.pilot_status.setText(f"ON — auto-splitting #{q['id']}...")
                    self.pilot_status.setStyleSheet("color: #ffc107; font-weight: bold;")
                    self._splitting_now = True
                    provider = self.llm_combo.currentText()
                    model = self.llm_model.currentText()
                    r2 = requests.post(
                        f"{self.get_server()}/api/question/{q['id']}/split",
                        json={"provider": provider, "model": model}, timeout=180)
                    if r2.ok:
                        self.pilot_status.setText(f"ON — #{q['id']} split! {len(r2.json().get('tasks', []))} layers")
                        self.pilot_status.setStyleSheet("color: #4caf50; font-weight: bold;")
                    else:
                        self.pilot_status.setText(f"ON — split #{q['id']} failed: {r2.json().get('error', r2.text)[:40]}")
                        self.pilot_status.setStyleSheet("color: #e94560; font-weight: bold;")
                    self._splitting_now = False
                else:
                    self.pilot_status.setText("ON — watching for new scenes...")
                    self.pilot_status.setStyleSheet("color: #4caf50; font-weight: bold;")
        except Exception as e:
            self._splitting_now = False
            self.pilot_status.setText(f"ON — error: {str(e)[:40]}")
            self.pilot_status.setStyleSheet("color: #e94560; font-weight: bold;")


class WorkerWidget_TTG(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self._mw = main_window
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
        self.auto_gen_cb = QCheckBox("Auto-Generate")
        self.auto_gen_cb.setToolTip("Auto-claim, generate, and upload tasks without manual input")
        config_row.addWidget(self.auto_gen_cb)
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
        self.neg_input.setPlaceholderText("No negative prompt")
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
        return self._mw.get_server()

    def download_model(self, model_type):
        self.dl_diffusers_btn.setEnabled(False)
        self.dl_comfy_btn.setEnabled(False)
        self.status_label.setText(f"Downloading {model_type} model...")
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
            r = requests.get(f"{self.get_server()}/api/tasks?status=pending&type=TTG", timeout=10)
            if r.ok:
                tasks = r.json()
                self.tasks_list.clear()
                for t in tasks:
                    text = f"Task #{t['id']} -- Layer {t.get('layer_number','?')}: {t.get('prompt','')[:80]}..."
                    item = QListWidgetItem(text)
                    item.setData(Qt.ItemDataRole.UserRole, t)
                    self.tasks_list.addItem(item)
                self.status_label.setText(f"Polling... ({len(tasks)} tasks available)")
                if self.auto_gen_cb.isChecked() and tasks and not self.active_task:
                    self.claim_task(task_dict=tasks[0])
        except Exception as e:
            self.status_label.setText(f"Poll error: {e}")

    def claim_task(self, item=None, task_dict=None):
        t = task_dict if task_dict else item.data(Qt.ItemDataRole.UserRole)
        if not t:
            return
        try:
            r = requests.post(f"{self.get_server()}/api/task/{t['id']}/claim", json={"worker_id": self.worker_id.text()}, timeout=10)
            if r.ok:
                self.active_task = r.json()
                neg = self.active_task.get("negative_prompt") or ""
                self.active_task_label.setPlainText(f"Task #{self.active_task['id']} -- Layer {self.active_task.get('layer_number','?')}\nPrompt: {self.active_task.get('prompt','')}")
                self.neg_label.setVisible(True)
                self.neg_input.setPlainText(neg)
                self.neg_input.setVisible(True)
                self.generate_btn.setEnabled(True)
                self.progress.setVisible(True)
                self.progress.setValue(0)
                self.image_preview.setVisible(False)
                self.status_label.setText("Task claimed! Edit negative prompt if needed, then Generate.")
                self.tasks_list.clear()
                if hasattr(self, 'auto_gen_cb') and self.auto_gen_cb.isChecked():
                    self.generate_image()
            else:
                self.status_label.setText(f"Claim error: {r.json().get('error', r.text)}")
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
        self.status_label.setText(f"Generating with Qwen ({method})...")
        self.progress.setValue(0)
        output_dir = os.path.join(os.path.dirname(__file__), "output")
        self.gen_thread = GenerateThread(
            self.active_task["prompt"],
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
        if hasattr(self, 'auto_gen_cb') and self.auto_gen_cb.isChecked():
            self.status_label.setText("Generated! Auto-uploading...")
            self.upload_result()
        else:
            self.status_label.setText("Generated! Click Upload Result PNG.")
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
                requests.post(f"{self.get_server()}/api/task/{self.active_task['id']}/reset", timeout=5)
            except Exception:
                pass
        self.active_task = None
        self.generated_path = None
        self.active_task_label.setPlainText("No active task -- failed task returned to queue")
        self.poll_tasks()

    def upload_result(self):
        filepath = self.generated_path
        if not filepath or not self.active_task:
            filepath, _ = QFileDialog.getOpenFileName(self, "Select PNG Result", "", "PNG Images (*.png)")
        if not filepath:
            return
        try:
            with open(filepath, "rb") as f:
                r = requests.post(f"{self.get_server()}/api/task/{self.active_task['id']}/result", files={"image": f}, timeout=30)
            if r.ok:
                self.status_label.setText("Uploaded!")
                self.active_task = None
                self.generated_path = None
                self.active_task_label.setPlainText("No active task")
                self.upload_btn.setEnabled(False)
                self.generate_btn.setEnabled(False)
                self.progress.setVisible(False)
                self.image_preview.setVisible(False)
                self.neg_input.setVisible(False)
                self.neg_label.setVisible(False)
                if hasattr(self, 'auto_gen_cb') and self.auto_gen_cb.isChecked():
                    self.poll_tasks()
            else:
                self.status_label.setText(f"Upload error: {r.json().get('error', r.text)}")
        except Exception as e:
            self.status_label.setText(f"Upload error: {e}")



# ─── ITG Tab Widgets (with actual ITG workers) ──────────────────────────

def _get_ollama_vision_models():
    """Query Ollama for ALL installed models — user picks which supports vision."""
    import subprocess
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=10)
        models = []
        for line in result.stdout.strip().split("\n")[1:]:
            parts = line.split()
            if parts:
                models.append(parts[0])
        return models if models else ["qwen3-vl:32b"]
    except Exception:
        return ["qwen3-vl:32b"]

class ClientWidget_ITG(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self._mw = main_window
        layout = QVBoxLayout(self)

        info = QLabel("Upload a painting/photo to decompose into 6 depth layers for Pepper's Ghost display.")
        info.setWordWrap(True)
        info.setStyleSheet("color: #888; font-size: 11px; padding-bottom: 8px;")
        layout.addWidget(info)

        upload_row = QHBoxLayout()
        self.file_label = QLabel("No file chosen")
        self.file_label.setStyleSheet("color: #aaa;")
        upload_row.addWidget(self.file_label)
        self.choose_btn = QPushButton("Choose Image")
        self.choose_btn.clicked.connect(self.choose_file)
        upload_row.addWidget(self.choose_btn)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Or paste image URL...")
        upload_row.addWidget(self.url_input)
        layout.addLayout(upload_row)

        self.image_preview = QLabel()
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setMaximumHeight(250)
        self.image_preview.setStyleSheet("border: 1px solid #333; border-radius: 6px; padding: 4px;")
        self.image_preview.setVisible(False)
        layout.addWidget(self.image_preview)

        depth_row = QHBoxLayout()
        self.depth_checkbox = QCheckBox("Manual depth")
        self.depth_checkbox.setChecked(False)
        depth_row.addWidget(self.depth_checkbox)
        self.depth_slider = QSlider(Qt.Orientation.Horizontal)
        self.depth_slider.setRange(1, 5)
        self.depth_slider.setValue(2)
        self.depth_slider.setEnabled(False)
        self.depth_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.depth_slider.valueChanged.connect(lambda v: self.depth_label.setText(f"Depth: {v}"))
        depth_row.addWidget(self.depth_slider)
        self.depth_label = QLabel("Depth: 2 (auto)")
        depth_row.addWidget(self.depth_label)
        self.depth_checkbox.toggled.connect(lambda checked: self.depth_slider.setEnabled(checked))
        self.depth_checkbox.toggled.connect(lambda checked: self.depth_label.setText(f"Depth: {self.depth_slider.value()}" if checked else "Depth: auto (Qwen3-VL)"))
        layout.addLayout(depth_row)

        self.submit_btn = QPushButton("Submit for Decomposition")
        self.submit_btn.clicked.connect(self.submit)
        layout.addWidget(self.submit_btn)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        layout.addWidget(QLabel("Your Decompositions:"))
        self.question_list = QListWidget()
        self.question_list.itemDoubleClicked.connect(self.open_question)
        layout.addWidget(self.question_list)
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh)
        layout.addWidget(self.refresh_btn)

        self.download_btn = QPushButton("📦 Download All Layers (ZIP)")
        self.download_btn.clicked.connect(self.download_zip)
        self.download_btn.setVisible(False)
        layout.addWidget(self.download_btn)

        self.chosen_file = None
        self._client_poll = QTimer()
        self._client_poll.timeout.connect(self.refresh)
        self._client_poll.start(5000)  # auto-refresh every 5s

    def get_server(self):
        return self._mw.get_server()

    def choose_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose Painting/Photo", "", "Images (*.png *.jpg *.jpeg *.webp);;All Files (*)")
        if path:
            self.chosen_file = path
            self.file_label.setText(os.path.basename(path))
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                scaled = pixmap.scaledToWidth(400, Qt.TransformationMode.SmoothTransformation)
                self.image_preview.setPixmap(scaled)
                self.image_preview.setVisible(True)

    def submit(self):
        url = self.url_input.text().strip()
        filepath = self.chosen_file

        if not filepath and not url:
            self.status_label.setText("Choose an image file or paste a URL.")
            return

        manual = self.depth_checkbox.isChecked()
        max_depth = self.depth_slider.value() if manual else 2

        try:
            if filepath:
                with open(filepath, "rb") as f:
                    r = requests.post(
                        f"{self.get_server()}/api/question/upload",
                        files={"file": f},
                        data={"max_depth": str(max_depth), "depth_control_manual": "1" if manual else "0", "description": os.path.basename(filepath)},
                        timeout=30,
                    )
            elif url:
                r = requests.post(
                    f"{self.get_server()}/api/question",
                    json={"type": "ITG", "description": url, "input_image_url": url, "max_depth": max_depth, "depth_control_manual": manual},
                    timeout=10,
                )
            else:
                return

            if r.ok:
                data = r.json()
                self.status_label.setText(f"Submitted! ID: {data['id']}")
                self.chosen_file = None
                self.file_label.setText("No file chosen")
                self.url_input.clear()
                self.image_preview.setVisible(False)
                self.refresh()
            else:
                self.status_label.setText(f"Error: {r.json().get('error', r.text)}")
        except Exception as e:
            self.status_label.setText(f"Connection error: {e}")

    def refresh(self):
        self.question_list.clear()
        self.download_btn.setVisible(False)
        try:
            r = requests.get(f"{self.get_server()}/api/questions?type=ITG", timeout=10)
            if r.ok:
                for q in r.json():
                    text = f"#{q['id']} [{q['status']}] depth={q.get('max_depth',0)}: {q.get('description','')[:60]}..."
                    item = QListWidgetItem(text)
                    item.setData(Qt.ItemDataRole.UserRole, q)
                    self.question_list.addItem(item)
                    if q.get("status") == "completed":
                        self._selected_download_q = q
                        self.download_btn.setVisible(True)
                        self.download_btn.setText(f"📦 Download Layers (Question #{q['id']})")
        except Exception:
            pass

    def open_question(self, item):
        q = item.data(Qt.ItemDataRole.UserRole)
        if not q:
            return
        if q.get("status") == "completed":
            self._selected_download_q = q
            self.download_btn.setVisible(True)
            self.download_btn.setText(f"📦 Download Layers (Question #{q['id']})")
        else:
            detail = QMessageBox(self)
            detail.setWindowTitle(f"Decomposition #{q['id']}")
            msg = f"Status: {q['status']}\nResolution: {q.get('original_resolution','?')}\nDepth: {q.get('max_depth',0)}"
            detail.setText(msg)
            detail.exec()

    def download_zip(self):
        q = getattr(self, '_selected_download_q', None)
        if not q:
            self.status_label.setText("Double-click a completed question first.")
            return
        try:
            r = requests.get(f"{self.get_server()}/api/question/{q['id']}/layers/download", timeout=60)
            if r.ok:
                save_path, _ = QFileDialog.getSaveFileName(self, "Save Layers ZIP", f"scene_{q['id']}_layers.zip", "ZIP Files (*.zip)")
                if save_path:
                    with open(save_path, "wb") as f:
                        f.write(r.content)
                    self.status_label.setText(f"Saved to {os.path.basename(save_path)}")
            else:
                self.status_label.setText(f"Download failed: {r.status_code}")
        except Exception as e:
            self.status_label.setText(f"Download error: {e}")


class BossWidget_ITG(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self._mw = main_window
        layout = QVBoxLayout(self)

        config_row = QHBoxLayout()
        config_row.addWidget(QLabel("Boss ID:"))
        self.boss_id = QLineEdit("boss-1")
        config_row.addWidget(self.boss_id)
        config_row.addWidget(QLabel("ComfyUI:"))
        self.comfy_url = QLineEdit("http://127.0.0.1:8188")
        config_row.addWidget(self.comfy_url)
        self.test_comfy_btn = QPushButton("Test ComfyUI")
        self.test_comfy_btn.clicked.connect(self.test_comfy)
        config_row.addWidget(self.test_comfy_btn)
        config_row.addWidget(QLabel("Vision:"))
        self.vision_model = QComboBox()
        self.vision_model.setEditable(True)
        self._populate_vision_models()
        config_row.addWidget(self.vision_model)
        self.auto_pilot_cb = QCheckBox("Auto-Pilot")
        self.auto_pilot_cb.setToolTip("Automatically split pending ITG questions, wait for children, and combine to 6 layers")
        self.auto_pilot_cb.clicked.connect(self._toggle_auto_pilot)
        config_row.addWidget(self.auto_pilot_cb)
        config_row.addStretch()
        layout.addLayout(config_row)

        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)

        self.state_label = QLabel("")
        self.state_label.setStyleSheet("color: #ffab40; font-weight: bold;")
        layout.addWidget(self.state_label)

        left_right = QHBoxLayout()
        left = QVBoxLayout()
        left.addWidget(QLabel("Pending ITG Questions:"))
        self.question_list = QListWidget()
        self.question_list.currentItemChanged.connect(self.on_question_select)
        left.addWidget(self.question_list)
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh)
        left.addWidget(self.refresh_btn)
        left_right.addLayout(left)

        right = QVBoxLayout()
        self.detail_group = QGroupBox("Question Detail")
        detail_layout = QVBoxLayout()
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setMinimumHeight(100)
        self.detail_text.setMaximumHeight(160)
        detail_layout.addWidget(self.detail_text)
        self.detail_group.setLayout(detail_layout)
        right.addWidget(self.detail_group)

        split_group = QGroupBox("Split Image")
        split_layout = QVBoxLayout()
        self.split_btn = QPushButton("Split with Qwen-Image-Layered (1->2)")
        self.split_btn.clicked.connect(self.split_and_process)
        split_layout.addWidget(self.split_btn)
        self.split_status = QLabel("")
        split_layout.addWidget(self.split_status)
        split_group.setLayout(split_layout)
        right.addWidget(split_group)

        children_group = QGroupBox("Children")
        children_layout = QVBoxLayout()
        self.children_list = QListWidget()
        children_layout.addWidget(self.children_list)
        self.combine_btn = QPushButton("Arrange Z-Order + Upload")
        self.combine_btn.clicked.connect(self.arrange_zorder)
        self.combine_btn.setEnabled(False)
        children_layout.addWidget(self.combine_btn)
        children_group.setLayout(children_layout)
        right.addWidget(children_group)

        left_right.addLayout(right)
        layout.addLayout(left_right)

        self.current_question = None
        self._boss_state = "idle"  # idle, processing_root, waiting_children, combining
        self._boss_timer = QTimer()
        self._boss_timer.timeout.connect(self._boss_poll)
        self.split_thread = None
        self.split_result = None
        self.root_task = None

    def _populate_vision_models(self):
        self.vision_model.clear()
        self.vision_model.addItems(_get_ollama_vision_models())

    def get_server(self):
        return self._mw.get_server()

    def test_comfy(self):
        try:
            r = requests.get(f"{self.comfy_url.text()}/system_stats", timeout=3)
            if r.status_code == 200:
                self.status_label.setText("ComfyUI: connected")
                self.status_label.setStyleSheet("color: #4caf50")
            else:
                self.status_label.setText("ComfyUI: not responding")
                self.status_label.setStyleSheet("color: #e94560")
        except Exception:
            self.status_label.setText("ComfyUI: not reachable")
            self.status_label.setStyleSheet("color: #e94560")

    def refresh(self):
        self.question_list.clear()
        try:
            r = requests.get(f"{self.get_server()}/api/questions?type=ITG&status=pending", timeout=10)
            if r.ok:
                for q in r.json():
                    text = f"#{q['id']}: {q.get('description','')[:60]}..."
                    item = QListWidgetItem(text)
                    item.setData(Qt.ItemDataRole.UserRole, q)
                    self.question_list.addItem(item)
        except Exception:
            pass

    def on_question_select(self):
        item = self.question_list.currentItem()
        if not item:
            return
        q = item.data(Qt.ItemDataRole.UserRole)
        self.current_question = q
        self.detail_text.setPlainText(f"#{q['id']} [{q['status']}]\nResolution: {q.get('original_resolution','?')}\nDepth: {q.get('max_depth',0)}\n{q.get('description','')}")
        self.load_children(q)

    def load_children(self, q):
        self.children_list.clear()
        try:
            r = requests.get(f"{self.get_server()}/api/question/{q['id']}/tree", timeout=10)
            if r.ok:
                tree = r.json().get("tree", [])
                for node in tree:
                    t = node.get("task", {})
                    text = f"Task #{t['id']} [{t['status']}] img={t.get('input_image','?')}"
                    item = QListWidgetItem(text)
                    item.setData(Qt.ItemDataRole.UserRole, t)
                    self.children_list.addItem(item)
        except Exception:
            pass

    def _toggle_auto_pilot(self):
        if self.auto_pilot_cb.isChecked():
            self._boss_state = "idle"
            self._boss_timer.start(3000)
            self.state_label.setText("ON — scanning for ITG questions...")
            self.state_label.setStyleSheet("color: #4caf50; font-weight: bold;")
            self._boss_poll()
        else:
            self._boss_timer.stop()
            self._boss_state = "idle"
            self.state_label.setText("")
            self.status_label.setText("Ready")

    def _boss_poll(self):
        if self._boss_state == "processing_root" and self.split_thread is not None:
            return  # split already running
        if self._boss_state == "waiting_children":
            self._check_children_completion()
            return
        if self._boss_state in ("processing_root", "combining"):
            return  # already working on a question

        try:
            r = requests.get(f"{self.get_server()}/api/questions?type=ITG&status=pending", timeout=10)
            if r.ok:
                questions = r.json()
                for q in questions:
                    self.current_question = q
                    self._start_root_split(q)
                    return
        except Exception as e:
            self.status_label.setText(f"Poll error: {e}")

    def _check_children_completion(self):
        if not self.root_task:
            return
        try:
            r = requests.get(f"{self.get_server()}/api/tasks?parent_task_id={self.root_task['id']}", timeout=10)
            if r.ok:
                tasks = r.json()
                if tasks and all(t.get("status") == "completed" for t in tasks):
                    itg_log(self.boss_id.text(), "CHILDREN_ALL_DONE", self.root_task["id"], f"starting Z-order")
                    requests.post(f"{self.get_server()}/api/task/{self.root_task['id']}/result",
                                  data={}, timeout=10)
                    self.status_label.setText("All children complete — arranging Z-order...")
                    self.combine_btn.setEnabled(True)
                    self.arrange_zorder()
        except Exception as e:
            self.status_label.setText(f"Children check error: {e}")

    def _start_root_split(self, q):
        self._boss_state = "processing_root"
        itg_log(self.boss_id.text(), "BOSS_START_ROOT", detail=f"question={q['id']}")
        self.state_label.setText(f"PROCESSING — Question #{q['id']}")
        self.state_label.setStyleSheet("color: #ffab40; font-weight: bold;")

        port = 8188
        try:
            port = int(self.comfy_url.text().rstrip("/").split(":")[-1])
        except ValueError:
            pass

        input_image = q.get("input_image_path", "")
        if not input_image:
            input_image = os.path.basename(q.get("input_image_url", ""))
        if not input_image:
            self.status_label.setText("No input image in question")
            self._boss_state = "idle"
            return

        # Create root task
        root_task = {
            "question_id": q["id"],
            "type": "ITG",
            "depth": 0,
            "max_depth": q.get("max_depth", 2),
            "prompt": "",
            "input_image": input_image,
        }
        try:
            r = requests.post(f"{self.get_server()}/api/tasks/batch",
                              json={"tasks": [root_task]}, timeout=10)
            if r.ok and r.json():
                self.root_task = r.json()[0]
                # Claim it
                cr = requests.post(f"{self.get_server()}/api/task/{self.root_task['id']}/claim",
                                   json={"worker_id": self.boss_id.text()}, timeout=10)
                if cr.ok:
                    self.root_task = cr.json()
                else:
                    self.root_task = r.json()[0]  # use created task even if claim fails
            else:
                self.status_label.setText("Failed to create root task")
                self._boss_state = "idle"
                return
        except Exception as e:
            self.status_label.setText(f"Root task error: {e}")
            self._boss_state = "idle"
            return

        self.status_label.setText(f"Root task #{self.root_task['id']} — splitting...")
        self.split_result = None
        output_dir = os.path.join("output", "itg", self.boss_id.text().replace(" ", "_"))
        self.split_thread = ITGSplitThread(
            self.get_server(), self.root_task,
            self.comfy_url.text(), self.vision_model.currentText(),
            output_dir, self.boss_id.text()
        )
        self.split_thread.progress_signal.connect(self._on_boss_progress)
        self.split_thread.finished_signal.connect(self._on_boss_finished)
        self.split_thread.error_signal.connect(self._on_boss_error)
        self.split_thread.start()

    def _on_boss_progress(self, msg):
        self.status_label.setText(msg)

    def _on_boss_finished(self, result):
        self.split_result = result
        self.split_thread = None

        if result.finish_type == "failed":
            self.status_label.setText("Root split failed — marking question failed")
            self._boss_state = "idle"
            return

        depth = self.root_task.get("depth", 0) or 0
        max_depth = self.root_task.get("max_depth", 2) or 2

        if depth >= max_depth:
            # Boss is at max depth — upload final directly (unusual)
            try:
                files = []
                for fn in result.uploaded_filenames:
                    output_dir = os.path.join("output", "itg", self.boss_id.text().replace(" ", "_"))
                    fp = os.path.join(output_dir, fn)
                    if os.path.exists(fp):
                        files.append(("images", (fn, open(fp, "rb"), "image/png")))
                if files:
                    requests.post(f"{self.get_server()}/api/task/{self.root_task['id']}/result",
                                  files=files, timeout=30)
                self.status_label.setText("Root at max depth — uploaded final.")
            except Exception as e:
                self.status_label.setText(f"Upload error: {e}")
            self._boss_state = "idle"
        else:
            # Create child tasks
            child_tasks = []
            for i, (fn, judgment) in enumerate(zip(result.uploaded_filenames, result.judgments)):
                desc = judgment.get("description", "")
                child_tasks.append({
                    "question_id": self.root_task["question_id"],
                    "type": "ITG",
                    "parent_task_id": self.root_task["id"],
                    "depth": depth + 1,
                    "max_depth": max_depth,
                    "prompt": f"Decompose this layer further: {desc}" if desc else "",
                    "input_image": fn,
                })
            if child_tasks:
                try:
                    r = requests.post(f"{self.get_server()}/api/tasks/batch",
                                      json={"tasks": child_tasks}, timeout=10)
                if r.ok:
                    self.status_label.setText(f"Created {len(child_tasks)} children — waiting...")
                    itg_log(self.boss_id.text(), "CHILDREN_CREATED", self.root_task["id"], f"count={len(child_tasks)} depth={(depth or 0)+1}")
                except Exception as e:
                    self.status_label.setText(f"Children error: {e}")

            # Save split metadata (via PUT, NOT complete — wait for children)
            split_data = {}
            if len(result.uploaded_filenames) >= 1:
                split_data["split_result_1"] = result.uploaded_filenames[0]
            if len(result.uploaded_filenames) >= 2:
                split_data["split_result_2"] = result.uploaded_filenames[1]
            try:
                requests.put(f"{self.get_server()}/api/task/{self.root_task['id']}",
                             json=split_data, timeout=10)
            except Exception:
                pass

            self._boss_state = "waiting_children"
            self.state_label.setText(f"WAITING — children of Question #{self.current_question['id']}")
            self.state_label.setStyleSheet("color: #ffab40; font-weight: bold;")
            self.combine_btn.setEnabled(True)

    def _on_boss_error(self, msg):
        self.split_thread = None
        self.status_label.setText(f"Split error: {msg[:100]}")
        self._boss_state = "idle"

    def split_and_process(self):
        if not self.current_question:
            self.split_status.setText("Select a question first.")
            return
        self.split_status.setText("")
        self._start_root_split(self.current_question)

    def arrange_zorder(self):
        if not self.current_question or self._boss_state != "waiting_children":
            self.split_status.setText("No children to arrange. Wait for split to complete.")
            self.split_status.setStyleSheet("color: #e94560")
            return

        self._boss_state = "combining"
        self.state_label.setText("COMBINING — downloading children and Z-ordering...")
        self.state_label.setStyleSheet("color: #ffab40; font-weight: bold;")
        self.split_status.setText("")

        try:
            qid = self.current_question["id"]
            output_dir = os.path.join("output", "itg", self.boss_id.text().replace(" ", "_"))
            os.makedirs(output_dir, exist_ok=True)

            # Get all leaf tasks (completed, with result filenames)
            r = requests.get(f"{self.get_server()}/api/question/{qid}/tree", timeout=10)
            if not r.ok:
                self.split_status.setText("Failed to get task tree")
                self._boss_state = "waiting_children"
                return

            tree = r.json().get("tree", [])
            all_results = self._collect_leaf_results(tree)

            if not all_results:
                self.split_status.setText("No completed leaf tasks yet")
                self._boss_state = "waiting_children"
                return

            if len(all_results) < 2:
                self.split_status.setText("Need at least 2 leaf layers to Z-order")
                self._boss_state = "waiting_children"
                return

            # Download all leaf result images
            downloaded = []
            for fn in all_results:
                local_path = os.path.join(output_dir, fn)
                if not os.path.exists(local_path):
                    img_r = requests.get(f"{self.get_server()}/api/files/{fn}", timeout=30)
                    if img_r.ok:
                        with open(local_path, "wb") as f:
                            f.write(img_r.content)
                if os.path.exists(local_path):
                    downloaded.append(local_path)

            if len(downloaded) < 2:
                self.split_status.setText("Could not download enough leaf images")
                self._boss_state = "waiting_children"
                return

            # Z-order using original image as reference
            original_image = self.current_question.get("input_image_path", "") or \
                              os.path.basename(self.current_question.get("input_image_url", ""))
            original_path = os.path.join(output_dir, original_image)
            if not os.path.exists(original_path) and original_image:
                img_r = requests.get(f"{self.get_server()}/api/files/{original_image}", timeout=30)
                if img_r.ok:
                    with open(original_path, "wb") as f:
                        f.write(img_r.content)

            if os.path.exists(original_path):
                z_ordered = determine_z_order(downloaded, original_path, model=self.vision_model.currentText())
            else:
                z_ordered = downloaded  # no parent — just use download order

            # Reduce to 6 layers
            final_6 = reduce_to_6_layers(z_ordered, output_dir)

            # Upload final 6
            files = []
            for i, path in enumerate(final_6):
                fname = f"layer_{i + 1}.png"
                files.append(("images", (fname, open(path, "rb"), "image/png")))

            r = requests.post(f"{self.get_server()}/api/question/{qid}/complete",
                              files=files, timeout=60)
            if r.ok:
                self.split_status.setText("Uploaded 6 final layers!")
                self.split_status.setStyleSheet("color: #4caf50")
                self.status_label.setText("Question completed!")
                self._boss_state = "idle"
                self.state_label.setText("DONE")
                self.state_label.setStyleSheet("color: #4caf50; font-weight: bold;")
                self.combine_btn.setEnabled(False)
            else:
                self.split_status.setText(f"Upload failed: {r.status_code}")
                self._boss_state = "waiting_children"

        except Exception as e:
            self.split_status.setText(f"Combine error: {e}")
            self.split_status.setStyleSheet("color: #e94560")
            self._boss_state = "waiting_children"

    def _collect_leaf_results(self, nodes):
        """Recursively collect result filenames from leaf tasks (no children)."""
        results = []
        for node in nodes:
            task = node.get("task", {})
            children = node.get("children", [])
            if not children:
                fn = task.get("result_filename", "")
                if fn:
                    results.extend(fn.split(","))
            else:
                results.extend(self._collect_leaf_results(children))
        return results


class ITGSplitResult:
    """Holds the result of an ITG split+judge+upload operation."""
    def __init__(self):
        self.good_layer_paths = []
        self.uploaded_filenames = []
        self.judgments = []
        self.finish_type = ""  # "children", "final", or "failed"


class ITGSplitThread(QThread):
    """Background thread: download → split (with retry) → judge → upload.
    
    Handles the full itg_node claim_and_process flow:
    1. Download input image from server
    2. split_image_into_n_layers (25s-10min, ComfyUI blocking)
    3. judge_layer_quality for each layer (2-5s each, Ollama)
    4. Dual-garbage retry loop (up to 3 attempts with new seeds)
    5. Upload good layers via POST /api/files/upload
    6. Emit ITGSplitResult with all data
    """
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(object)   # ITGSplitResult
    error_signal = pyqtSignal(str)

    def __init__(self, server_url, task, comfy_url, vision_model, output_dir, node_id="gui"):
        super().__init__()
        self.server_url = server_url
        self.task = task
        self.comfy_url = comfy_url
        self.vision_model = vision_model
        self.output_dir = output_dir
        self.node_id = node_id

    def run(self):
        result = ITGSplitResult()
        tid = self.task.get("id", "?")
        itg_log(self.node_id, "THREAD_START", tid, f"depth={self.task.get('depth')}/{self.task.get('max_depth')}")
        try:
            depth = self.task.get("depth", 0) or 0
            max_depth = self.task.get("max_depth", 2) or 2

            # Step 1: Download input image
            input_image = self.task.get("input_image", "")
            if not input_image:
                self.error_signal.emit("No input_image in task")
                return

            self.progress_signal.emit("Downloading input image...")
            input_path = os.path.join(self.output_dir, input_image)
            if not os.path.exists(input_path):
                r = requests.get(f"{self.server_url}/api/files/{input_image}", timeout=30)
                if r.ok:
                    os.makedirs(self.output_dir, exist_ok=True)
                    with open(input_path, "wb") as f:
                        f.write(r.content)
                else:
                    self.error_signal.emit(f"Download failed: {r.status_code}")
                    return

            # Step 2-4: Split + Judge with retry loop
            max_retries = 3
            port = 8188
            host = "127.0.0.1"
            try:
                url_parts = self.comfy_url.rstrip("/").replace("://", ":").split(":")
                host = url_parts[1] if len(url_parts) >= 2 else "127.0.0.1"
                port = int(url_parts[-1])
            except (ValueError, IndexError):
                pass

            for attempt in range(max_retries):
                if attempt > 0:
                    self.progress_signal.emit(f"All garbage — retrying (attempt {attempt + 1}/{max_retries})...")
                else:
                    self.progress_signal.emit("Splitting image (ComfyUI)...")

                # Split
                layer_files = split_image_into_n_layers(
                    input_path, self.output_dir, n=2,
                    steps=20, cfg=4.0, comfyui_host=host, comfyui_port=port,
                    prompt=self.task.get("prompt", "") or ""
                )

                if len(layer_files) != 2:
                    if attempt < max_retries - 1:
                        continue
                    self.error_signal.emit(f"Expected 2 layers, got {len(layer_files)}")
                    return

                # Judge each layer
                good_layers = []
                judgments = []
                itg_log(self.node_id, "SPLIT_DONE", tid, f"attempt={attempt+1} layers={len(layer_files)}")
                for i, lf in enumerate(layer_files):
                    self.progress_signal.emit(f"Judging layer {i + 1}/2...")
                    judgment = judge_layer_quality(
                        lf, model=self.vision_model,
                        parent_description=f"Sub-part {i + 1} from: {input_image}"
                    )
                    itg_log(self.node_id, "JUDGE_RESULT", tid, f"layer={i+1} quality={judgment.get('quality')}")
                    judgments.append(judgment)
                    if judgment["quality"] == "good":
                        good_layers.append(lf)

                if good_layers:
                    result.good_layer_paths = good_layers
                    result.judgments = judgments
                    break  # success!
                elif attempt >= max_retries - 1:
                    self.error_signal.emit("3 dual-garbage retries exhausted — branch failed")
                    result.finish_type = "failed"
                    self.finished_signal.emit(result)
                    return
                # else: continue retry

            # Step 5: Upload good layers
            result.uploaded_filenames = []
            for i, lf in enumerate(result.good_layer_paths):
                self.progress_signal.emit(f"Uploading good layer {i + 1}/{len(result.good_layer_paths)}...")
                with open(lf, "rb") as f:
                    r = requests.post(
                        f"{self.server_url}/api/files/upload",
                        files={"file": f},
                        data={"task_id": str(self.task["id"])},
                        timeout=30
                    )
                    if r.ok:
                        result.uploaded_filenames.append(r.json()["filename"])

            # Step 6: Determine finish type
            if depth >= max_depth:
                result.finish_type = "final"
            else:
                result.finish_type = "children"

            self.finished_signal.emit(result)

        except Exception as e:
            self.error_signal.emit(str(e))


class WorkerWidget_ITG(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self._mw = main_window
        layout = QVBoxLayout(self)

        config_row = QHBoxLayout()
        config_row.addWidget(QLabel("Worker ID:"))
        self.worker_id = QLineEdit("worker-itg-1")
        config_row.addWidget(self.worker_id)
        config_row.addWidget(QLabel("ComfyUI:"))
        self.comfy_url = QLineEdit("http://127.0.0.1:8188")
        config_row.addWidget(self.comfy_url)
        self.test_comfy_btn = QPushButton("Test")
        self.test_comfy_btn.clicked.connect(self.test_comfy)
        config_row.addWidget(self.test_comfy_btn)
        config_row.addWidget(QLabel("Vision:"))
        self.vision_model = QComboBox()
        self.vision_model.setEditable(True)
        self._populate_vision_models()
        config_row.addWidget(self.vision_model)
        config_row.addStretch()
        self.auto_process_cb = QCheckBox("Auto-Process")
        self.auto_process_cb.setToolTip("Automatically split+judge+upload when task is claimed")
        config_row.addWidget(self.auto_process_cb)
        self.poll_toggle = QPushButton("Start Polling")
        self.poll_toggle.setCheckable(True)
        self.poll_toggle.clicked.connect(self.toggle_polling)
        config_row.addWidget(self.poll_toggle)
        layout.addLayout(config_row)

        self.status_label = QLabel("Not polling")
        layout.addWidget(self.status_label)

        tasks_group = QGroupBox("Available ITG Tasks (click to claim)")
        tasks_layout = QVBoxLayout()
        self.tasks_list = QListWidget()
        self.tasks_list.itemClicked.connect(self.claim_task)
        tasks_layout.addWidget(self.tasks_list)
        tasks_group.setLayout(tasks_layout)
        layout.addWidget(tasks_group)

        active_group = QGroupBox("Active ITG Task")
        active_layout = QVBoxLayout()
        self.active_task_label = QTextEdit()
        self.active_task_label.setMaximumHeight(120)
        self.active_task_label.setPlaceholderText("No active task")
        active_layout.addWidget(self.active_task_label)

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
        self.split_btn = QPushButton("Split Image (1->2)")
        self.split_btn.clicked.connect(self.split_task)
        self.split_btn.setEnabled(False)
        gen_row.addWidget(self.split_btn)
        self.upload_btn = QPushButton("Upload Results")
        self.upload_btn.clicked.connect(self.upload_results)
        self.upload_btn.setEnabled(False)
        gen_row.addWidget(self.upload_btn)
        gen_row.addStretch()
        active_layout.addLayout(gen_row)
        active_group.setLayout(active_layout)
        layout.addWidget(active_group)

        self.poll_timer = QTimer()
        self.poll_timer.timeout.connect(self.poll_tasks)
        self.active_task = None
        self.split_thread = None
        self.split_result = None
        self._children_timer = QTimer()
        self._watching_children = False

    def _populate_vision_models(self):
        self.vision_model.clear()
        self.vision_model.addItems(_get_ollama_vision_models())

    def get_server(self):
        return self._mw.get_server()

    def test_comfy(self):
        try:
            r = requests.get(f"{self.comfy_url.text()}/system_stats", timeout=3)
            self.status_label.setText("ComfyUI: connected" if r.status_code == 200 else "ComfyUI: not responding")
        except Exception:
            self.status_label.setText("ComfyUI: not reachable")

    def toggle_polling(self):
        if self.poll_toggle.isChecked():
            self.poll_timer.start(5000)
            self.poll_toggle.setText("Stop Polling")
            self.status_label.setText("Polling for ITG tasks...")
            self.poll_tasks()
        else:
            self.poll_timer.stop()
            self.poll_toggle.setText("Start Polling")
            self.status_label.setText("Not polling")

    def poll_tasks(self):
        try:
            r = requests.get(f"{self.get_server()}/api/tasks?status=pending&type=ITG", timeout=10)
            if r.ok:
                tasks = r.json()
                self.tasks_list.clear()
                for t in tasks:
                    text = f"Task #{t['id']} depth={t.get('depth',0)}: {t.get('input_image','?')[:40]}..."
                    item = QListWidgetItem(text)
                    item.setData(Qt.ItemDataRole.UserRole, t)
                    self.tasks_list.addItem(item)
                self.status_label.setText(f"Polling... ({len(tasks)} ITG tasks)")
        except Exception as e:
            self.status_label.setText(f"Poll error: {e}")

    def claim_task(self, item):
        t = item.data(Qt.ItemDataRole.UserRole)
        if not t:
            return
        try:
            r = requests.post(f"{self.get_server()}/api/task/{t['id']}/claim", json={"worker_id": self.worker_id.text()}, timeout=10)
            if r.ok:
                self.active_task = r.json()
                self.active_task_label.setPlainText(f"Task #{self.active_task['id']} depth={self.active_task.get('depth',0)}\nInput: {self.active_task.get('input_image','')}\nPrompt: {self.active_task.get('prompt','')}")
                self.split_btn.setEnabled(True)
                self.status_label.setText("Task claimed!")
                self.tasks_list.clear()
                if self.auto_process_cb.isChecked():
                    self.split_task()
        except Exception as e:
            self.status_label.setText(f"Claim error: {e}")

    def split_task(self):
        if not self.active_task or self.split_thread is not None:
            return
        self.split_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)  # indeterminate
        self.status_label.setText("Starting split...")

        port = 8188
        try:
            port = int(self.comfy_url.text().rstrip("/").split(":")[-1])
        except ValueError:
            pass

        self.split_result = None
        self.split_thread = ITGSplitThread(
            self.get_server(), self.active_task,
            self.comfy_url.text(), self.vision_model.currentText(),
            os.path.join("output", "itg", self.worker_id.text().replace(" ", "_")),
            self.worker_id.text()
        )
        self.split_thread.progress_signal.connect(self._on_split_progress)
        self.split_thread.finished_signal.connect(self._on_split_finished)
        self.split_thread.error_signal.connect(self._on_split_error)
        self.split_thread.start()

    def _on_split_progress(self, msg):
        self.status_label.setText(msg)
        self.progress.setVisible(True)

    def _on_split_finished(self, result):
        self.split_result = result
        self.progress.setVisible(False)
        self.split_thread = None

        if result.finish_type == "failed":
            self.status_label.setText("Split failed — all retries exhausted")
            self.split_btn.setEnabled(False)
            self.upload_btn.setEnabled(False)
            self._reset_and_reclaim()
            return

        # Show preview of first good layer
        if result.good_layer_paths:
            pix = QPixmap(result.good_layer_paths[0])
            if not pix.isNull():
                scaled = pix.scaledToWidth(400, Qt.TransformationMode.SmoothTransformation)
                self.image_preview.setPixmap(scaled)
                self.image_preview.setVisible(True)

        self.status_label.setText(f"Split done ({len(result.good_layer_paths)} good layers). Upload ready.")
        self.upload_btn.setEnabled(True)

        if self.auto_process_cb.isChecked():
            self.upload_results()

    def _on_split_error(self, msg):
        self.progress.setVisible(False)
        self.split_thread = None
        self.status_label.setText(f"Split error: {msg[:100]}")
        self._reset_and_reclaim()

    def _reset_and_reclaim(self):
        if self.active_task:
            try:
                requests.post(f"{self.get_server()}/api/task/{self.active_task['id']}/reset", timeout=10)
            except Exception:
                pass
            self.active_task = None
        self.split_btn.setEnabled(False)
        self.upload_btn.setEnabled(False)
        self.image_preview.setVisible(False)
        if self.auto_process_cb.isChecked():
            self.poll_tasks()

    def upload_results(self):
        if not self.active_task or not self.split_result:
            return

        result = self.split_result
        depth = self.active_task.get("depth", 0) or 0
        max_depth = self.active_task.get("max_depth", 2) or 2

        try:
            if result.finish_type == "final" or depth >= max_depth:
                # LEAF — upload final images and complete immediately
                files = []
                for fn in result.uploaded_filenames:
                    fp = os.path.join(self.split_thread.output_dir, fn) if self.split_thread else None
                    if fp and os.path.exists(fp):
                        files.append(("images", (fn, open(fp, "rb"), "image/png")))
                if files:
                    r = requests.post(f"{self.get_server()}/api/task/{self.active_task['id']}/result",
                                      files=files, timeout=30)
                    if r.ok:
                        self.status_label.setText("Final results uploaded!")
                self._finish_task()
            else:
                # NON-LEAF — save metadata, create children, wait for children
                split_data = {}
                if len(result.uploaded_filenames) >= 1:
                    split_data["split_result_1"] = result.uploaded_filenames[0]
                if len(result.uploaded_filenames) >= 2:
                    split_data["split_result_2"] = result.uploaded_filenames[1]
                requests.put(f"{self.get_server()}/api/task/{self.active_task['id']}",
                             json=split_data, timeout=10)

                # Create child tasks
                child_tasks = []
                for i, (fn, judgment) in enumerate(zip(result.uploaded_filenames, result.judgments)):
                    desc = judgment.get("description", "")
                    child_tasks.append({
                        "question_id": self.active_task["question_id"],
                        "type": "ITG",
                        "parent_task_id": self.active_task["id"],
                        "depth": depth + 1,
                        "max_depth": max_depth,
                        "prompt": f"Decompose this layer further: {desc}" if desc else "",
                        "input_image": fn,
                    })
                if child_tasks:
                    r = requests.post(f"{self.get_server()}/api/tasks/batch",
                                      json={"tasks": child_tasks}, timeout=10)
                    if r.ok:
                        self.status_label.setText(f"Created {len(child_tasks)} children — watching...")

                # Start watching children (do NOT mark self complete yet)
                self._start_watching_children()

        except Exception as e:
            self.status_label.setText(f"Upload error: {e}")

    def _finish_task(self):
        self.active_task = None
        self.split_result = None
        self.split_btn.setEnabled(False)
        self.upload_btn.setEnabled(False)
        self.image_preview.setVisible(False)
        self.active_task_label.setPlainText("No active task")
        if self.auto_process_cb.isChecked():
            self.poll_tasks()

    def _start_watching_children(self):
        self._watching_children = True
        try:
            self._children_timer.timeout.disconnect()
        except TypeError:
            pass
        self._children_timer.timeout.connect(self._check_children)
        self._children_timer.start(5000)
        self.split_btn.setEnabled(False)
        self.upload_btn.setEnabled(False)

    def _check_children(self):
        if not self.active_task:
            self._finish_watching()
            return
        try:
            r = requests.get(f"{self.get_server()}/api/tasks?parent_task_id={self.active_task['id']}", timeout=10)
            if r.ok:
                tasks = r.json()
                if tasks and all(t.get("status") == "completed" for t in tasks):
                    requests.post(f"{self.get_server()}/api/task/{self.active_task['id']}/result",
                                  data={}, timeout=10)
                    self.status_label.setText("Children complete — task done!")
                    self._finish_watching()
        except Exception:
            pass

    def _finish_watching(self):
        self._watching_children = False
        try:
            self._children_timer.stop()
            self._children_timer.timeout.disconnect()
        except TypeError:
            pass
        self._finish_task()


# ─── Main Window with Tabs ──────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Strulovitz Ghost")
        self.setMinimumSize(950, 680)

        central = QWidget()
        self.setCentralWidget(central)
        outer_layout = QVBoxLayout(central)

        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("Server:"))
        self.server_input = QLineEdit(SERVER_URL)
        self.server_input.setMaximumWidth(300)
        top_bar.addWidget(self.server_input)
        top_bar.addStretch()
        top_bar.addWidget(QLabel("Role:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Client", "Boss", "Worker", "Viewer"])
        self.mode_combo.currentTextChanged.connect(self.switch_mode)
        top_bar.addWidget(self.mode_combo)
        outer_layout.addLayout(top_bar)

        # Tabs
        self.tabs = QTabWidget()
        self.ttg_stack = QStackedWidget()
        self.itg_stack = QStackedWidget()

        # TTG widgets
        self.client_ttg = ClientWidget_TTG(self)
        self.boss_ttg = BossWidget_TTG(self)
        self.worker_ttg = WorkerWidget_TTG(self)
        self.ttg_stack.addWidget(self.client_ttg)
        self.ttg_stack.addWidget(self.boss_ttg)
        self.ttg_stack.addWidget(self.worker_ttg)

        # ITG widgets
        self.client_itg = ClientWidget_ITG(self)
        self.boss_itg = BossWidget_ITG(self)
        self.worker_itg = WorkerWidget_ITG(self)
        self.itg_stack.addWidget(self.client_itg)
        self.itg_stack.addWidget(self.boss_itg)
        self.itg_stack.addWidget(self.worker_itg)

        self.tabs.addTab(self.ttg_stack, "Text To Ghost (TTG)")
        self.tabs.addTab(self.itg_stack, "Image To Ghost (ITG)")

        outer_layout.addWidget(self.tabs)

        # Viewer (separate from TTG/ITG tabs)
        self.viewer_widget = ViewerWidget()
        self.viewer_widget.hide()
        outer_layout.addWidget(self.viewer_widget)

        # Sync mode across tabs
        self.mode_combo.currentTextChanged.connect(self.switch_mode)

    def switch_mode(self, mode):
        idx = 0 if mode == "Client" else 1 if mode == "Boss" else 2 if mode == "Worker" else 3
        if idx == 3:
            self.tabs.hide()
            self.viewer_widget.show()
            self.viewer_widget.refresh_scenes()
            return
        self.viewer_widget.hide()
        self.tabs.show()
        self.ttg_stack.setCurrentIndex(idx)
        self.itg_stack.setCurrentIndex(idx)
        if mode == "Boss":
            self.boss_ttg.refresh()
            self.boss_itg.refresh()

    def get_server(self):
        return self.server_input.text().rstrip("/")


# ─── Dark Theme + Main ──────────────────────────────────────────────────

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
    QPushButton:hover { background-color: #c73652; }
    QPushButton:disabled { background-color: #555; color: #999; }
    QPushButton:checked { background-color: #4ecca3; }
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
    QLabel { color: #eee; }
    QListWidget::item:selected { background-color: #e94560; }
    QProgressBar {
        border: 1px solid #333;
        border-radius: 4px;
        text-align: center;
    }
    QProgressBar::chunk {
        background-color: #4ecca3;
        border-radius: 3px;
    }
    QTabWidget::pane { border: 1px solid #333; }
    QTabBar::tab {
        background: #0f3460;
        padding: 8px 16px;
        border: 1px solid #333;
        border-bottom: none;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
    }
    QTabBar::tab:selected { background: #e94560; color: white; }
    QCheckBox { color: #eee; }
    QSlider::groove:horizontal {
        border: 1px solid #333;
        height: 6px;
        background: #0f3460;
        border-radius: 3px;
    }
    QSlider::handle:horizontal {
        background: #4ecca3;
        width: 16px;
        margin: -6px 0;
        border-radius: 8px;
    }
    """

    app.setStyleSheet(dark_style)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
