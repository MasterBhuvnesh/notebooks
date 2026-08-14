# Thin wrapper over tools/build.py -- the script is the build, this is shorthand.
PY ?= python

.PHONY: all doc new clean force

all:
	$(PY) tools/build.py $(DOC)

force:
	$(PY) tools/build.py --force $(DOC)

new:
	@test -n "$(SLUG)" || (echo "usage: make new SLUG=2026-thing" && exit 1)
	$(PY) tools/build.py --new $(SLUG)

clean:
	find docs -type f \( -name '*.aux' -o -name '*.log' -o -name '*.toc' -o -name '*.out' \) -delete
