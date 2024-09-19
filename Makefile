#!/usr/bin/make -f

# Portions of this file contributed by NIST are governed by the
# following statement:
#
# This software was developed at the National Institute of Standards
# and Technology by employees of the Federal Government in the course
# of their official duties. Pursuant to title 17 Section 105 of the
# United States Code this software is not subject to copyright
# protection and is in the public domain. NIST assumes no
# responsibility whatsoever for its use by other parties, and makes
# no guarantees, expressed or implied, about its quality,
# reliability, or any other characteristic.
#
# We would appreciate acknowledgement if the software is used.

SHELL := /bin/bash

PYTHON3 ?= python3

py_srcfiles := \
  src/facet_cardinalities_ttl.py \
  src/generate_single_stub_json.py

all: \
  .venv-pre-commit/var/.pre-commit-built.log \
  all-tests

.PHONY: \
  all-tests \
  all-var \
  check-pytest \
  check-supply-chain \
  check-supply-chain-pre-commit

.mypy.done.log: \
  $(py_srcfiles) \
  .venv.done.log
	source venv/bin/activate \
	  && mypy \
	    --strict \
	    $(py_srcfiles)
	touch $@

.venv.done.log: \
  requirements.txt
	rm -rf venv
	$(PYTHON3) -m venv \
	  venv
	source venv/bin/activate \
	  && pip install \
	    --upgrade \
	    pip
	source venv/bin/activate \
	  && pip install \
	    --requirement requirements.txt
	touch $@

# This virtual environment is meant to be built once and then persist, even through 'make clean'.
# If a recipe is written to remove this flag file, it should first run `pre-commit uninstall`.
.venv-pre-commit/var/.pre-commit-built.log:
	rm -rf .venv-pre-commit
	test -r .pre-commit-config.yaml \
	  || (echo "ERROR:Makefile:pre-commit is expected to install for this repository, but .pre-commit-config.yaml does not seem to exist." >&2 ; exit 1)
	$(PYTHON3) -m venv \
	  .venv-pre-commit
	source .venv-pre-commit/bin/activate \
	  && pip install \
	    --upgrade \
	    pip \
	    setuptools \
	    wheel
	source .venv-pre-commit/bin/activate \
	  && pip install \
	    pre-commit
	source .venv-pre-commit/bin/activate \
	  && pre-commit install
	mkdir -p \
	  .venv-pre-commit/var
	touch $@

all-tests: \
  all-var
	$(MAKE) \
	  --directory tests

all-var: \
  .mypy.done.log
	$(MAKE) \
	  --directory var

check: \
  .venv-pre-commit/var/.pre-commit-built.log \
  check-pytest \
  all-tests

check-pytest: \
  .venv.done.log
	source venv/bin/activate \
	  && pytest \
	    --doctest-modules \
	    --log-level=DEBUG \
	    $(py_srcfiles)

check-supply-chain: \
  check-supply-chain-pre-commit \
  .mypy.done.log

# Update pre-commit configuration and use the updated config file to
# review code.  Only have Make exit if 'pre-commit run' modifies files.
check-supply-chain-pre-commit: \
  .venv-pre-commit/var/.pre-commit-built.log
	source .venv-pre-commit/bin/activate \
	  && pre-commit autoupdate
	git diff \
	  --exit-code \
	  .pre-commit-config.yaml \
	  || ( \
	      source .venv-pre-commit/bin/activate \
	        && pre-commit run \
	          --all-files \
	          --config .pre-commit-config.yaml \
	    ) \
	    || git diff \
	      --stat \
	      --exit-code \
	      || ( \
	          echo \
	            "WARNING:Makefile:pre-commit configuration can be updated.  It appears the updated would change file formatting." \
	            >&2 \
	            ; exit 1 \
                )
	@git diff \
	  --exit-code \
	  .pre-commit-config.yaml \
	  || echo \
	    "INFO:Makefile:pre-commit configuration can be updated.  It appears the update would not change file formatting." \
	    >&2

clean:
	@$(MAKE) \
	  --directory tests \
	  clean
	@$(MAKE) \
	  --directory var \
	  clean
	@rm -f \
	  .venv.done.log
	@rm -rf \
	  venv
