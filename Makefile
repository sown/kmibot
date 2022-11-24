.PHONY: all clean lint type isort

CMD:=poetry run
PYMODULE:=bot

all: type lint

lint:
	$(CMD) flake8 $(PYMODULE)

type:
	$(CMD) mypy $(PYMODULE)

isort:
	$(CMD) isort $(PYMODULE)

clean:
	git clean -Xdf # Delete all files in .gitignore