"""Qt 安全工具模块 - 解决对象生命周期问题

PySide6/Qt 与 Python 的内存管理机制不同，容易导致以下问题：
1. QTimer.singleShot + lambda 捕获 Qt 对象引用，对象销毁后访问导致 SIGSEGV
2. Python GC 在后台线程销毁 Qt 对象导致崩溃
3. Qt 父子对象销毁顺序问题

本模块提供安全的延迟操作工具，使用 weakref 避免这些问题。
"""
import weakref
from typing import Any, Callable, Optional
from PySide6.QtCore import QTimer


class SafeTimer:
    """安全的延迟操作工具类

    所有方法都使用 weakref 保护对象引用，避免访问已销毁的 Qt 对象。
    """

    @staticmethod
    def call_method(obj: Any, method_name: str, delay: int = 0, *args, **kwargs) -> None:
        """安全地延迟调用对象方法

        Args:
            obj: 目标对象
            method_name: 方法名
            delay: 延迟时间（毫秒）
            *args: 方法参数
            **kwargs: 方法关键字参数

        Example:
            SafeTimer.call_method(self, '_scroll_to_bottom', 100)
        """
        weak_obj = weakref.ref(obj)

        def action():
            o = weak_obj()
            if o is not None:
                try:
                    getattr(o, method_name)(*args, **kwargs)
                except (RuntimeError, AttributeError):
                    pass  # 对象已销毁或方法不存在

        QTimer.singleShot(delay, action)

    @staticmethod
    def set_text(widget: Any, text: str, delay: int = 1000) -> None:
        """安全地延迟设置文本

        Args:
            widget: 目标控件（需要有 setText 方法）
            text: 要设置的文本
            delay: 延迟时间（毫秒），默认1秒

        Example:
            button.setText("✓")
            SafeTimer.set_text(button, "📋")  # 1秒后恢复
        """
        weak_widget = weakref.ref(widget)

        def action():
            w = weak_widget()
            if w is not None:
                try:
                    w.setText(text)
                except RuntimeError:
                    pass  # 对象已销毁

        QTimer.singleShot(delay, action)

    @staticmethod
    def call_with_refs(delay: int, callback: Callable, *refs: Any) -> None:
        """安全地延迟调用，自动保护所有引用

        Args:
            delay: 延迟时间（毫秒）
            callback: 回调函数，参数为解析后的引用
            *refs: 需要保护的对象引用

        Example:
            SafeTimer.call_with_refs(
                50,
                lambda container, scrollbar: (
                    container.updateGeometry(),
                    scrollbar.setValue(scrollbar.maximum())
                ),
                self.container,
                self.scrollbar
            )
        """
        weak_refs = [weakref.ref(r) for r in refs]

        def action():
            resolved = [wr() for wr in weak_refs]
            if all(r is not None for r in resolved):
                try:
                    callback(*resolved)
                except RuntimeError:
                    pass  # 对象已销毁

        QTimer.singleShot(delay, action)

    @staticmethod
    def delayed_action(delay: int, callback: Callable, guard_obj: Optional[Any] = None) -> None:
        """安全地延迟执行回调

        Args:
            delay: 延迟时间（毫秒）
            callback: 回调函数（无参数）
            guard_obj: 守护对象，如果提供则在对象销毁后不执行回调

        Example:
            SafeTimer.delayed_action(100, lambda: print("done"), self)
        """
        if guard_obj is not None:
            weak_guard = weakref.ref(guard_obj)

            def guarded_action():
                if weak_guard() is not None:
                    try:
                        callback()
                    except RuntimeError:
                        pass

            QTimer.singleShot(delay, guarded_action)
        else:
            def action():
                try:
                    callback()
                except RuntimeError:
                    pass

            QTimer.singleShot(delay, action)
