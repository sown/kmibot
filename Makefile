.PHONY: all clean format format-check lint lint-fix type

CMD:=poetry run
PYMODULE:=kmibot

all: type format lint

format:
	$(CMD) ruff format $(PYMODULE)

format-check:
	$(CMD) ruff format --check $(PYMODULE)

lint:
	$(CMD) ruff $(PYMODULE)

lint-fix:
	$(CMD) ruff --fix $(PYMODULE)

type:
	$(CMD) mypy $(PYMODULE)

clean:
	git clean -Xdf # Delete all files in .gitignore