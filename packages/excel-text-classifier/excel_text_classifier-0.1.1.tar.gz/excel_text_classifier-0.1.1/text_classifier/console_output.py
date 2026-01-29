from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any, Iterator, Optional

import typer


class ConsoleOutput:
    """统一封装控制台输出与 rich 降级逻辑。

    - 若 rich 可用：使用彩色输出、表格、进度条等能力
    - 若 rich 不可用：使用 typer.echo 作为降级方案
    """

    def __init__(self) -> None:
        self._has_rich = False
        self._console = None
        self._Table = None
        self._Progress = None

        try:  # 动态加载 rich，避免强依赖
            from rich.console import Console  # type: ignore
            from rich.table import Table  # type: ignore
            from rich.progress import Progress  # type: ignore

            self._console = Console()
            self._Table = Table
            self._Progress = Progress
            self._has_rich = True
        except Exception:  # pragma: no cover
            self._has_rich = False

    # 属性暴露
    @property
    def has_rich(self) -> bool:
        return self._has_rich

    # 基本输出方法
    def info(self, message: str) -> None:
        logging.info(message)
        if self._has_rich and self._console is not None:
            self._console.print(f"[bold green]{message}[/bold green]")
        else:
            typer.echo(message)

    def warning(self, message: str) -> None:
        logging.warning(message)
        if self._has_rich and self._console is not None:
            self._console.print(f"[bold yellow]{message}[/bold yellow]")
        else:
            typer.echo(message)

    def error(self, message: str) -> None:
        logging.error(message)
        if self._has_rich and self._console is not None:
            self._console.print(f"[bold red]{message}[/bold red]")
        else:
            typer.echo(message, err=True)

    def plain(self, message: str) -> None:
        """不做颜色处理的普通输出，但仍记录日志。"""
        logging.info(message)
        if self._has_rich and self._console is not None:
            self._console.print(message)
        else:
            typer.echo(message)

    # 统计表格输出
    def stats_table(self, *, total: int, classified: int, unclassified: int) -> None:
        """输出统计信息，rich 时使用表格，否则使用多行文本。"""
        classified_ratio = (classified / total * 100) if total else 0.0
        unclassified_ratio = 100 - classified_ratio if total else 0.0

        logging.info(
            "统计: total=%s, classified=%s(%.2f%%), unclassified=%s(%.2f%%)",
            total,
            classified,
            classified_ratio,
            unclassified,
            unclassified_ratio,
        )

        if self._has_rich and self._console is not None and self._Table is not None:
            table = self._Table(title="分类统计")
            table.add_column("指标", style="cyan", justify="left")
            table.add_column("数值", style="magenta", justify="right")

            table.add_row("总行数", str(total))
            table.add_row("已分类", f"{classified} ({classified_ratio:.2f}%)")
            table.add_row("未分类", f"{unclassified} ({unclassified_ratio:.2f}%)")

            self._console.print(table)
        else:
            msg = (
                f"总行数: {total}\n"
                f"已分类: {classified} ({classified_ratio:.2f}%)\n"
                f"未分类: {unclassified} ({unclassified_ratio:.2f}%)"
            )
            typer.echo(msg)

    # 进度条上下文管理器
    @contextmanager
    def progress(self, total: int) -> Iterator[Optional[Any]]:
        """返回一个可用于更新进度的对象。

        使用方式：

        with console.progress(total=total) as progress:
            if progress is not None:
                task_id = progress.add_task("分类中...", total=total)
                # 在每条记录处理完成后调用 progress.advance(task_id)
        """
        if self._has_rich and self._Progress is not None and self._console is not None and total > 0:
            from rich.live import Live  # type: ignore

            progress = self._Progress()
            task_id = progress.add_task("分类中...", total=total)

            with Live(progress, console=self._console):  # pragma: no cover - 视图渲染
                yield (progress, task_id)
        else:
            # 降级时不提供进度，仅保留接口
            yield None
