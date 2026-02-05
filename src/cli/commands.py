"""Обработчики CLI команд"""

import asyncio
from pathlib import Path

from .formatters import print_section, print_kv
from .helpers import get_runner, load_experiment_with_eval


# ── run ──────────────────────────────────────────────────────────────────────

async def cmd_run(args):
    """Запустить эксперимент"""
    runner = get_runner()
    models = args.models
    if args.all_models:
        models = None
    if args.category == "B":
        await runner.init_mcp(use_mock=not args.no_mock)
    try:
        result = await runner.run_experiment(
            category=args.category,
            model_keys=models,
            task_ids=args.tasks,
        )

        print_section("Итоги")
        print_kv("Задач выполнено", str(len(result.task_results)))
        print_kv("Всего токенов", f"{result.total_tokens:,}")
        print_kv("Общая стоимость", f"${result.total_cost:.4f}")
        print_kv("Общее время", f"{result.total_time:.1f} сек")

        if result.task_results:
            avg_match = sum(
                t.determinism.match_percent
                for t in result.task_results
                if t.determinism
            ) / len(result.task_results)
            print_kv("Детерминизм", f"{avg_match:.1f}% (среднее совпадение ответов)")
        print()
    finally:
        await runner.close_mcp()


# ── info ─────────────────────────────────────────────────────────────────────

def cmd_info(args):
    """Показать информацию"""
    from src.config.settings import get_settings
    from src.utils.file_ops import load_yaml

    settings = get_settings()
    runner = get_runner()

    if args.balance:
        balance = runner.llm.get_balance()
        if balance:
            print_section("Баланс OpenRouter")
            print_kv("Лимит", f"${balance['limit']:.2f}")
            print_kv("Использовано", f"${balance['usage']:.4f}")
            print_kv("Доступно", f"${balance['available']:.4f}")
        else:
            print("Ошибка: не удалось получить баланс")

    if args.models:
        print_section("Доступные модели")
        models_config = load_yaml(settings.paths.get_models_path())
        print(f"  {'Ключ':<10} {'Название':<25} {'Детерминизм':<12} {'Цена (in/out)':<15}")
        print("  " + "-" * 65)
        for key, model in models_config["models"].items():
            meta = model.get("meta", {})
            det = meta.get("determinism_param", "temperature")
            price_in = meta.get("price_input", 0)
            price_out = meta.get("price_output", 0)
            print(f"  {key:<10} {model['name']:<25} {det:<12} ${price_in}/{price_out}")

    if args.tasks:
        category = args.tasks
        print_section(f"Задачи категории {category}")
        tasks_config = load_yaml(settings.paths.get_tasks_path(category))
        print(f"  {'ID':<6} {'Название':<35} {'Сложность':<10}")
        print("  " + "-" * 55)
        for task in tasks_config.get("tasks", []):
            print(f"  {task['id']:<6} {task['name']:<35} {task.get('difficulty', 'medium'):<10}")
    print()


# ── evaluate ─────────────────────────────────────────────────────────────────

def cmd_evaluate(args):
    """Оценка эксперимента SMOP"""
    from src.config.settings import get_settings
    from src.evaluator import run_dashboard, list_experiments_cli, show_status_cli

    settings = get_settings()

    if args.list:
        list_experiments_cli(settings.paths.raw_results_dir)
        return

    if args.status:
        show_status_cli(args.status, settings.paths.evaluations_dir)
        return

    if not args.experiment_id:
        print("Ошибка: укажите ID эксперимента или используйте --list")
        return

    run_dashboard(
        experiment_id=args.experiment_id,
        evaluator_id=args.evaluator,
        results_dir=settings.paths.raw_results_dir,
        evaluations_dir=settings.paths.evaluations_dir,
        reports_dir=settings.paths.reports_dir,
    )


# ── report ───────────────────────────────────────────────────────────────────

