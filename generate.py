import argparse
import importlib.resources
import json
import os
from typing import Union

import case_utils.ontology
import rdflib
from case_utils.namespace import (
    NS_CASE_INVESTIGATION,
    NS_CASE_VOCABULARY,
    NS_UCO_ACTION,
    NS_UCO_CORE,
    NS_UCO_IDENTITY,
    NS_UCO_LOCATION,
    NS_UCO_MARKING,
    NS_UCO_OBSERVABLE,
    NS_UCO_PATTERN,
    NS_UCO_ROLE,
    NS_UCO_TOOL,
    NS_UCO_TYPES,
    NS_UCO_VICTIM,
    NS_UCO_VOCABULARY,
)
from case_utils.ontology.version_info import CURRENT_CASE_VERSION

# NOTICE
# This software was produced for the U.S. Government under contract FA8702-22-C-0001,
# and is subject to the Rights in Data-General Clause 52.227-14, Alt. IV (DEC 2007)
# ©2022 The MITRE Corporation. All Rights Reserved.
# Released under PRS 18-4297.


__version__ = "0.0.2"

NS_SH = rdflib.SH
NS_RDF = rdflib.RDF
NS_XSD = rdflib.XSD

caseutils_version = case_utils.__version__
# uco_version = '0.9.0' - don't know how uco denotes their version

ignore_keys = [
    "http://www.w3.org/2000/01/rdf-schema#range",  # rdf:range
    "http://www.w3.org/2000/01/rdf-schema#label",  # rdf:label
    "http://www.w3.org/2000/01/rdf-schema#comment",  # rdf:comment
    "http://www.w3.org/ns/shacl#targetClass",  # sh:targetClass
]

# direct uco vocabulary
# obs_prefix = {str(NS_UCO_OBSERVABLE):'observable:',
#               str(NS_UCO_CORE):'core:',
#               str(NS_UCO_TOOL):'tool:',
#               str(NS_UCO_ACTION):'action:',
#               str(NS_UCO_VOCABULARY):'vocabulary:',
#               str(NS_UCO_IDENTITY):'identity:',
#               str(NS_UCO_LOCATION):'location:',
#               str(NS_UCO_MARKING):'marking:',
#               str(NS_UCO_PATTERN):'pattern:',
#               str(NS_SH):'sh:',
#               str(NS_RDF):'rdfs:',
#               'http://www.w3.org/2000/01/rdf-schema#':'rdfs:',
#               str(NS_XSD):'xsd:',
#               str(NS_UCO_VICTIM):"victim:",
#               str(NS_UCO_ROLE):"role:",
#               str(NS_UCO_TYPES):"types:",
#              }

# case-uco vocabulary
obs_prefix = {  # uco vocabulary
    str(NS_UCO_MARKING): "uco-marking:",
    str(NS_UCO_TOOL): "uco-tool:",
    str(NS_SH): "sh:",
    str(NS_RDF): "rdfs:",
    str(NS_XSD): "xsd:",
    str(NS_RDF): "rdf:",
    str(NS_UCO_OBSERVABLE): "uco-observable:",
    str(NS_UCO_MARKING): "uco-marking:",
    str(NS_UCO_IDENTITY): "uco-identity:",
    str(NS_UCO_VICTIM): "uco-victim:",
    str(NS_UCO_VOCABULARY): "uco-vocabulary:",
    str(NS_UCO_PATTERN): "uco-pattern:",
    str(NS_UCO_CORE): "uco-core:",
    str(NS_UCO_TOOL): "uco-tool:",
    str(NS_UCO_ACTION): "uco-action:",
    str(NS_UCO_LOCATION): "uco-location:",
    "http://www.w3.org/2000/01/rdf-schema#": "rdfs:",
    str(NS_UCO_ROLE): "uco-role:",
    str(NS_UCO_TYPES): "uco-types:",
    # case vocab
    str(NS_CASE_INVESTIGATION): "investigation:",
    str(NS_CASE_VOCABULARY): "vocabulary:",
}

