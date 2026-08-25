from .analyzers import run, score
from .detect import detect
from .models import AuditResult
from .repository import Repository


CATEGORIES = ["Architecture", "Security", "Testing", "Dependencies", "Documentation", "Performance", "Code Quality", "Release Readiness"]


def audit(root: str, mode: str = "full") -> AuditResult:
    repo = Repository(root)
    findings = run(repo, mode)
    state = repo.git_state()
    commands = repo.project_commands()
    return AuditResult(str(repo.root), detect(repo), [score(c, findings) for c in CATEGORIES], findings,
                       [{"command": "git branch --show-current", "result": state["branch"]},
                        {"command": "git log -1 --oneline", "result": state["last_commit"]},
                        {"command": "project commands (discovered, not run)", "result": commands}])
