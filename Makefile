.PHONY: css clear build all

css:
	pnpm run css

clear:
	python pen.py clear

build:
	python pen.py build

lint:
	black pen.py --line-length 120 --target-version py38
	
all: build css