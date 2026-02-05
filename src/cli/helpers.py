"""Общие helper-ы для CLI команд"""

from typing import Optional, Tuple

from src.config.settings import get_settings, Settings
from src.core.benchmark import BenchmarkRunner
from src.evaluator import ExperimentParser, SMOPEvaluator, ExperimentEvaluation
from src.schemas.results import ExperimentResult


def get_runner() -> BenchmarkRunner:
    """Создать BenchmarkRunner (использует настройки из Settings)"""
    return BenchmarkRunner()


def load_experiment_with_eval(
    experiment_id: str,
    settings: Optional[Settings] = None,
) -> Tuple[Optional[ExperimentResult], Optional[ExperimentEvaluation]]:
    """
    Загрузить эксперимент и лучшую оценку — общий паттерн для report/stats/charts.
    
    Returns:
        (experiment, evaluation) — любой может быть None если не найден
    """
    if settings is None:
        settings = get_settings()

    parser = ExperimentParser(settings.paths.raw_results_dir)
    evaluator = SMOPEvaluator(settings.paths.evaluations_dir)

    experiment = parser.load_experiment(experiment_id)
    if not experiment:
        return None, None

    evaluations = evaluator.list_evaluations(experiment_id)
    if not evaluations:
        return experiment, None

    best_eval_info = max(evaluations, key=lambda e: e["progress_percent"])
    evaluation = evaluator.load(experiment_id, best_eval_info["evaluator_id"])

    return experiment, evaluation
