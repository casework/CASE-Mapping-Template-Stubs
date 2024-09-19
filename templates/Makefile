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
  all-ontologies.mk
	$(MAKE) \
	  --file all-ontologies.mk

all-ontologies.mk: \
  $(top_srcdir)/.venv.done.log \
  $(top_srcdir)/src/generate_all_ontologies_mk.py
	source $(top_srcdir)/venv/bin/activate \
	  && python3 $(top_srcdir)/src/generate_all_ontologies_mk.py \
	    _$@
	mv _$@ $@

check: \
  all

clean:
	@ls */Makefile \
	  | while read subdir_makefile ; do \
	      $(MAKE) \
	        --directory $$(dirname $${subdir_makefile}) \
	        clean ; \
	    done
	@rm -f \
	  all-ontologies.mk
