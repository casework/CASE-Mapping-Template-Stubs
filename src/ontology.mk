#!/usr/bin/make -f

# Portions of this file contributed by NIST are governed by the
# following statement:
#
# This software was developed at the National Institute of Standards
# and Technology by employees of the Federal Government in the course
# of their official duties. Pursuant to Title 17 Section 105 of the
# United States Code, this software is not subject to copyright
# protection within the United States. NIST assumes no responsibility
# whatsoever for its use by other parties, and makes no guarantees,
# expressed or implied, about its quality, reliability, or any other
# characteristic.
#
# We would appreciate acknowledgement if the software is used.

# Usage:
# This Makefile is expected to be used with a Make include directive,
# with the variable prefix_iri defined.  This variable should end with
# the delimiting character, typically '/' in CDO.

# E.g., https://ontology.unifiedcyberontology.org/uco/core/
PREFIX_IRI ?=
ifeq ($(PREFIX_IRI),)
$(error PREFIX_IRI must be given.)
endif

SHELL := /bin/bash

top_srcdir := ../..

all: \
  all-classes.mk
	$(MAKE) \
	  --file all-classes.mk

all-classes.mk: \
  $(top_srcdir)/.venv.done.log \
  $(top_srcdir)/src/generate_all_classes_mk.py
	source $(top_srcdir)/venv/bin/activate \
	  && python3 $(top_srcdir)/src/generate_all_classes_mk.py \
	    _$@ \
	    $(PREFIX_IRI)
	mv _$@ $@

check: \
  all

clean:
	@rm -f \
	  *.json \
	  all-classes.mk
