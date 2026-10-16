class ComparisonResults:
    def __init__(self, return_diff: bool, performance_diff: bool, mutation_diff: bool) -> None:
        self.return_diff = return_diff
        self.performance_diff = performance_diff
        self.mutation_diff = mutation_diff

    def __str__(self) -> str:
        return f"ComparisonResults(return_diff={self.return_diff}, performance_diff={self.performance_diff}, mutation_diff={self.mutation_diff})"