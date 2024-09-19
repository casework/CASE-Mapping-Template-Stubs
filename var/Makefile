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

top_srcdir := ..

all: \
  facet_cardinalities.ttl

check: \
  all

clean:
	@rm -f \
	  _* \
	  *.ttl

facet_cardinalities.ttl: \
  $(top_srcdir)/.venv.done.log \
  $(top_srcdir)/src/facet_cardinalities_ttl.py
	rm -f __$@ _$@
	source $(top_srcdir)/venv/bin/activate \
	  && python3 $(top_srcdir)/src/facet_cardinalities_ttl.py \
	    __$@
	# Normalize if normalizing jar has already been downloaded from pre-commit.
	test ! -r $(top_srcdir)/rdf-toolkit.jar \
	  || java -jar $(top_srcdir)/rdf-toolkit.jar \
	    --inline-blank-nodes \
	    --source __$@ \
	    --source-format turtle \
	    --target _$@ \
	    --target-format turtle
	if [ -r _$@ ]; then rm __$@ ; else mv __$@ _$@ ; fi
	mv _$@ $@
