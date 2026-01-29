class SolverError(Exception):
    def __init__(self, message: str = "Unexpected solver error"):
        self.message = message
        super().__init__(self.message)


class AssignmentError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ModelError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
