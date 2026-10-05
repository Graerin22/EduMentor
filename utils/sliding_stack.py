from PyQt6.QtWidgets import QStackedWidget
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QPoint, QParallelAnimationGroup

class SlidingStackedWidget(QStackedWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.animation_group = QParallelAnimationGroup()

    def slide_to_index(self, target_index):
        if self.currentIndex() == target_index or target_index < 0 or target_index >= self.count():
            return

        is_next = target_index > self.currentIndex()
        current_widget = self.currentWidget()
        next_widget = self.widget(target_index)
        width = self.width()
        
        start_pos_next = QPoint(width, 0) if is_next else QPoint(-width, 0)
        end_pos_current = QPoint(-width, 0) if is_next else QPoint(width, 0)

        next_widget.setGeometry(0, 0, self.width(), self.height())
        next_widget.move(start_pos_next)
        next_widget.show()
        next_widget.raise_()

        self.animation_group.clear()

        anim_current = QPropertyAnimation(current_widget, b"pos")
        anim_current.setDuration(400)
        anim_current.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim_current.setStartValue(QPoint(0, 0))
        anim_current.setEndValue(end_pos_current)
        self.animation_group.addAnimation(anim_current)

        anim_next = QPropertyAnimation(next_widget, b"pos")
        anim_next.setDuration(400)
        anim_next.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim_next.setStartValue(start_pos_next)
        anim_next.setEndValue(QPoint(0, 0))
        self.animation_group.addAnimation(anim_next)

        self.animation_group.finished.connect(lambda: self.setCurrentIndex(target_index))
        self.animation_group.start()
