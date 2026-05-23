import sys
import os
import json
import logging
import traceback
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QWidget, QGraphicsView, QGraphicsScene, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QComboBox, QGroupBox,
)
from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import QPixmap, QImage, QPainter, QShortcut, QKeySequence

log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"scene_viewer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(filename=log_file, level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s: %(message)s')
logging.info("Scene viewer starting")

SETTINGS_FILE = "scene.json"


class LayerWindow(QWidget):
    def __init__(self, layer_path, layer_index, saved_state=None):
        super().__init__()
        self.layer_path = layer_path
        self.layer_index = layer_index
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
        self.view.setStyleSheet("background: transparent; border: none;")
        self.view.setBackgroundBrush(Qt.GlobalColor.transparent)
        self.setStyleSheet("background-color: #0d0d0d;")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        self.scene = QGraphicsScene()
        self.scene.setBackgroundBrush(Qt.GlobalColor.transparent)
        self.pixmap_item = self.scene.addPixmap(QPixmap())
        self.view.setScene(self.scene)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view)
        self.setLayout(layout)

        self.zoom_level = 1.0
        self.rotation = 0
        self._loading = True
        self.load_image(layer_path)
        self.restore_state(saved_state)
        self._loading = False

        self._save_timer = QTimer()
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(200)
        self._save_timer.timeout.connect(self.request_save)

    def load_image(self, path):
        img = QImage(path)
        if img.isNull():
            self.setWindowTitle(f"Layer {self.layer_index + 1} (not found)")
            return
        pix = QPixmap.fromImage(img)
        self.pixmap_item.setPixmap(pix)
        self.scene.setSceneRect(QRectF(pix.rect()))

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

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_R:
            self.view.rotate(90)
            self.rotation = (self.rotation + 90) % 360
            self.schedule_save()
        else:
            super().keyPressEvent(event)

    def schedule_save(self):
        if not self._loading:
            self._save_timer.start()

    def request_save(self):
        viewer = self.window()
        if hasattr(viewer, 'save_all'):
            viewer.save_all()

    def moveEvent(self, event):
        super().moveEvent(event)
        self.schedule_save()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.schedule_save()

    def wheelEvent(self, event):
        factor = 1.1 if event.angleDelta().y() > 0 else 0.9
        self.view.scale(factor, factor)
        self.zoom_level *= factor
        self.schedule_save()
        event.accept()

    def closeEvent(self, event):
        self.schedule_save()
        event.accept()