def cmd_report(args):
    """Генерация отчёта"""
    from src.config.settings import get_settings
    from src.evaluator import ReportGenerator, generate_report

    settings = get_settings()
    experiment, evaluation = load_experiment_with_eval(args.experiment_id, settings)

    if not experiment:
        print(f"Ошибка: эксперимент не найден: {args.experiment_id}")
        return
    if not evaluation:
        print(f"Ошибка: оценка не найдена. Сначала: evaluate {args.experiment_id}")
        return

    formats = ["json", "html", "latex"] if args.format == "all" else [args.format]

    paths = generate_report(
        evaluation,
        experiment,
        settings.paths.reports_dir,
        formats=formats,
    )

    print_section("Отчёты сгенерированы")
    for fmt, path in paths.items():
        print(f"  {fmt.upper()}: {path}")
    print()

    if args.compare:
        experiment2, evaluation2 = load_experiment_with_eval(args.compare, settings)
        if experiment2 and evaluation2:
            generator = ReportGenerator(settings.paths.reports_dir)
            report1 = generator.generate(evaluation, experiment)
            report2 = generator.generate(evaluation2, experiment2)
            comparison = generator.generate_comparison_report(report1, report2)

            print_section("Сравнительный анализ")
            for metric, data in comparison.get("delta", {}).items():
                diff = data.get("diff", 0)
                sign = "+" if diff > 0 else ""
                print(f"  {metric}: {data.get('exp1', 0):.1f} → {data.get('exp2', 0):.1f} ({sign}{diff:.2f})")
            print()


# ── stats ────────────────────────────────────────────────────────────────────

def cmd_stats(args):
    """Показать статистику эксперимента"""
    from src.evaluator import StatisticsCalculator

    experiment, evaluation = load_experiment_with_eval(args.experiment_id)

    if not evaluation:
        print(f"Оценка для {args.experiment_id} не найдена")
        return

    calc = StatisticsCalculator(evaluation, experiment)
    summary = calc.calculate_summary()

    print_section(f"Статистика: {args.experiment_id}")

    overall_q = summary.get("overall_Q", {})
    print(f"  Интегральный Q: {overall_q.get('mean', 0):.2f} ± {overall_q.get('std', 0):.2f}")
    print(f"  95% ДИ: [{overall_q.get('ci_lower', 0):.2f}, {overall_q.get('ci_upper', 0):.2f}]")
    print()

    print("  Метрики SMOP:")
    for metric in ["S", "M", "O", "P"]:
        data = summary.get("by_metric", {}).get(metric, {})
        print(f"    {metric}: {data.get('mean', 0):.1f} (σ={data.get('std', 0):.2f})")
    print()

    print(f"  Оценено: {summary.get('total_evaluated', 0)}/{summary.get('total_runs', 0)} прогонов")

    det = summary.get("determinism")
    if det:
        print(f"  Детерминизм: {det.get('mean', 0) * 100:.1f}%")

    corr = calc.calculate_correlation_det_quality()
    if corr is not None:
        print(f"  Корреляция детерминизм-качество: {corr:.3f}")
    print()


# ── charts ───────────────────────────────────────────────────────────────────

def cmd_charts(args):
    """Генерация графиков эксперимента"""
    from src.config.settings import get_settings
    from src.evaluator import ChartGenerator, check_matplotlib_available

    if not check_matplotlib_available():
        print("Ошибка: matplotlib не установлен. pip install matplotlib")
        return

    settings = get_settings()
    experiment, evaluation = load_experiment_with_eval(args.experiment_id, settings)

    if not evaluation:
        print(f"Оценка для {args.experiment_id} не найдена")
        return

    formats = args.format if isinstance(args.format, list) else [args.format]
    if "all" in formats:
        formats = ["png", "svg", "pdf"]

    charts_dir = Path(settings.paths.reports_dir) / "charts" / args.experiment_id

    print_section(f"Генерация графиков: {args.experiment_id}")
    print(f"  Форматы: {', '.join(formats)}")
    print(f"  Директория: {charts_dir}")
    print()

    generator = ChartGenerator(evaluation, experiment, str(charts_dir), formats=formats)

    if args.chart == "all":
        results = generator.generate_all()
    else:
        chart_methods = {
            "dashboard": generator.plot_summary_dashboard,
            "radar": generator.plot_smop_radar,
            "comparison": generator.plot_models_comparison,
            "q_by_model": generator.plot_q_by_model,
            "distribution": generator.plot_scores_distribution,
            "boxplot": generator.plot_boxplot_by_model,
            "heatmap": generator.plot_heatmap_tasks_models,
            "det_quality": generator.plot_determinism_vs_quality,
        }
        if args.chart not in chart_methods:
            print(f"Неизвестный тип графика: {args.chart}")
            return
        paths = chart_methods[args.chart]()
        results = {args.chart: paths} if paths else {}

    print_section("Графики созданы")
    for name, paths in results.items():
        print(f"  {name}:")
        for p in paths:
            print(f"    - {p}")
    print()
