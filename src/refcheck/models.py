class ComparisonResults:
    def __init__(self, return_diff: bool, performance_original: float | None, performance_migrated: float | None, mutation_diff: bool) -> None:
        self.return_diff = return_diff
        self.performance_original = performance_original
        self.performance_migrated = performance_migrated
        self.mutation_diff = mutation_diff

    def __str__(self) -> str:
        return f"ComparisonResults(return_diff={self.return_diff}, performance_original={self.performance_original}, performance_migrated={self.performance_migrated}, mutation_diff={self.mutation_diff})"