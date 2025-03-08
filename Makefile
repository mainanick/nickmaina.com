.PHONY: css clear build all

css:
	pnpm run css

clear:
	python site.py clear

build:
	python site.py build

lint:
	black site.py --line-length 120 --target-version py38
	
all: build css