class SceneViewer(QWidget):
    def __init__(self, outputs_dir, initial_scene=None):
        super().__init__()
        self.outputs_dir = os.path.abspath(outputs_dir)
        self.current_folder = None
        self.windows = []
        self.scenes = self._scan_scenes()

        self.setWindowTitle("StrulovitzGhost — Scene Viewer")
        self.setFixedSize(440, 220)

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 8, 10, 8)

        self.scene_label = QLabel("No scene loaded")
        self.scene_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.scene_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.scene_label)

        nav = QHBoxLayout()

        self.prev_btn = QPushButton("◀ Prev")
        self.prev_btn.setEnabled(False)
        self.prev_btn.clicked.connect(self.prev_scene)
        nav.addWidget(self.prev_btn)

        self.scene_combo = QComboBox()
        self.scene_combo.setMinimumWidth(200)
        for s in self.scenes:
            self.scene_combo.addItem(s)
        self.scene_combo.currentTextChanged.connect(self.on_combo_change)
        nav.addWidget(self.scene_combo, 1)

        self.next_btn = QPushButton("Next ▶")
        self.next_btn.setEnabled(False)
        self.next_btn.clicked.connect(self.next_scene)
        nav.addWidget(self.next_btn)

        layout.addLayout(nav)

        hint = QLabel("Wheel=zoom | Drag=pan | R=rotate 90° | ← →=switch scene")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(hint)

        self.preview_group = QGroupBox("Scene Contents")
        preview_layout = QVBoxLayout()
        self.preview_label = QLabel("")
        self.preview_label.setWordWrap(True)
        self.preview_label.setStyleSheet("color: #ccc; font-size: 11px;")
        preview_layout.addWidget(self.preview_label)
        self.preview_group.setLayout(preview_layout)
        layout.addWidget(self.preview_group)

        self.setLayout(layout)

        self._auto_save_timer = QTimer()
        self._auto_save_timer.setInterval(2000)
        self._auto_save_timer.timeout.connect(self.save_all)

        QShortcut(QKeySequence(Qt.Key.Key_Left), self, activated=self.prev_scene)
        QShortcut(QKeySequence(Qt.Key.Key_Right), self, activated=self.next_scene)

        if initial_scene and initial_scene in self.scenes:
            self.scene_combo.setCurrentText(initial_scene)
        elif self.scenes:
            self.scene_combo.setCurrentIndex(0)

        self.show()
        self.raise_()
        self.activateWindow()

    def _scan_scenes(self):
        scenes = []
        if os.path.isdir(self.outputs_dir):
            for entry in sorted(os.listdir(self.outputs_dir)):
                path = os.path.join(self.outputs_dir, entry)
                if os.path.isdir(path):
                    pngs = [f for f in os.listdir(path) if f.lower().endswith('.png')]
                    if pngs:
                        scenes.append(entry)
        return scenes

    def on_combo_change(self, name):
        if name and name != self.current_folder:
            self.load_scene(name)

    def load_scene(self, name):
        self.save_all()
        for w in self.windows:
            w.close()
        self.windows.clear()

        folder = os.path.join(self.outputs_dir, name)
        settings_path = os.path.join(folder, SETTINGS_FILE)
        saved = {}
        if os.path.exists(settings_path):
            try:
                with open(settings_path, 'r') as f:
                    saved = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

        png_files = sorted(
            f for f in os.listdir(folder)
            if f.lower().endswith('.png') and 'composite' not in f.lower()
        )[:6]

        self.current_folder = name
        self.scene_label.setText(f"\U0001f4c1 {name}")

        lines = []
        for f in sorted(os.listdir(folder)):
            if f.lower().endswith('.png') and 'composite' not in f.lower():
                size_kb = os.path.getsize(os.path.join(folder, f)) // 1024
                lines.append(f"  {f} ({size_kb} KB)")
        self.preview_label.setText("\n".join(lines))

        for i, fname in enumerate(png_files):
            path = os.path.join(folder, fname)
            state = saved.get(str(i), None) if saved else None
            w = LayerWindow(path, i, state)
            w.show()
            w.raise_()
            w.activateWindow()
            self.windows.append(w)

        self._auto_save_timer.start()
        self._update_nav()

    def _update_nav(self):
        if not self.scenes:
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            return
        try:
            idx = self.scenes.index(self.current_folder)
        except ValueError:
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            return
        self.prev_btn.setEnabled(idx > 0)
        self.next_btn.setEnabled(idx < len(self.scenes) - 1)

    def prev_scene(self):
        if not self.scenes:
            return
        try:
            idx = self.scenes.index(self.current_folder)
        except ValueError:
            return
        if idx > 0:
            self.scene_combo.setCurrentText(self.scenes[idx - 1])

    def next_scene(self):
        if not self.scenes:
            return
        try:
            idx = self.scenes.index(self.current_folder)
        except ValueError:
            return
        if idx < len(self.scenes) - 1:
            self.scene_combo.setCurrentText(self.scenes[idx + 1])

    def save_all(self):
        if not self.current_folder or not self.windows:
            return
        folder = os.path.join(self.outputs_dir, self.current_folder)
        state = {}
        for i, w in enumerate(self.windows):
            state[str(i)] = w.get_state()
        try:
            with open(os.path.join(folder, SETTINGS_FILE), 'w') as f:
                json.dump(state, f, indent=2)
        except IOError:
            pass

    def closeEvent(self, event):
        self.save_all()
        self._auto_save_timer.stop()
        for w in self.windows:
            w.close()
        event.accept()


def launch_scene_viewer(scene_name=None):
    try:
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)
        logging.info("QApplication created")

        def excepthook(exc_type, exc_value, tb):
            logging.critical("".join(traceback.format_exception(exc_type, exc_value, tb)))
            sys.__excepthook__(exc_type, exc_value, tb)
        sys.excepthook = excepthook
        logging.info("Exception hook installed")

        repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        outputs_dir = os.path.join(repo_dir, "src", "output")
        logging.info(f"Outputs dir: {outputs_dir}")

        if not os.path.isdir(outputs_dir):
            logging.error(f"Outputs directory not found: {outputs_dir}")
            sys.exit(1)

        if scene_name is None and len(sys.argv) > 1:
            scene_name = sys.argv[1]
        logging.info(f"Initial scene: {scene_name}")

        viewer = SceneViewer(outputs_dir, initial_scene=scene_name)
        logging.info(f"Viewer created, {len(viewer.windows)} layer windows, {len(viewer.scenes)} scenes")
        logging.info("Entering event loop")
        app.exec()
        logging.info("Event loop ended")
    except Exception:
        logging.critical(f"Fatal: {traceback.format_exc()}")
        raise


if __name__ == "__main__":
    launch_scene_viewer()
