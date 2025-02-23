.PHONY: css clear build all

css:
	pnpm run css

clear:
	python scripts/build.py clear

build:
	python scripts/build.py build

lint:
	black scripts/build.py --line-length 120 --target-version py38 
all: build css