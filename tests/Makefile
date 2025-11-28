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

SHELL := /bin/bash

top_srcdir := ..

all: \
  InvestigativeAction.svg \
  ArchiveFile.svg \
  Bag.svg

%.svg: \
  %.dot
	dot \
	  -T svg \
	  -o _$@ \
	  $<
	mv _$@ $@

ArchiveFile.dot: \
  ArchiveFile.json \
  $(top_srcdir)/src/generate_single_stub_dot.py \
  $(top_srcdir)/var/facet_cardinalities.ttl
	rm -f _$@
	source $(top_srcdir)/venv/bin/activate \
	  && python3 $(top_srcdir)/src/generate_single_stub_dot.py \
	    _$@ \
	    http://example.org/kb/ArchiveFile-1 \
	    $(top_srcdir)/var/facet_cardinalities.ttl \
	    ArchiveFile.json
	mv _$@ $@

ArchiveFile.json: \
  $(top_srcdir)/.venv.done.log \
  $(top_srcdir)/src/generate_single_stub_json.py \
  $(top_srcdir)/var/facet_cardinalities.ttl
	rm -f __$@ _$@
	source $(top_srcdir)/venv/bin/activate \
	  && python $(top_srcdir)/src/generate_single_stub_json.py \
	    --debug \
	    __$@ \
	    https://ontology.unifiedcyberontology.org/uco/observable/ArchiveFile \
	    $(top_srcdir)/var/facet_cardinalities.ttl
	python3 -m json.tool \
	  __$@ \
	  _$@
	rm __$@
	mv _$@ $@

Bag.dot: \
  Bag.json \
  $(top_srcdir)/src/generate_single_stub_dot.py \
  $(top_srcdir)/var/facet_cardinalities.ttl
	rm -f _$@
	source $(top_srcdir)/venv/bin/activate \
	  && python3 $(top_srcdir)/src/generate_single_stub_dot.py \
	    _$@ \
	    http://example.org/kb/Bag-1 \
	    $(top_srcdir)/var/facet_cardinalities.ttl \
	    Bag.json
	mv _$@ $@

Bag.json: \
  $(top_srcdir)/.venv.done.log \
  $(top_srcdir)/src/generate_single_stub_json.py \
  $(top_srcdir)/var/facet_cardinalities.ttl
	rm -f __$@ _$@
	source $(top_srcdir)/venv/bin/activate \
	  && python $(top_srcdir)/src/generate_single_stub_json.py \
	    --debug \
	    __$@ \
	    http://purl.org/co/Bag \
	    $(top_srcdir)/var/facet_cardinalities.ttl
	python3 -m json.tool \
	  __$@ \
	  _$@
	rm __$@
	mv _$@ $@

InvestigativeAction.dot: \
  InvestigativeAction.json \
  $(top_srcdir)/src/generate_single_stub_dot.py \
  $(top_srcdir)/var/facet_cardinalities.ttl
	rm -f _$@
	source $(top_srcdir)/venv/bin/activate \
	  && python3 $(top_srcdir)/src/generate_single_stub_dot.py \
	    _$@ \
	    http://example.org/kb/InvestigativeAction-1 \
	    $(top_srcdir)/var/facet_cardinalities.ttl \
	    InvestigativeAction.json
	mv _$@ $@

InvestigativeAction.json: \
  $(top_srcdir)/.venv.done.log \
  $(top_srcdir)/src/generate_single_stub_json.py \
  $(top_srcdir)/var/facet_cardinalities.ttl
	rm -f __$@ _$@
	source $(top_srcdir)/venv/bin/activate \
	  && python $(top_srcdir)/src/generate_single_stub_json.py \
	    --debug \
	    __$@ \
	    https://ontology.caseontology.org/case/investigation/InvestigativeAction \
	    $(top_srcdir)/var/facet_cardinalities.ttl
	python3 -m json.tool \
	  __$@ \
	  _$@
	rm __$@
	mv _$@ $@

check: \
  all

clean:
	@rm -f \
	  *.dot \
	  *.json \
	  *.svg
