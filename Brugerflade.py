import os
import sys

import pygame
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from funktions import calculate_path_cost, find_path
from klasser import (
    LODRET,
    TILE_SIZE,
    VANDRET,
    RandomWorld,
    SandboxWorld,
)

SCREEN_WIDTH = VANDRET * TILE_SIZE
SCREEN_HEIGHT = LODRET * TILE_SIZE

START_COLOR = (255, 230, 0)
GOAL_COLOR = (220, 30, 30)

class GameView(QWidget):
    """Pygame-tegneflade indlejret i et Qt-widget."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_NativeWindow, True)
        self.setAttribute(Qt.WidgetAttribute.WA_DontCreateNativeAncestors, True)
        self.setFixedSize(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.world = None
        self.world_type = None
        self.goal = None
        self.path = []
        self.score = 0
        self.start = (0, 0)

        self.sandbox_mode = "goal"
        self.selected_terrain = None
        self.brush_radius = 4

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_game)

    def showEvent(self, event):
        super().showEvent(event)

        if not pygame.get_init():
            pygame.init()

        if pygame.display.get_surface() is None:
            # Opret Pygame-fladen inde i Qt-widgettens vindue.
            os.environ["SDL_WINDOWID"] = str(int(self.winId()))

            if sys.platform.startswith("win"):
                os.environ["SDL_VIDEODRIVER"] = "windib"

            pygame.display.init()
            pygame.display.set_mode(
                (SCREEN_WIDTH, SCREEN_HEIGHT),
                pygame.NOFRAME,
            )
            pygame.display.set_caption("Terræn")

        self.timer.start(16)

    def start_random_world(self):
        self.world = RandomWorld()
        self.world_type = "random"
        self.reset_route()
        self.setFocus()

    def start_sandbox_world(self):
        self.world = SandboxWorld()
        self.world_type = "sandbox"
        self.sandbox_mode = "goal"
        self.selected_terrain = None
        self.reset_route()
        self.setFocus()

    def reset_route(self):
        self.goal = None
        self.path = []
        self.score = 0
        self.update_score_label()

    def update_score_label(self):
        main_window = self.window()
        if hasattr(main_window, "score_label"):
            main_window.score_label.setText(f"Rute-score: {self.score:.1f}")

    def update_game(self):
        if self.world is None or pygame.display.get_surface() is None:
            return

        surface = pygame.display.get_surface()
        self.world.draw(surface)

        if self.path:
            self.world.draw_path(surface, self.path)

        start_center = (
            self.start[0] * TILE_SIZE + TILE_SIZE // 2,
            self.start[1] * TILE_SIZE + TILE_SIZE // 2,
        )
        pygame.draw.circle(surface, START_COLOR, start_center, 8)

        if self.goal is not None:
            goal_center = (
                self.goal[0] * TILE_SIZE + TILE_SIZE // 2,
                self.goal[1] * TILE_SIZE + TILE_SIZE // 2,
            )
            pygame.draw.circle(surface, GOAL_COLOR, goal_center, 8)

        pygame.display.flip()
        self.update_score_label()

    def keyPressEvent(self, event):
        if self.world_type != "sandbox":
            return

        key = event.key()

        if key == Qt.Key.Key_R:
            self.sandbox_mode = "goal"
            self.selected_terrain = None
        elif key == Qt.Key.Key_B:
            self.sandbox_mode = "paint"
            self.selected_terrain = self.world.mountains
        elif key == Qt.Key.Key_V:
            self.sandbox_mode = "paint"
            self.selected_terrain = self.world.water
        elif key == Qt.Key.Key_G:
            self.sandbox_mode = "paint"
            self.selected_terrain = self.world.grass
        else:
            return

        self.update_game()

    def mousePressEvent(self, event):
        if self.world is None or event.button() != Qt.MouseButton.LeftButton:
            return

        col = int(event.position().x()) // TILE_SIZE
        row = int(event.position().y()) // TILE_SIZE

        if not (0 <= col < VANDRET and 0 <= row < LODRET):
            return

        position = (col, row)

        if self.world_type == "sandbox" and self.sandbox_mode == "paint":
            self.paint_brush(position)
        elif self.world.is_grass(position):
            self.goal = position
            self.path = find_path(self.world, self.start, self.goal)
            self.score = calculate_path_cost(self.world, self.path)
            self.update_score_label()

        self.update_game()

    def paint_brush(self, center):
        """Tegner en cirkulær pensel med radius målt i felter."""
        center_col, center_row = center
        radius = self.brush_radius - 1

        for row in range(
            max(0, center_row - radius),
            min(LODRET, center_row + radius + 1),
        ):
            for col in range(
                max(0, center_col - radius),
                min(VANDRET, center_col + radius + 1),
            ):
                dx = col - center_col
                dy = row - center_row

                if dx * dx + dy * dy > radius * radius:
                    continue

                position = (col, row)

                # Startfeltet holdes som græs, så en rute altid kan starte.
                if (
                    position == self.start
                    and self.selected_terrain is not self.world.grass
                ):
                    continue

                self.world.set_terrain(position, self.selected_terrain)

        self.reset_route()

    def set_brush_radius(self, radius):
        self.brush_radius = radius

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Terræn og ruteplanlægning")
        self.resize(1000, 820)
        self.setMinimumSize(780, 760)

        self.setStyleSheet(
            """
            QMainWindow, QWidget {
                background: white;
                color: black;
            }

            QFrame#gameFrame {
                border: 1px solid black;
                background: white;
            }

            QLabel#scoreLabel {
                border: 1px solid black;
                background: white;
                color: black;
                font-size: 16px;
                padding: 4px;
            }

            QPushButton {
                background: white;
                color: black;
                border: 1px solid black;
                padding: 10px;
                min-height: 38px;
                font-size: 14px;
            }

            QPushButton:hover {
                background: #eeeeee;
            }

            QPushButton:pressed {
                background: #dddddd;
            }
            """
        )

        root = QWidget()
        self.setCentralWidget(root)

        layout = QHBoxLayout(root)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(36)

        self.game = GameView(self)

        controls = QVBoxLayout()
        controls.setSpacing(14)
        controls.addStretch(1)

        random_button = QPushButton("Random")
        random_button.clicked.connect(self.game.start_random_world)
        controls.addWidget(random_button)

        sandbox_button = QPushButton("Sandbox")
        sandbox_button.clicked.connect(self.game.start_sandbox_world)
        controls.addWidget(sandbox_button)

        help_text = QLabel(
            "Sandbox-taster:\n"
            "B = bjerg\n"
            "V = vand\n"
            "G = græs\n"
            "R = vælg mål"
        )
        controls.addWidget(help_text)

        brush_label = QLabel("Penselradius: 4 felt")
        controls.addWidget(brush_label)

        brush_slider = QSlider(Qt.Orientation.Horizontal)
        brush_slider.setMinimum(1)
        brush_slider.setMaximum(8)
        brush_slider.setValue(4)
        brush_slider.setToolTip("Vælg penslens radius i felter")

        def update_brush_radius(radius):
            self.game.set_brush_radius(radius)
            brush_label.setText(f"Penselradius: {radius} felter")

        brush_slider.valueChanged.connect(update_brush_radius)
        controls.addWidget(brush_slider)

        quit_button = QPushButton("Quit")
        quit_button.clicked.connect(self.close)
        controls.addWidget(quit_button)

        controls.addStretch(1)

        control_widget = QWidget()
        control_widget.setLayout(controls)
        control_widget.setFixedWidth(150)

        game_frame = QFrame()
        game_frame.setObjectName("gameFrame")

        game_layout = QVBoxLayout(game_frame)
        game_layout.setContentsMargins(1, 1, 1, 1)
        game_layout.setSpacing(6)

        self.score_label = QLabel("Rute-score: 0.0")
        self.score_label.setObjectName("scoreLabel")
        self.score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.score_label.setFixedHeight(32)
        game_layout.addWidget(self.score_label)

        game_layout.addWidget(
            self.game,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )

        layout.addWidget(control_widget)
        layout.addWidget(game_frame, 1)

    def closeEvent(self, event):
        self.game.timer.stop()
        pygame.quit()
        event.accept()