import os

from PyQt6.QtCore import QDir, QMimeData, QModelIndex, Qt, pyqtSignal
from PyQt6.QtGui import (
    QDrag,
    QDragEnterEvent,
    QDragMoveEvent,
    QDropEvent,
    QFileSystemModel,
)
from PyQt6.QtWidgets import QTreeView


class FileTreeView(QTreeView):
    """
    一个封装了 QTreeView 和 QFileSystemModel 的可复用文件浏览组件，并实现了拖放功能。
    """

    internal_drop = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._model = QFileSystemModel()
        self._model.setFilter(QDir.Filter.AllEntries | QDir.Filter.NoDotAndDotDot)

        # 设置根路径为空字符串以显示所有驱动盘
        self._model.setRootPath("")
        drives = QDir.drives()

        self.setModel(self._model)

        self.setSortingEnabled(True)
        self.sortByColumn(0, Qt.SortOrder.AscendingOrder)

        for i in range(1, self._model.columnCount()):
            if i != 1 and i != 3:
                self.hideColumn(i)

        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(self.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)

        # 显示所有驱动盘但不展开
        if drives:
            for drive in drives:
                index = self._model.index(drive.path())
                if index.isValid():
                    self.setExpanded(index, False)

    def set_root_path(self, path: str):
        # 处理空路径情况 - 显示所有驱动器
        if path == "":
            self._model.setRootPath("")
            self.setRootIndex(QModelIndex())  # 清除根索引以显示所有驱动器
            return

        # 原有非空路径处理逻辑保持不变
        if not os.path.exists(path):
            return

        # 统一处理文件和文件夹：都导航到父目录并选中项目
        target_dir = path if os.path.isdir(path) else os.path.dirname(path)
        if os.path.isdir(target_dir):
            root_index = self._model.setRootPath(target_dir)
            self.setRootIndex(root_index)
            # 选中并滚动到目标项目
            item_index = self._model.index(path)
            if item_index.isValid():
                self.setCurrentIndex(item_index)
                self.scrollTo(item_index)

    def dragEnterEvent(self, event: QDragEnterEvent | None):
        if event is None:
            return

        mime_data = event.mimeData()
        if mime_data is not None and (mime_data.hasUrls() or mime_data.hasText()):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QDragMoveEvent | None):
        if event is None:
            return

        mime_data = event.mimeData()
        if mime_data is not None and (mime_data.hasUrls() or mime_data.hasText()):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent | None):
        if event is None:
            return

        mime_data = event.mimeData()
        if mime_data is None:
            return

        source_widget = event.source()

        if mime_data.hasUrls():
            first_url = mime_data.urls()[0]
            path = first_url.toLocalFile()
            self.set_root_path(path)
            event.acceptProposedAction()
            return

        if mime_data.hasText():
            source_path = mime_data.text()
            if not source_path:
                return

            target_index = self.indexAt(event.position().toPoint())
            if target_index.isValid():
                target_path = self._model.filePath(target_index)
                if not self._model.isDir(target_index):
                    target_path = os.path.dirname(target_path)
            else:
                target_path = self._model.filePath(self.rootIndex())

            if source_path and target_path:
                self.internal_drop.emit(source_path, target_path)
                event.acceptProposedAction()
            return

        super().dropEvent(event)

    def startDrag(self, supportedActions):
        indexes = self.selectedIndexes()
        if not indexes:
            return

        source_index = indexes[0]
        source_path = self._model.filePath(source_index)

        mime_data = QMimeData()
        mime_data.setText(source_path)

        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.exec(Qt.DropAction.MoveAction)

    def get_root_path(self) -> str:
        """返回当前视图的根路径。"""
        return self._model.filePath(self.rootIndex())

    def refresh(self):
        """刷新视图以显示文件系统的更改。"""
        self._model.setRootPath(self._model.rootPath())
