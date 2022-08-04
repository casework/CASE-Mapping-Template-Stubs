import os
import rdflib
from copy import deepcopy
import argparse
import json
from typing import Union
from case_utils.namespace import *

NS_SH = rdflib.SH
NS_RDF = rdflib.RDF
NS_XSD = rdflib.XSD

ignore_keys = ['http://www.w3.org/2000/01/rdf-schema#range', #rdf:range
               'http://www.w3.org/2000/01/rdf-schema#label', #rdf:label
               'http://www.w3.org/2000/01/rdf-schema#comment', #rdf:comment
               'http://www.w3.org/ns/shacl#targetClass', #sh:targetClass
               'http://www.w3.org/2000/01/rdf-schema#subClassOf' #rdf:subClassOf
#                '@type'
              ]

obs_prefix = {str(NS_UCO_OBSERVABLE):'observable:',
              str(NS_UCO_CORE):'core:',
              str(NS_UCO_TOOL):'tool:',
              str(NS_UCO_ACTION):'action:',
              str(NS_CASE_VOCABULARY):'vocabulary:',
              str(NS_UCO_IDENTITY):'identity:',
              str(NS_UCO_LOCATION):'location:',
              str(NS_UCO_MARKING):'marking:',
              str(NS_UCO_PATTERN):'pattern:',
              str(NS_SH):'sh:',
              str(NS_RDF):'rdf:',
              str(NS_XSD):'xsd:'

             }


def reducestring(string):
    for k,v in obs_prefix.items():
        if k in string:
            return string.replace(k,v)

def paduco(string):
    return "uco-"+string

def makedirs(directory):
    os.makedirs(f'{directory}',exist_ok = True)

class main:
    def __init__(self,ontology_dir:str,directory:str = "templates"):
        makedirs(directory)
        assert os.path.isdir(ontology_dir)
        assert os.path.isdir(directory)
        self.onto_dir = ontology_dir
        obspre = ['observable','core','tool','action','identity','vocabulary','location','marking','pattern']
        dirs = os.listdir(ontology_dir)
        self.files_dir =  [os.path.join(ontology_dir,i,i+".ttl") for i in obspre]


        self.directory = directory
    def generate(self):
        self.files_dir.append('/Users/ngpiazza/Desktop/uco_jsontemplates/UCO-master/ontology/master/uco.ttl')

        g = rdflib.Graph()
        for file in self.files_dir:
            g.parse(file)

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
            if string:
                dicto3[string] = {}
                dicto3[string]['@context'] = {}
                dicto3[string]['@graph'] = [{}]
                dicto3[string]['@graph'][0]['@id'] = "kb:"+string.split(":")[-1].lower()+"1"
                dicto3[string]['@graph'][0]['@type'] = "uco-" + string
        for shprop in sh_property:
            s,p,o = shprop
            string = reducestring(str(s))
            if string:
                dicto3[string]['@graph'][0][paduco(ot[str(o)])] = None
        for shprop in sh_property:
            s,p,o = shprop
            string = reducestring(str(s))
            if string:
                dicto3[string]['@context']['kb'] = "http://example.org/kb/"
                for k,v in obs_prefix.items():
                    if v in string:
                        dicto3[string]['@context'][paduco(v)] = k.strip("/")+"#"
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
    args = parser.parse_args()

    makedirs(args.output)
    obj = main(args.ontology,args.output)
    obj.generate()
    if args.specific:
        obj.run(args.specific)
    else:
        obj.run()