reverse_obs_prefix = {}
for k, v in obs_prefix.items():
    reverse_obs_prefix[v] = k


def reducestring(string: str, returnChange=False):
    for k, v in obs_prefix.items():
        if k in string:
            if returnChange:
                return string.replace(k, v), True
            else:
                return string.replace(k, v)
    if returnChange:
        return str(string), False
    else:
        return str(string)


def makedirs(directory):
    os.makedirs(f"{directory}", exist_ok=True)


class main:
    def __init__(
        self,
        ontology_dir: str = None,
        directory: str = "templates",
        useCaseUtils: bool = False,
        short: bool = False,
    ):
        makedirs(directory)

        self.switch = useCaseUtils
        if not ontology_dir:
            pass
        elif "," in ontology_dir:
            ontology_dir = ontology_dir.split(",")
        else:
            ontology_dir = [ontology_dir]
        self.generate_short = short
        self.onto_dir = ontology_dir
        self.prepad = "uco"
        if ontology_dir:
            self.files_dir = []
            for onto in ontology_dir:
                if os.path.isdir(onto):
                    for onto in self.onto_dir:
                        for root, dirs, files in os.walk(onto, topdown=False):
                            for name in files:
                                if name.endswith(".ttl"):
                                    adir = os.path.join(root, name)
                                    if adir not in self.files_dir:
                                        self.files_dir.append(adir)
                elif os.path.isfile(onto):
                    if adir not in self.files_dir:
                        self.files_dir.append(adir)
        self.directory = directory

    def paduco(self, string):
        v = string.split(":")[0] + ":"
        if v in reverse_obs_prefix:
            return string  # don't pad eg. investigation
        else:
            return self.prepad + "-" + string  # if not defined, pad it.

    def removepad(self, string):
        if string.startswith(self.prepad):
            return string.replace(self.prepad + "-", "")
        else:
            return string

    def load_graph(self):
        self.g = rdflib.Graph()
        if self.onto_dir:
            for file in self.files_dir:
                self.g.parse(file)
            if self.switch:
                case_utils.ontology.load_subclass_hierarchy(self.g)
        else:
            ttl_filename = "case-" + CURRENT_CASE_VERSION + ".ttl"
            ttl_data = importlib.resources.read_text(case_utils.ontology, ttl_filename)
            self.g.parse(data=ttl_data)
            case_utils.ontology.load_subclass_hierarchy(self.g)

    def load_case_version(self):
        try:
            self.case_version = str(
                [
                    list(i)
                    for i in self.g.query(
                        "SELECT ?s ?p ?o WHERE{?s owl:versionInfo ?o}"
                    )
                ][0][2]
            )
        except Exception:
            self.case_version = CURRENT_CASE_VERSION

    def getSubClassOf(self, name: str):
        res = [
            i
            for i in self.g.query(
                "SELECT ?o WHERE {{ {} rdfs:subClassOf ?o }}".format(
                    self.removepad(name)
                )
            )
        ]
        if res:
            return res[0]
        return res  # comes back as list of triples

    def getProperty(self, name: str):
        res = [
            i
            for i in self.g.query(
                "SELECT ?o WHERE {{ {} sh:property ?o }}".format(self.removepad(name))
            )
        ]
        return res  # comes back as list of triples

    def getPath(self, name: str):
        res = [
            i
            for i in self.g.query(
                "SELECT ?o WHERE {{ {} sh:path ?o }}".format(self.removepad(name))
            )
        ]
        return res  # comes back as list of triples

    def getUCOname(self, name):
        return self.removepad(reducestring(name))

    def getParents(self, name: str, hist: list = []):
        parents = self.getSubClassOf(name)
        if not parents:
            return []
        else:
            for parent in parents:  # DFS
                p = self.getUCOname(parent)
                if p not in hist:
                    hist.append(p)
                # check if each parent has parents that isn't part of hist
                for i in self.getParents(p, hist):
                    if i not in hist:
                        hist.append(i)
        return hist

    def generate_bnodes(self):
        self.bnode_dict = {}
        for triple in self.g.query("SELECT ?s ?o WHERE { ?s sh:property ?o}"):
            s, o = triple
            self.bnode_dict[str(s)] = []
            self.bnode_dict[str(s)].append(reducestring(o))

        for triple in self.g.query("SELECT ?s ?o WHERE { ?s sh:path ?o}"):
            s, o = triple
            if str(s) not in self.bnode_dict:
                self.bnode_dict[str(s)] = []
            self.bnode_dict[str(s)].append(reducestring(o))

    def generate_classes(self):
        self.class_names = []
        for triple in self.g.query("SELECT ?s ?p WHERE {?s ?p owl:Class}"):
            s, p = triple
            self.class_names.append(self.removepad(reducestring(s)))

    def findContext(self, dict_graph: dict):
        c = {}
        for t in dict_graph.keys():
            for k, v in obs_prefix.items():
                if self.paduco(t).startswith(v):
                    c[self.paduco(v.strip(":"))] = k.strip("/") + "#"
        return c

    def load_single(self, name: str):
        single = {"@context": {}, "@graph": [{}]}
        single["@context"]["kb"] = "http://example.org/kb/"
        n = "".join(name.split(":")[1:])
        single["@graph"][0]["@id"] = "kb:" + n.lower() + "1"
        single["@graph"][0]["@type"] = self.paduco(name)

        # add the properties of the object
        props = self.getProperty(name)
        for prop in props:
            for p in self.bnode_dict[str(prop[0])]:
                if p:
                    single["@graph"][0][self.paduco(p)] = None

        single["@context"].update(self.findContext({name: None}))
        single["@context"].update(self.findContext(single["@graph"][0]))
        single["@version"] = {
            "case_util": caseutils_version,
            "ontology_version": self.case_version,
        }

        if self.generate_short:
            pass
        else:
            # add the parent's properties
            parents = self.getParents(name, [])
            for parent in parents:
                props = self.getProperty(parent)
                for prop in props:
                    for node in self.bnode_dict[str(prop[0])]:
                        single["@graph"][0][self.paduco(node)] = None
            single["@context"].update(self.findContext(single["@graph"][0]))
        return single

    def generate(self):
        self.load_graph()
        self.load_case_version()
        self.generate_bnodes()

        self.generate_classes()
        return

    def convertToJson(self, obj_name: str):
        vocab, newname = obj_name.split(":")
        obj = self.load_single(obj_name)

        if obj == {}:
            print(f"FAILED:{obj_name}")
            return
        nextdir = f"{self.directory}/{self.paduco(vocab)}"
        makedirs(nextdir)

        with open(f"{nextdir}/{newname}.json", "w") as fl:
            json.dump(obj, fl, indent=2)
            fl.close()
        print(f"Success:{self.paduco(obj_name)}")

    def run(self, name: Union[list, str] = None):
        if not name:
            name = self.class_names
        else:
            name = [self.paduco(name)]
        for k in name:
            self.convertToJson(k)
        return


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-o", "--ontology", help="ontology ttl file.", type=str, required=False
    )
    parser.add_argument(
        "--output",
        help="default output folder for studs",
        type=str,
        required=False,
        default="templates",
    )

    parser.add_argument(
        "-s", "--specific", help="specific single object name", type=str, required=False
    )
    parser.add_argument(
        "-a",
        "--caseutil",
        help="[T/F] allow case_utils to load uco ontology.",
        type=bool,
        required=False,
        default=False,
    )
    parser.add_argument(
        "-t",
        "--short",
        help="[T/F] generate short stub (no superclass properties) or full stub.",
        type=bool,
        required=False,
        default=False,
    )
    args = parser.parse_args()

    obj = main(args.ontology, args.output, args.caseutil, args.short)

    makedirs(args.output)
    obj.generate()
    if args.specific:
        obj.run(args.specific)
    else:
        obj.run()
