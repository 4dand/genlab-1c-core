"""
AI-1C-Code-Generation-Benchmark CLI
Универсальный entry point для всех операций фреймворка.

Примеры:
    # Запуск эксперимента
    python main.py run -c A -m gemini -t A1
    python main.py run -c B --all-models
    
    # Информация
    python main.py info --balance
    python main.py info --models
    python main.py info --tasks A
"""

import asyncio
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from src.config import setup_logging
from src.cli import cmd_run, cmd_info, cmd_evaluate, cmd_report, cmd_stats, cmd_charts

setup_logging()


def main():
    parser = argparse.ArgumentParser(
        description="AI-1C-Code-Generation-Benchmark CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  %(prog)s run -c A -m gemini -t A1      # Запуск одной задачи
  %(prog)s run -c A --all-models         # Запуск всех моделей
  %(prog)s info --balance                # Проверка баланса OpenRouter
  %(prog)s info --models                 # Список доступных моделей
  %(prog)s info --tasks A                # Список задач категории
  %(prog)s evaluate experiment_B_123     # Оценка эксперимента
  %(prog)s evaluate --list               # Список экспериментов
  %(prog)s report experiment_B_123       # Генерация отчёта
        """
    )
    subparsers = parser.add_subparsers(dest="command", help="Команды")
    
    # run
    run_parser = subparsers.add_parser("run", help="Запустить эксперимент")
    run_parser.add_argument("-c", "--category", choices=["A", "B"], default="A",
                           help="Категория задач (по умолчанию: A)")
    run_parser.add_argument("-m", "--models", nargs="+", choices=["claude", "gpt", "gemini"],
                           help="Модели для тестирования")
    run_parser.add_argument("--all-models", action="store_true",
                           help="Тестировать все доступные модели")
    run_parser.add_argument("-t", "--tasks", nargs="+",
                           help="ID задач (например: A1 A2)")
    run_parser.add_argument("--no-mock", action="store_true",
                           help="Использовать реальный MCP сервер (категория B)")
    
    # info
    info_parser = subparsers.add_parser("info", help="Показать информацию")
    info_parser.add_argument("--balance", action="store_true",
                            help="Показать баланс OpenRouter")
    info_parser.add_argument("--models", action="store_true",
                            help="Список доступных моделей")
    info_parser.add_argument("--tasks", metavar="CATEGORY",
                            help="Список задач категории (A или B)")
    
    # evaluate
    evaluate_parser = subparsers.add_parser("evaluate", help="Оценка эксперимента SMOP")
    evaluate_parser.add_argument("experiment_id", nargs="?",
                                help="ID эксперимента для оценки")
    evaluate_parser.add_argument("--list", action="store_true",
                                help="Показать список доступных экспериментов")
    evaluate_parser.add_argument("--status", metavar="EXPERIMENT_ID",
                                help="Показать прогресс оценки эксперимента")
    evaluate_parser.add_argument("--evaluator", default="expert_01",
                                help="ID эксперта (по умолчанию: expert_01)")
    
    # report
    report_parser = subparsers.add_parser("report", help="Генерация отчёта")
    report_parser.add_argument("experiment_id",
                              help="ID эксперимента")
    report_parser.add_argument("--format", choices=["json", "html", "latex", "all"],
                              default="all",
                              help="Формат отчёта (по умолчанию: all)")
    report_parser.add_argument("--compare", metavar="EXPERIMENT_ID",
                              help="ID второго эксперимента для сравнения")
    
    # stats
    stats_parser = subparsers.add_parser("stats", help="Показать статистику")
    stats_parser.add_argument("experiment_id",
                             help="ID эксперимента")
    
    # charts
    charts_parser = subparsers.add_parser("charts", help="Генерация графиков")
    charts_parser.add_argument("experiment_id",
                              help="ID эксперимента")
    charts_parser.add_argument("--chart", 
                              choices=["all", "dashboard", "radar", "comparison", 
                                      "q_by_model", "distribution", "boxplot", 
                                      "heatmap", "det_quality"],
                              default="all",
                              help="Тип графика (по умолчанию: all)")
    charts_parser.add_argument("--format", nargs="+",
                              choices=["png", "svg", "pdf", "all"],
                              default=["all"],
                              help="Формат экспорта (по умолчанию: all)")
    
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return
    
    handlers = {
        "run": lambda: asyncio.run(cmd_run(args)),
        "info": lambda: cmd_info(args),
        "evaluate": lambda: cmd_evaluate(args),
        "report": lambda: cmd_report(args),
        "stats": lambda: cmd_stats(args),
        "charts": lambda: cmd_charts(args),
    }
    handlers[args.command]()


if __name__ == "__main__":
    main()
