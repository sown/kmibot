.PHONY: all clean lint lint-fix type

CMD:=poetry run
PYMODULE:=kmibot

all: type lint

lint:
	$(CMD) ruff $(PYMODULE)

lint-fix:
	$(CMD) ruff --fix $(PYMODULE)

type:
	$(CMD) mypy $(PYMODULE)

clean:
	git clean -Xdf # Delete all files in .gitignore