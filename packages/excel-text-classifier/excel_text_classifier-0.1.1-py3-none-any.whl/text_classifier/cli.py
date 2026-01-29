from __future__ import annotations

from typing import Optional

import logging
import typer

from .classifier import classify_excel, classify_series
from .config_loader import load_rules
from .console_output import ConsoleOutput
from .io_excel import read_excel, write_excel_with_column

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

console = ConsoleOutput()

app = typer.Typer(help="Excel 多标签文本分类工具（支持 JSON/YAML/Excel 规则配置）")


@app.command()
def main(
    input_file: str = typer.Option(..., "--input-file", "-i", help="输入 Excel 文件路径"),
    text_column: str = typer.Option(..., "--text-column", "-t", help="文本列名"),
    config_file: str = typer.Option(..., "--config", "-c", help="规则配置文件路径（JSON/YAML/Excel）"),
    sheet_name: Optional[str] = typer.Option(None, "--sheet-name", help="工作表名称（默认第一个）"),
    output_file: Optional[str] = typer.Option(None, "--output-file", "-o", help="输出 Excel 文件路径"),
    output_column: str = typer.Option("classification_tags", "--output-column", help="输出标签列名"),
    config_format: Optional[str] = typer.Option(
        None, "--config-format", help="配置格式: json / yaml / excel（缺省根据扩展名自动推断）"
    ),
    case_sensitive: bool = typer.Option(False, "--case-sensitive", help="是否大小写敏感匹配"),
    dry_run: bool = typer.Option(False, "--dry-run", help="只统计分类结果，不写回 Excel 文件"),
) -> None:
    """命令行入口：对 Excel 文件中的文本列进行多标签分类。"""
    try:
        logging.info(
            "CLI 调用: input_file=%s, text_column=%s, config_file=%s, sheet_name=%s, output_file=%s",
            input_file,
            text_column,
            config_file,
            sheet_name,
            output_file,
        )

        if dry_run:
            # 只做统计，不写回文件
            df = read_excel(input_file, sheet_name=sheet_name)
            if text_column not in df.columns:
                available = ", ".join(map(str, df.columns))
                raise KeyError(f"文本列 '{text_column}' 不存在，可用列名: {available}")

            rules = load_rules(config_file, config_format=config_format)
            labels = classify_series(df[text_column], rules, case_sensitive=case_sensitive)

            total = len(df)
            classified = int((labels != "").sum())
            unclassified = total - classified

            console.stats_table(total=total, classified=classified, unclassified=unclassified)
        else:
            console.info("开始分类...")

            if not console.has_rich:
                # 无 rich 时不显示进度条，直接调用 classify_excel
                out_path = classify_excel(
                    input_file=input_file,
                    config_file=config_file,
                    text_column=text_column,
                    sheet_name=sheet_name,
                    output_file=output_file,
                    output_column=output_column,
                    config_format=config_format,
                    case_sensitive=case_sensitive,
                )
                console.info(f"分类完成，输出文件: {out_path}")
                return

            # 使用 rich 进度条显示进度
            df = read_excel(input_file, sheet_name=sheet_name)
            if text_column not in df.columns:
                available = ", ".join(map(str, df.columns))
                raise KeyError(f"文本列 '{text_column}' 不存在，可用列名: {available}")

            rules = load_rules(config_file, config_format=config_format)

            total = len(df)

            def progress_callback(done: int, _total: int) -> None:
                if progress_state[0] is not None:
                    progress, task_id = progress_state[0]
                    progress.advance(task_id)

            progress_state: list = [None]

            with console.progress(total=total) as progress:
                if progress is not None:
                    progress_state[0] = progress

                labels = classify_series(
                    df[text_column],
                    rules,
                    case_sensitive=case_sensitive,
                    progress_callback=progress_callback,
                )

            df[output_column] = labels

            # 生成输出路径（与 classify_excel 保持一致逻辑）
            import os

            if output_file is None:
                base, ext = os.path.splitext(input_file)
                if not ext:
                    ext = ".xlsx"
                out_path = f"{base}_classified{ext}"
            else:
                out_path = output_file

            write_excel_with_column(df, out_path)

            console.info(f"分类完成，输出文件: {out_path}")

    except Exception as exc:
        console.error(f"错误: {exc}")
        raise typer.Exit(code=1)
