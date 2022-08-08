import os
import rdflib
from copy import deepcopy
import argparse
import json
from typing import Union
from case_utils.namespace import *
import case_utils.ontology
from case_utils.ontology.version_info import CURRENT_CASE_VERSION

#NOTICE
# This software was produced for the U.S. Government under contract FA8702-22-C-0001,
# and is subject to the Rights in Data-General Clause 52.227-14, Alt. IV (DEC 2007)
# ©2022 The MITRE Corporation. All Rights Reserved.
# Released under PRS 18-4297.


__version__ = '0.0.2'

NS_SH = rdflib.SH
NS_RDF = rdflib.RDF
NS_XSD = rdflib.XSD

caseutils_version  = case_utils.__version__
#uco_version = '0.9.0' - don't know how uco denotes their version

ignore_keys = ['http://www.w3.org/2000/01/rdf-schema#range', #rdf:range
               'http://www.w3.org/2000/01/rdf-schema#label', #rdf:label
               'http://www.w3.org/2000/01/rdf-schema#comment', #rdf:comment
               'http://www.w3.org/ns/shacl#targetClass', #sh:targetClass
              ]

#direct uco vocabulary
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
#              }

#case-uco vocabulary
obs_prefix = {  #uco vocabulary
                str(NS_UCO_MARKING):'uco-marking:',
                str(NS_UCO_TOOL):'uco-tool:',
                str(NS_SH):'sh:',
                str(NS_RDF):'rdfs:',
                str(NS_XSD):'xsd:',
                str(NS_RDF):'rdf:',
                str(NS_UCO_OBSERVABLE):'uco-observable:',
                str(NS_UCO_MARKING):'uco-marking:',
                str(NS_UCO_IDENTITY):'uco-identity:',
                str(NS_UCO_VICTIM):"uco-victim:",
                str(NS_UCO_VOCABULARY):'uco-vocabulary:',
                str(NS_UCO_PATTERN):'uco-pattern:',
                str(NS_UCO_CORE):'uco-core:',
                str(NS_UCO_TOOL):'uco-tool:',
                str(NS_UCO_ACTION):'uco-action:',
                str(NS_UCO_LOCATION):'uco-location:',
                'http://www.w3.org/2000/01/rdf-schema#':'rdfs:',
                str(NS_UCO_ROLE):"uco-role:",
                str(NS_UCO_TYPES):"uco-types:",
                #case vocab
                str(NS_CASE_INVESTIGATION): "investigation:",
                str(NS_CASE_VOCABULARY):'vocabulary:'}

def reducestring(string:str, returnChange=False):
    for k,v in obs_prefix.items():
        if k in string:
            if returnChange:
                return string.replace(k,v),True
            else:
                return string.replace(k,v)
    if returnChange:
        return str(string),False
    else:
        return str(string)

def removeuco(string):
    return string[3:]

def makedirs(directory):
    os.makedirs(f'{directory}',exist_ok = True)

