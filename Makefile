.PHONY: css build all

css:
	pnpm run tailwind

build:
	python scripts/build.py

all: build css