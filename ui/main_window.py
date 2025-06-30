import logging
import os

from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import (
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from core.symlink import create_symlink, is_admin
from ui.file_tree import FileTreeView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SymLink GUI")
        self.setGeometry(100, 100, 1200, 800)

        if is_admin():
            self.setWindowTitle(self.windowTitle() + " (Administrator)")

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 创建左侧面板
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_toolbar = QToolBar()
        self.left_up_btn = QPushButton("向上")
        self.left_reset_btn = QPushButton("重置")
        left_toolbar.addWidget(self.left_up_btn)
        left_toolbar.addWidget(self.left_reset_btn)
        left_layout.addWidget(left_toolbar)
        self.left_tree = FileTreeView()
        left_layout.addWidget(self.left_tree)
        left_widget.setLayout(left_layout)

        # 创建右侧面板
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_toolbar = QToolBar()
        self.right_up_btn = QPushButton("向上")
        self.right_reset_btn = QPushButton("重置")
        right_toolbar.addWidget(self.right_up_btn)
        right_toolbar.addWidget(self.right_reset_btn)
        right_layout.addWidget(right_toolbar)
        self.right_tree = FileTreeView()
        right_layout.addWidget(self.right_tree)
        right_widget.setLayout(right_layout)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([600, 600])

        self.setCentralWidget(splitter)

        # 连接信号
        self.left_tree.internal_drop.connect(self.handle_internal_drop)
        self.right_tree.internal_drop.connect(self.handle_internal_drop)
        self.left_up_btn.clicked.connect(lambda: self.go_up(self.left_tree))
        self.right_up_btn.clicked.connect(lambda: self.go_up(self.right_tree))
        self.left_reset_btn.clicked.connect(lambda: self.reset_view(self.left_tree))
        self.right_reset_btn.clicked.connect(lambda: self.reset_view(self.right_tree))

        # 设置初始路径
        self.reset_view(self.left_tree)
        self.reset_view(self.right_tree)

        logging.basicConfig(level=logging.INFO)
        logging.info("MainWindow initialized and signals connected.")

    def go_up(self, tree_view):
        """导航到当前目录的上一级"""
        current_path = tree_view.get_root_path()
        if current_path:
            parent_path = os.path.dirname(current_path)
            if parent_path and os.path.exists(parent_path):
                tree_view.set_root_path(parent_path)

    def reset_view(self, tree_view):
        """重置视图到初始目录"""
        tree_view.set_root_path(os.path.expanduser("~"))

    @pyqtSlot(str, str)
    def handle_internal_drop(self, source_path, target_path):
        """处理内部拖放事件，创建符号链接。"""
        logging.info(f"Handling drop from '{source_path}' to '{target_path}'")

        source_name = os.path.basename(source_path)
        reply = QMessageBox.question(
            self,
            "Confirm Action",
            f"Are you sure you want to create a symbolic link?\n\n"
            f"Source:\n{source_path}\n\n"
            f"Target Folder:\n{target_path}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.No:
            logging.info("User cancelled the operation.")
            return

        success, message = create_symlink(source_path, target_path)

        if success:
            QMessageBox.information(self, "Success", message)

            left_root = self.left_tree.get_root_path()
            right_root = self.right_tree.get_root_path()

            # 只有当root路径有效时才检查和刷新
            if left_root and os.path.normcase(
                os.path.commonpath([target_path, left_root])
            ) == os.path.normcase(left_root):
                self.left_tree.refresh()

            if right_root and os.path.normcase(
                os.path.commonpath([target_path, right_root])
            ) == os.path.normcase(right_root):
                self.right_tree.refresh()
        else:
            QMessageBox.critical(self, "Error", message)
