from rich.console import Console

console = Console(highlight=False)


class SolverLog:
    def __init__(self):
        self.log: str = ""
        self.add_newline = False
        self._header_printed = False
        self._titles_to_print = ["User Parameters", "Model Summary", "Solve", "Solver Results"]

    def next_time_add_new_line(self) -> None:
        self.add_newline = True

    def update_log(self, new_log: str) -> None:
        """Updates the log.

        Takes as input the updated log. It will make sure that the old log is contained in the new log, and print the
        difference to the screen
        """
        if new_log == "":
            return

        old_log_len = len(self.log)

        if self.log != new_log[:old_log_len]:
            msg = "There was some suspicious discrepancy in the solver log received from the server. "
            msg += "The solver log might not be printed in the order as the solver generated it."
            console_string_print(msg, style="warning")

        if len(new_log) != old_log_len and self.add_newline:
            console_string_print("")
            self.add_newline = False

        new_log_list = new_log[old_log_len:].split("\n")
        for linnum, line in enumerate(new_log_list, 1):
            # if no next line exists, we don't want to print a new line character
            end = ""
            if linnum < len(new_log_list):
                end = "\n"
            if not self._header_printed:
                header = "Quantagonia HybridSolver"
                if header in line:
                    styled_line = line.replace(
                        "Quantagonia HybridSolver", "[bold green]Quantagonia HybridSolver[/bold green]"
                    )
                    console_string_print(styled_line, end=end)
                    self._header_printed = True
                    continue
            if line.strip() in self._titles_to_print:
                console_string_print(line, style="title", end=end)
                self._titles_to_print.remove(line.strip())
                continue
            # all other lines are printed unprocessed
            console_string_print(line, end=end)
        self.log = new_log


def console_string_print(msg: str, style: str = "default", end: str = "\n") -> None:
    if style == "warning":
        msg = "[yellow]Warning:[/yellow] " + msg
    if style == "title":
        msg = "[bold]" + msg + "[/bold]"
    console.print(msg, end=end)
