[INSTALL & SETUP]:
1. `pip install -r requirements.txt` #rdflib
2. `pip install case_utils` #https://github.com/casework/CASE-Utilities-Python/tree/Draft-autogen-classes or https://github.com/casework/CASE-Utilities-Python

We don't use other functions of case_utils other than their namespaces so you label it independently, the rest will function.

[USAGE/RUN]
  - generate.py [-o:required,-s:Optional[],--output:default="templates"]
    --"-o", ontology directory, required.
    --"-s", specify a class by name that has at least one property, Optional. The name must be conventional to the original vocabulary eg. observable, tool, action, etc.
    --"--output", specify a specific directory to put the stubs, Optional, default = "templates"


Examples:

"python generate.py -o ../UCO-master/ontology -s observable:DeviceFacet"
"python generate.py -o ../UCO-master/ontology"


Folders: 
1. `\template` is generated by generate2.py
2. `\template2` is generated by generate.py


NOTE: There are two scripts, generate.py and generate2.py.
- `generate.py` only generates the properties that are under sh:property and sh:path of an object, this implies this does not include inherited properties from superclasses.
- `generate2.py` attempts to generate both the properties that show under sh:property, sh:path and superclasses. Eg. 'tool:DefensiveTool' does not have any non-inherited properties, but has two superclasses: tool:Tool and core:UcoObject (which is the superclass of tool:Tool) which the script will attempt to trackdown the superclasses properties, though it can get really long. Therefore, choose `generate.py` for a short stub indicating only properties that explicitly tied to the object, or `generate2.py` for a longer stub indicating properties from also their superclasses.



The code loads the ontology into an rdfgraph, however, because it is an empty graph, querying for directly the shacl properties isn't as simple as first expected. Both codes leverage querying the graph for related triples to make the preprocessing such as chaining the bnode ids with the shacl properties. `generate2.py` goes a step further to querying for chaining of objects with their superclasses to retrieve the extensive superclass properties.


current limitations:
The code `generate.py` will generate for objects which have sh:property, however if there is an object which has no non-inherited properties, only superclass properties, code doesn't grab superclass properties.

`generate2.py` may miss a few owl objects depending on where it breaks during the processing phase.
