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
# with the variable PREFIX_IRI defined.  The file running the include
# follows a Makefile templating pattern similar to a late step in the
# Automake framework.
#
# The Makefile template is expected to be called from a 3rd-level
# directory corresponding with an ontology concept.  E.g., for this IRI:
#
# https://ontology.unifiedcyberontology.org/uco/core/UcoObject
#
# This directory would receive a copy of this file, renamed to
# `Makefile`, and adapted to populate the variable-value PREFIX_IRI.
#
# /templates/uco-core/UcoObject/
#
# This file then delegates the remaining Make scripting to the file
# `/src/class.mk`.
#
# This pattern lets a user descend to any directory level under
# `/templates` and run `make` in their current directory, enabling
# focused rebuilds.

SHELL := /bin/bash

# E.g., UcoObject, corresponding with:
# https://ontology.unifiedcyberontology.org/uco/core/UcoObject
LOCAL_NAME ?= $(shell basename $$PWD)

# This variable should end with the delimiting character, typically '/'
# in CDO.
# E.g., https://ontology.unifiedcyberontology.org/uco/core/
PREFIX_IRI ?=
ifeq ($(PREFIX_IRI),)
$(error PREFIX_IRI must be given.)
endif

ifeq ($(top_srcdir),)
$(error top_srcdir must be given.)
endif

all: \
  $(LOCAL_NAME).svg \
  $(LOCAL_NAME).json

%.svg: \
  %.dot
	dot \
	  -T svg \
	  -o _$@ \
	  $<
	mv _$@ $@

$(LOCAL_NAME).dot: \
  $(top_srcdir)/.venv.done.log \
  $(top_srcdir)/src/generate_single_stub_dot.py \
  $(top_srcdir)/var/facet_cardinalities.ttl
	rm -f _$@
	source $(top_srcdir)/venv/bin/activate \
	  && python3 $(top_srcdir)/src/generate_single_stub_dot.py \
	    _$@ \
	    $(PREFIX_IRI)$(LOCAL_NAME) \
	    $(top_srcdir)/var/facet_cardinalities.ttl
	mv _$@ $@

$(LOCAL_NAME).json: \
  $(top_srcdir)/.venv.done.log \
  $(top_srcdir)/src/generate_single_stub_json.py \
  $(top_srcdir)/var/facet_cardinalities.ttl
	rm -f _$@
	source $(top_srcdir)/venv/bin/activate \
	  && python3 $(top_srcdir)/src/generate_single_stub_json.py \
	    _$@ \
	    $(PREFIX_IRI)$(LOCAL_NAME) \
	    $(top_srcdir)/var/facet_cardinalities.ttl
	mv _$@ $@

check: \
  all

clean:
	@rm -f \
	  *.dot \
	  *.json \
	  *.svg
