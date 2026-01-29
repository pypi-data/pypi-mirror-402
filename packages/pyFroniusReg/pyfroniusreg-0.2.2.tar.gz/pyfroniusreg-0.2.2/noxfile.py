import nox
import os


@nox.session
def lint(session):
    session.install("ruff")
    session.run("ruff", "check", "--exclude", "examples", "--exclude", "tools")
    session.run("ruff", "check", "--extend-select", "N", "src/pyfroniusreg/froniusreg.py")


@nox.session
def build_and_check_dists(session):
    session.install("build", "check-manifest >= 0.42", "twine")
    session.run("check-manifest", "--ignore", "noxfile.py,tests/**,examples/**,src/pyfronius/*")
    session.run("python", "-m", "build")
    session.run("python", "-m", "twine", "check", "dist/*")


@nox.session
def build(session):
    lint(session)
    build_and_check_dists(session)


@nox.session
def tests(session):
    session.install("pytest")
    build_and_check_dists(session)

    generated_files = os.listdir("dist/")
    generated_sdist = os.path.join("dist/", generated_files[1])

    session.install(generated_sdist)

    session.run("pytest")