class main:
    def __init__(self,ontology_dir:str,directory:str = "templates", useCaseUtils:bool = False ):
        makedirs(directory)

        self.switch = useCaseUtils
        if "," in ontology_dir:
            ontology_dir = ontology_dir.split(",")
        else:
            ontology_dir = [ontology_dir]
        self.onto_dir = ontology_dir
        self.prepad = ""
        self.files_dir = []
        for onto in ontology_dir:
            if os.path.isdir(onto):
                for onto in self.onto_dir:
                    for root, dirs, files in os.walk(onto, topdown = False):
                       for name in files:
                           if name.endswith(".ttl"):
                              adir = os.path.join(root, name)
                              if adir not in self.files_dir:
                                  self.files_dir.append(adir)
            elif os.path.isfile(onto):
              if adir not in self.files_dir:
                  self.files_dir.append(adir)
        self.directory = directory

    def paduco(self,string):
        if string.startswith(self.prepad):
            return string
        elif "-" in string:
            return string
        else:
            return self.prepad+"-"+string

    def getLineage(self,objn:str,hist:list=[]):
        j = []
        if objn not in self.superclassdict:
            return []
        if not self.superclassdict[objn]:
            return [objn]
        else:
            for q in self.superclassdict[objn]:
                if q not in hist:
                    hist.append(q)
                try:
                    self.getLineage(q,hist=hist)
                except:
                    pass
        if len(hist) == 1:
            return [hist]
        return hist

    def determineContext(self,parents:Union[list,dict]):
        d = []
        if type(parents)==list:
            for p in parents:
                for k,v in obs_prefix.items():
                    if p.split(":")[0]+":" == v:
                        d.append(k)
            return d
        elif type(parents)==dict:
            for s,t in parents.items():
                for k,v in obs_prefix.items():
                    if s.split(":")[0]+":" == v:
                        d.append(k)
            return d

    def generate(self):
        g = rdflib.Graph()
        for file in self.files_dir:
            g.parse(file)
        if self.switch:
            case_utils.ontology.load_subclass_hierarchy(g)

        self.case_version = str([list(i) for i in g.query('SELECT ?s ?p ?o WHERE{?s owl:versionInfo ?o}')][0][2])

        sh_path = [i for i in g.query("SELECT ?s ?p ?o WHERE {?s sh:path ?o}")]
        ot = {}
        for shpath in sh_path:
            s,p,o = shpath
            ot[str(s)] = reducestring(str(o))
        dicto3 = {}
        sh_property = [i for i in g.query("SELECT ?s ?p ?o WHERE {?s sh:property ?o }")]
        for shprop in sh_property:
            s,p,o = shprop
            string = reducestring(str(s))
            dicto3[string] = {}
            dicto3[string]['@context'] = {}
            dicto3[string]['@graph'] = [{}]
            dicto3[string]['@graph'][0]['@id'] = "kb:"+string.split(":")[-1].lower()+"1"
            dicto3[string]['@graph'][0]['@type'] = string
        for shprop in sh_property:
            s,p,o = shprop
            string = reducestring(str(s))
            dicto3[string]['@graph'][0][(ot[str(o)])] = None
            dicto3[string]['@context']['kb'] = "http://example.org/kb/"

        for shprop in sh_property:
            s,p,o = shprop
            string = reducestring(str(s))
            for k,v in obs_prefix.items():
                if v.strip(":") == string.split(":")[0]:
                    dicto3[string]['@context'][self.paduco(v).strip(":")] = k.strip("/")+"#"


        allkeys = list(dicto3.keys())
        for key in allkeys:
            dicto3[key]['@version']={'case_util':caseutils_version,'ontology_version':self.case_version}
        self.dicto2 = dicto3


        return


    def convertToJson(self,obj_name:str):
        vocab, newname = obj_name.split(":")
        obj = self.dicto2[obj_name]
        if obj == {}:
            print(f"FAILED:{obj_name}")
            return
        nextdir = f"{self.directory}/{vocab}"
        makedirs(nextdir)

        with open(f"{nextdir}/{newname}.json", 'w') as fl:
            json.dump(obj, fl,indent=2)
            fl.close()
        print(f"Success:{obj_name}")

    def run(self,name:Union[list,str] = None):
        if not name:
            name = list(self.dicto2.keys())
        elif type(name)==str:
                name = [name]
        for k in name:
            self.convertToJson(k)
        return


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-o',"--ontology", help="ontology ttl file.",type=str,required=False)
    parser.add_argument("--output", help="default output folder for studs",type=str,required=False,default = "templates")

    parser.add_argument("-s", "--specific", help="specific single object name",type=str,required=False)
    parser.add_argument("-a", "--caseutil", help="[T/F] allow case_utils to load uco ontology.",type=bool,required=False,default=False)
    args = parser.parse_args()

    if args.caseutil:
        obj = main(args.ontology,args.output,True)
    else:
        obj = main(args.ontology,args.output)

    makedirs(args.output)
    obj.generate()
    if args.specific:
        obj.run(args.specific)
    else:
        obj.run()
