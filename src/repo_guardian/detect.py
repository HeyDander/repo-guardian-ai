from pathlib import Path
from .repository import Repository


def detect(repo: Repository) -> list[str]:
    files = [p for p in repo.files() if not any(part in {"tests", "fixtures"} for part in p.relative_to(repo.root).parts)]
    names = {p.name for p in files}
    suffixes = {p.suffix for p in files}
    result: list[str] = []
    if "package.json" in names:
        result += ["JavaScript", "Node.js"]
        package = repo.read(repo.root / "package.json")
        if '"typescript"' in package or ".ts" in " ".join(str(p) for p in files): result.append("TypeScript")
        if '"next"' in package: result.append("Next.js")
        if '"react"' in package: result.append("React")
        if '"vue"' in package: result.append("Vue")
    if suffixes & {".py"} or "pyproject.toml" in names or "requirements.txt" in names: result.append("Python")
    if any("fastapi" in repo.read(p).lower() for p in files if p.name in {"requirements.txt", "pyproject.toml"}): result.append("FastAPI")
    if "django" in repo.read(repo.root / "requirements.txt").lower() if repo.exists("requirements.txt") else False: result.append("Django")
    if ".go" in suffixes or "go.mod" in names: result.append("Go")
    if ".rs" in suffixes or "Cargo.toml" in names: result.append("Rust")
    if suffixes & {".java", ".kt"} or names & {"pom.xml", "build.gradle", "build.gradle.kts"}: result.append("Java/Kotlin")
    if ".php" in suffixes or "composer.json" in names: result.append("PHP")
    if ".rb" in suffixes or "Gemfile" in names: result.append("Ruby")
    if suffixes & {".cs"} or ".sln" in " ".join(names): result.append("C#/.NET")
    if suffixes & {".c", ".h", ".cpp", ".cc"} or "CMakeLists.txt" in names: result.append("C/C++")
    if "Dockerfile" in names or any(p.name.startswith("docker-compose") for p in files): result.append("Docker")
    if any(p.suffix in {".tf"} for p in files): result.append("Terraform")
    return list(dict.fromkeys(result))
