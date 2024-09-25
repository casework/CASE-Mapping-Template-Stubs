# Maintenance

This repository derives JSON-LD "stub" dictionaries from the ontologies in CDO.

The generation process for these ontologies uses `make`, with some balance of hard-coding and source-including to save on code redundancy.

The maintenance necessary for this repository occurs when a new ontology is released.  In most cases, this will be the necessary script to follow:

```bash
# (On a fresh Git clone.)
make clean
make -j
git add templates
git commit -s -m "Regenerate Make-managed files"
# Editing and updating README.md to refresh the implemented CASE version should come next.
```

(Note: Some `make`s assume infinite CPU resources if `-j` (`--jobs`) does not have a following numeric argument.  On, e.g., macOS, you might want to follow that flag with the number of cores on your system.)

In the event a new ontology (i.e., a new namespace with `owl:Class`es) is added, a new directory under `/templates` will need to be created and given a `Makefile`.  Copying `/templates/uco-core/Makefile` into the new directory and adapting its hard-coded prefix IRI will enable the workflow to function again.
