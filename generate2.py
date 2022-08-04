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
#                'http://www.w3.org/2000/01/rdf-schema#subClassOf' #rdf:subClassOf
#                '@type'
              ]

obs_prefix = {str(NS_UCO_OBSERVABLE):'observable:',
              str(NS_UCO_CORE):'core:',
              str(NS_UCO_TOOL):'tool:',
              str(NS_UCO_ACTION):'action:',
              str(NS_UCO_VOCABULARY):'vocabulary:',
              str(NS_UCO_IDENTITY):'identity:',
              str(NS_UCO_LOCATION):'location:',
              str(NS_UCO_MARKING):'marking:',
              str(NS_UCO_PATTERN):'pattern:',
              str(NS_SH):'sh:',
              str(NS_RDF):'rdfs:',
              'http://www.w3.org/2000/01/rdf-schema#':'rdfs:',
              str(NS_XSD):'xsd:',
              str(NS_UCO_VICTIM):"victim:",
              str(NS_UCO_ROLE):"role:"

             }


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

def paduco(string):
    return "uco-"+string
def removeuco(string):
    return string[3:]

def makedirs(directory):
    os.makedirs(f'{directory}',exist_ok = True)

class main:
    def __init__(self,ontology_dir:str,directory:str = "templates"):
        makedirs(directory)
        assert os.path.isdir(ontology_dir)
        assert os.path.isdir(directory)
        self.onto_dir = ontology_dir
        obspre = ['observable','core','tool','action',\
                  'identity','vocabulary','location','marking','pattern','victim','role']
        dirs = os.listdir(ontology_dir)
        self.files_dir =  [os.path.join(ontology_dir,i,i+".ttl") for i in obspre]
        self.files_dir.append(f'{ontology_dir}/master/uco.ttl')
        self.directory = directory

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
                dicto3[string]['@graph'][0]['@type'] = string
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

        superclassdict = {}
        for s,p,o in g.query("SELECT ?s ?p ?o WHERE {?s rdfs:subClassOf ?o }"):
            if not o:
                continue
            rs = reducestring(s)
            rp = r"rdfs:subClassOf"
            ro = reducestring(o)
            if rs not in superclassdict:
                superclassdict[rs] = [ro]
            else:
                superclassdict[rs].append(ro)
        self.superclassdict = superclassdict


        dict3 = {}
        for cls in self.superclassdict.keys():
            if cls in dicto3:
                if dicto3[cls]['@graph']!=[{}]:
                    dict3[cls] = dicto3[cls]
            else:
                dict3[cls] = {}

            if '@content' not in dict3[cls]:
                dict3[cls]['@context']:{}
                dict3[cls]['@context'] = {"kb":'http://example.org/kb/'}
            if '@graph' not in dict3[cls]:
                dict3[cls]['@graph'] = [{}]
                dict3[cls]['@graph'][0]['@id'] = "kb:"+cls.split(":")[-1].lower()+"1"
                dict3[cls]['@graph'][0]['@type'] = paduco(cls)
            parents = self.getLineage(cls)
            for parent in parents:
                if parent in self.superclassdict:
                    if self.superclassdict[parent]:
                        for supc in self.superclassdict[parent]:
                            if supc in dicto3:
                                if dicto3[supc]['@graph']!=[{}]:
                                    for v in dicto3[supc]['@graph'][0].keys():
                                        if v in dict3[cls]['@graph'][0]:
                                            pass
                                        else:
                                            dict3[cls]['@graph'][0][v] = None
            tmp = {}
            for k,v in dict3[cls]['@graph'][0].items():
                tmp[k.replace("uco-","")] = v

            if dict3[cls]['@graph'][0]['@type'][:3] != 'uco-':
                dict3[cls]['@graph'][0]['@type'] = paduco(dict3[cls]['@graph'][0]['@type'])
            cont = self.determineContext(tmp)
            if cont:
                for co in cont:
                    if co not in dict3[cls]['@context']:
                        dict3[cls]['@context'][paduco(obs_prefix[co])] = co.strip("/")+"#"


        self.dicto2 = dict3
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
