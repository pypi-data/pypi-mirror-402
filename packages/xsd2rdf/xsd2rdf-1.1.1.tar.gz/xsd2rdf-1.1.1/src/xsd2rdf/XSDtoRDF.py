import xml.etree.ElementTree as ET
import os
import rdflib
from rdflib import Graph, Literal, BNode, Namespace, RDF, URIRef, OWL
from pyshacl import validate
import argparse
from .utils import recursiceCheck, built_in_types, create_formatted_label, create_property_iri_suffix
import time
from datetime import datetime


class XSDtoRDF:    
    def __init__(self, abbreviations_file=None, debug=False, namespaced_concepts=False, has_prefix_for_properties=False):
        """
        Initialize the XSDtoRDF class that combines SHACL and SKOS functionalities
        
        Args:
            abbreviations_file: Optional path to a file containing abbreviations (one per line)
            debug: Boolean flag to enable debug output (default: False)
            namespaced_concepts: Boolean flag to set IRI template for SKOS concept and conceptscheme IRI's
                                 FALSE (default) will result in: xsdTargetNS/concepts/conceptschemename_conceptname
                                 TRUE will result in: xsdTargetNS/concepts/conceptschemename/conceptname
        """
        self.debug = debug
        self.namespaced_concepts = namespaced_concepts
        self.has_prefix_for_properties = has_prefix_for_properties

        # Load custom abbreviations if provided
        self.custom_abbreviations = None
        if abbreviations_file:
            from .utils import load_abbreviations_from_file
            self.custom_abbreviations = load_abbreviations_from_file(abbreviations_file)
            
        # Common namespaces
        self.era = rdflib.Namespace('http://data.europa.eu/949/')
        self.rdfSyntax = rdflib.Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
        self.rdfsNS = rdflib.Namespace('http://www.w3.org/2000/01/rdf-schema#')
        self.xsdNS = rdflib.Namespace('http://www.w3.org/2001/XMLSchema#')
        self.xsdTargetNS = rdflib.Namespace('http://example.com/')
        self.NS = rdflib.Namespace('http://example.com/shapes/')
        self.owlNS = rdflib.Namespace('http://www.w3.org/2002/07/owl#')
        self.dctNS = rdflib.Namespace('http://purl.org/dc/terms/')
        self.cc = rdflib.Namespace('http://creativecommons.org/ns#')
        
        # SHACL specific namespaces
        self.shaclNS = rdflib.Namespace('http://www.w3.org/ns/shacl#')
        
        # SKOS specific namespaces
        self.skosNS = rdflib.Namespace('http://www.w3.org/2004/02/skos/core#')
        self.dctNS = rdflib.Namespace('http://purl.org/dc/terms/')
        self.ccNS = rdflib.Namespace('http://creativecommons.org/ns#')
        self.cc_license = URIRef("http://data.europa.eu/eli/dec_impl/2017/863/oj")
        
        # Common variables
        self.type_list = built_in_types()
        self.xsdNSdict = dict()
        self.processed_files = []
        self.xsd_file = None
        self.BASE_PATH = None
        self.root = None
        self.language = "en" #default language
        
        # SHACL specific variables
        self.SHACL = Graph()
        self.shapes = []
        self.extensionShapes = []
        self.enumerationShapes = []
        self.choiceShapes = []
        self.order_list = []
        self.backUp = None
        self.subproperty_dictionary = {}  # Dictionary to track subproperties and their parent properties
        self.union_member_types = set()  # Track simpleTypes used as union memberTypes

        # SKOS specific variables
        self.SKOS = Graph()  # Graph for SKOS content
        self.concepts = []
        self.concept_schemes = {}  # Dictionary to track concept schemes and their concepts
        self.current_date = datetime.now().strftime("%Y-%m-%d")
        
        # OWL specific variables
        self.OWL_Graph = Graph()

    def debug_print(self, *args, **kwargs):
        """Print debug messages only if debug mode is enabled"""
        if self.debug:
            print(*args, **kwargs)

    def append_to_shapes_hierarchy(self, shape_to_append):
        """Append a shape to self.shapes to keep track of shapes hierarchy and debug print the updated shapes list."""
        self.shapes.append(shape_to_append)
        self.debug_print("DEBUG| Appended shape to hierarchy:", [str(shape).split(str(self.NS))[-1] if '/' in str(shape) else str(shape) for shape in self.shapes])

    def pop_from_shapes_hierarchy(self):
        """Pop the last shape from self.shapes to keep track of shapes hierarchy and debug print the updated shapes list."""
        if self.shapes:
            popped_shape = self.shapes.pop()
            self.debug_print("DEBUG| Popped shape from hierarchy:", str(popped_shape).split(str(self.NS))[-1])
            self.debug_print("DEBUG| Pop, new shapes list:", [str(shape).split(str(self.NS))[-1] if '/' in str(shape) else str(shape) for shape in self.shapes])
        else:
            self.debug_print("DEBUG| No shapes to pop from hierarchy.")
        return popped_shape

    def initialize_skos_graph(self):
        """Initialize a new RDF Graph with namespace bindings for SKOS"""
        graph = Graph()
        graph.bind('era', self.era)
        graph.bind('skos', self.skosNS)
        graph.bind('rdf', self.rdfSyntax)
        graph.bind('rdfs', self.rdfsNS)
        graph.bind('xsd', self.xsdNS)
        graph.bind('shapes', self.NS)
        graph.bind('dct', self.dctNS)
        graph.bind('cc', self.ccNS)
        graph.bind('', self.xsdTargetNS)
        graph.bind("concepts", self.xsdTargetNS + 'concepts/')
        return graph

    def isSimpleComplex(self,xsd_element,xsd_type=None):
        """A function to determine whether the type of element is SimpleType or ComplexType"""
        if xsd_element == None:
            exception = f"Element {xsd_element} not found in the XSD file."
            raise ValueError(exception)
        if xsd_type == None:
            xsd_type = xsd_element.get("type")
        if xsd_type == None:                          
            if "complexType" in xsd_element.tag:
                if xsd_element.attrib.get("mixed") == "true":
                    return "mixed"
                for child in xsd_element.findall("./"):
                    if "simpleContent" in child.tag:
                        return "simpleContent"
                return 1
            elif "simpleType" in xsd_element.tag:
                return 0
            else:
                for child in xsd_element.findall("./"):                  
                    if "complexType" in child.tag or "complexType" in xsd_element.tag:
                        if child.attrib.get("mixed") == "true":
                            return "mixed"
                        for sub_child in child:
                            if "simpleContent" in sub_child.tag:
                                return "simpleContent"
                        return 1
                    elif "simpleType" in child.tag:
                        return 0
                return 0
        elif xsd_type.split(":")[-1] in self.type_list:
            return 0 #built-in type
        else:
            xsd_type = xsd_type.split(":")[-1]
            elements = self.root.findall(f".//*[@name='{xsd_type}']", self.xsdNSdict)
            # can't combine both conditions as xmltree doesn't support the full xpath syntax
            # sometimes, some elements are named after their type, we need to find the element that contains the type definition
            # that means we need to find the complexType or the simpleType element with that name
            child = next((e for e in elements if ("complexType" in e.tag or "simpleType" in e.tag)), None)
            if child is None:
                return 0
            if "complexType" in child.tag:                
                return 1
            elif "simpleType" in child.tag:
                return 0
            else:
                # Complex content
                return 1

    def find_parent(self, element, parent):
        """Find the parent element in the XML tree"""
        for child in parent:
            if child is element:
                return parent
            if len(child) > 0:
                result = self.find_parent(element, child)
                if result is not None:
                    return result
        return None

    def parse_language(self):
        """Parse the language from the XSD metadata."""
        if self.root is not None:
            language_element = self.root.find(".//{http://purl.org/dc/terms/}language")
            if language_element is not None and language_element.text:
                self.language = language_element.text.strip()

    def process_enumeration_for_skos(self, parent_element):
        """Process an element with enumeration values for SKOS concepts"""
        # Get the name of the type/element containing the enumeration
        name = parent_element.get("name")
        if not name:
            return None

        # Check for enumeration restrictions
        enums = parent_element.findall('.//xs:enumeration', namespaces={"xs": "http://www.w3.org/2001/XMLSchema"})
        if not enums:
            return None

        # Create a concept scheme for this enumeration type
        concept_scheme_uri = URIRef(self.xsdTargetNS + "concepts/" + name + "/" + name)
        scheme_doc = None

        # Get documentation for the concept scheme
        annotation = parent_element.find("./{*}annotation")
        if annotation is not None:
            doc = annotation.find("./{*}documentation")
            if doc is not None and doc.text:
                scheme_doc = doc.text.strip()

        # Initialize or update dictionary for this concept scheme
        if name not in self.concept_schemes:
            self.concept_schemes[name] = {
                'uri': concept_scheme_uri,
                'doc': scheme_doc,
                'concepts': []
            }

        # Process each enumeration value as a SKOS concept
        concepts = []
        for enum in enums:
            value = enum.get("value")
            if value:
                if self.namespaced_concepts:
                    concept_uri = URIRef(self.xsdTargetNS + "concepts/" + name + "/" + value.replace(" ", "_"))
                else:
                    concept_uri = URIRef(self.xsdTargetNS + "concepts/" + name + "_" + value.replace(" ", "_"))
                concept_def = None

                # Process documentation for each enumeration value if available
                for annotation in enum.findall(".//{*}annotation"):
                    for doc in annotation.findall(".//{*}documentation"):
                        if doc.text:
                            concept_def = doc.text.strip()

                # Add concept to the concept scheme dictionary
                self.concept_schemes[name]['concepts'].append({
                    'uri': concept_uri,
                    'value': value,
                    'definition': Literal(concept_def, lang=self.language) if concept_def else None
                })

                # Keep track of created concepts
                self.concepts.append(concept_uri)
                concepts.append(concept_uri)

        return {
            'scheme_uri': concept_scheme_uri,
            'concepts': concepts
        }

    def transRestriction(self, tag, value, subject=None):
        """Process XSD restrictions and map them to SHACL constraints"""
        self.debug_print("DEBUG| transRestriction:", tag, value, subject)
        if subject == None:
            subject = self.shapes[-1]

        if "type" in tag or "restriction" in tag:
            if ((":" in value) and (value.split(":")[-1] in self.type_list)):
                p = self.shaclNS.datatype
                o = self.xsdNS[value.split(":")[-1]]
                self.SHACL.add((subject, p, o))
            elif value in self.type_list:
                p = self.shaclNS.datatype
                o = self.xsdNS[value]
                self.SHACL.add((subject, p, o))

        elif "default" in tag:
            p = self.shaclNS.defaultValue
            o = Literal(value)
            self.SHACL.add((subject, p, o))

        elif "fixed" in tag:
            p = self.shaclNS["in"]
            o = Literal(value)
            bn = BNode()
            self.SHACL.add((subject, p, bn))
            self.SHACL.add((bn, RDF.first, o))
            self.SHACL.add((bn, RDF.rest, RDF.nil))

        elif "pattern" in tag:
            p = self.shaclNS.pattern
            o = Literal(value)
            self.SHACL.add((subject, p, o))

        elif "maxExclusive" in tag:
            p = self.shaclNS.maxExclusive
            o = Literal(value)
            self.SHACL.add((subject, p, o))

        elif "minExclusive" in tag:
            p = self.shaclNS.minExclusive
            o = Literal(value)
            self.SHACL.add((subject, p, o))
  
        elif "maxInclusive" in tag:
            p = self.shaclNS.maxInclusive
            o = Literal(value)
            self.SHACL.add((subject, p, o))

        elif "minInclusive" in tag:
            p = self.shaclNS.minInclusive
            o = Literal(value)
            self.SHACL.add((subject, p, o))

        elif "length" in tag:        
            p = self.shaclNS.minLength
            o = Literal(int(value))
            self.SHACL.add((subject, p, o))
            p = self.shaclNS.maxLength
            o = rdflib.Literal(int(value))
            self.SHACL.add((subject, p, o))

        elif "minLength" in tag:        
            p = self.shaclNS.minLength
            o = Literal(int(value))
            self.SHACL.add((subject, p, o))

        elif "maxLength" in tag:        
            p = self.shaclNS.maxLength
            o = Literal(int(value))
            self.SHACL.add((subject, p, o))

    def transAnnotation(self, xsd_element, subject):
        if xsd_element is None:
            self.debug_print("DEBUG| transAnnotation: xsd_element is None")
            return
        self.debug_print("DEBUG| transAnnotation:", xsd_element.tag, subject)
        """Process XSD annotations and map them to SHACL descriptions"""
        for child in xsd_element.findall("./"):
            tag = child.tag
            if "annotation" in tag:
                for sub_child in child.findall("./"):
                    tag = sub_child.tag
                    if "appinfo" in tag:
                        p = self.shaclNS.description
                        o = Literal(sub_child.text, lang=self.language)
                        self.SHACL.add((subject, p, o))
                    elif "documentation" in tag:
                        p = self.shaclNS.description
                        o = Literal(sub_child.text, lang=self.language)
                        self.SHACL.add((subject, p, o))

    def transEnumeration(self, xsd_element):
        self.debug_print("DEBUG| transEnumeration:", xsd_element.tag)
        """Process XSD enumerations for both SHACL and SKOS"""
        values = []
        subject = self.shapes[-1]
        parent_element = self.find_parent(xsd_element, self.root)

        if parent_element not in self.enumerationShapes:
            self.enumerationShapes.append(parent_element)
        else:
            return xsd_element

        # Process for SKOS concepts
        # Find first parent element with name
        parent_element_with_name = parent_element
        while parent_element_with_name is not None and parent_element_with_name.get("name") is None:
            parent_element_with_name = self.find_parent(parent_element_with_name, self.root)
        enum_skos = self.process_enumeration_for_skos(parent_element_with_name)
        
        # Process for SHACL constraints
        for e in parent_element.findall('.//xs:enumeration', namespaces={"xs": "http://www.w3.org/2001/XMLSchema"}):
            if e.get("value"):
                values.append(e.get("value"))

        if values == []:
            return xsd_element
        else:
            # If we have SKOS concepts for this enumeration, use them instead of literals
            if enum_skos:
                # Use sh:class and sh:nodeKind IRI to reference SKOS concepts in the constraints
                self.SHACL.add((subject, self.shaclNS.nodeKind, self.shaclNS.IRI))
                self.SHACL.add((subject, URIRef("http://www.w3.org/ns/shacl#class"), self.skosNS.Concept))
                
                # Remove previous sh:datatype constraint if it exists
                self.SHACL.remove((subject, self.shaclNS.datatype, None))
                
                # Add SPARQL constraint to validate against the concept scheme
                sparql_bn = BNode()
                
                # Add the SPARQL constraint to the subject
                self.SHACL.add((subject, self.shaclNS.sparql, sparql_bn))
                self.SHACL.add((sparql_bn, RDF.type, self.shaclNS.SPARQLConstraint))
                self.SHACL.add((sparql_bn, self.shaclNS.message, Literal(f"The value must be a SKOS concept in the scheme {enum_skos['scheme_uri']}.", lang=self.language)))
                self.SHACL.add((sparql_bn, self.shaclNS.prefixes, Literal("skos:")))
                
                # Add the SPARQL select query
                sparql_query = f"""
                    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
                    SELECT $this
                    WHERE {{
                        $this $PATH ?concept .
                        FILTER NOT EXISTS{{
                            ?concept skos:inScheme <{enum_skos['scheme_uri']}> .
                        }}
                    }}
                """
                self.SHACL.add((sparql_bn, self.shaclNS.select, Literal(sparql_query)))                
            else:
                # Traditional sh:in constraint with literal values
                current_BN = BNode()
                self.SHACL.add((subject, self.shaclNS["in"], current_BN))
                for index in range(len(values))[0:-1]:
                    self.SHACL.add((current_BN, RDF.first, Literal(values[index]))) 
                    next_BN = BNode()
                    self.SHACL.add((current_BN, RDF.rest, next_BN)) 
                    current_BN = next_BN

                self.SHACL.add((current_BN, RDF.first, Literal(values[-1]))) 
                self.SHACL.add((current_BN, RDF.rest, RDF.nil))
                
        return xsd_element    
    
    def transEleSimple(self, xsd_element):
        self.debug_print("DEBUG| transEleSimple:", xsd_element.tag)
        """A function to translate XSD element with simple type and attribute to SHACL property shape"""
        element_name = xsd_element.get("name")
        if element_name == None:
            return xsd_element
        
        subject = self.NS[f'PropertyShape/{element_name}']

        if self.shapes != []:
            if "NodeShape" in str(self.shapes[-1]):
                pre_subject_path = self.shapes[-1].split("NodeShape/")[1]
            elif "PropertyShape" in str(self.shapes[-1]):
                pre_subject_path = self.shapes[-1].split("PropertyShape/")[1]
            
            subject = self.NS[f'PropertyShape/{pre_subject_path}/{element_name}']
            
            if subject not in self.choiceShapes:
                subject_ns = self.shapes[-2] if "PropertyShape" in str(self.shapes[-1]) and len(self.shapes) > 1 else self.shapes[-1]
                self.SHACL.add((subject_ns, self.shaclNS.property, subject))
        
        self.transAnnotation(xsd_element, subject)
        self.append_to_shapes_hierarchy(subject)
        self.SHACL.add((subject, self.rdfSyntax['type'], self.shaclNS.PropertyShape))

        element_name_as_property = create_property_iri_suffix(element_name, self.has_prefix_for_properties)
        self.SHACL.add((subject, self.shaclNS.path, self.xsdTargetNS[element_name_as_property]))

        if "attribute" not in xsd_element.tag:
            if(len(self.shapes)>1):
                element_min_occurs = Literal(int(xsd_element.get("minOccurs", "1")))
                element_max_occurs = xsd_element.get("maxOccurs", "1")
            else:
                # if the element is not evaluated as part of a NodeShape/PropertyShape relationship, no default minOccurs/maxOccurs should be added
                element_min_occurs = xsd_element.get("minOccurs")
                element_max_occurs = xsd_element.get("maxOccurs")

            if (isinstance(element_min_occurs, int) or isinstance(element_min_occurs, str)):
                element_min_occurs = Literal(int(element_min_occurs))  
                self.SHACL.add((subject, self.shaclNS.minCount, element_min_occurs))
            
            if element_max_occurs != "unbounded" and (isinstance(element_max_occurs, int) or isinstance(element_max_occurs, str)):
                element_max_occurs = Literal(int(element_max_occurs))    
                self.SHACL.add((subject, self.shaclNS.maxCount, element_max_occurs))          

        elif xsd_element.get("use") == "required":
            self.SHACL.add((subject, self.shaclNS.minCount, Literal(1)))
            self.SHACL.add((subject, self.shaclNS.maxCount, Literal(1)))        
        elif xsd_element.get("use") == "optional":
            self.SHACL.add((subject, self.shaclNS.minCount, Literal(0)))
            self.SHACL.add((subject, self.shaclNS.maxCount, Literal(1)))
        elif xsd_element.get("use") == "prohibited":
            self.SHACL.add((subject, self.shaclNS.minCount, Literal(0)))
            self.SHACL.add((subject, self.shaclNS.maxCount, Literal(0)))            
        elif "fixed" in xsd_element.attrib:
            self.SHACL.add((subject, self.shaclNS.minCount, Literal(1)))
            self.SHACL.add((subject, self.shaclNS.maxCount, Literal(1)))

        # Format the element name for labels
        formatted_label = create_formatted_label(element_name, self.custom_abbreviations)
        self.SHACL.add((subject, self.shaclNS.name, Literal(formatted_label, lang=self.language)))

        if self.order_list != []:
            self.SHACL.add((subject, self.shaclNS.order, Literal(self.order_list.pop())))

        for name in xsd_element.attrib:
            self.transRestriction(name, xsd_element.attrib[name], subject)

        element_type = xsd_element.get("type") 
        # child type, built-in type or xsd simple type
        if element_type == None:
            return xsd_element
        elif element_type.split(":")[-1] in self.type_list:
            # already translated
            return xsd_element 
        else:
            # add subPropertyOf relationship
            element_type_name = element_type.split(":")[-1]
            element_type_lowercase = element_type_name[0].lower() + element_type_name[1:] if element_type_name else ""
            self.debug_print(f"DEBUG| add subproperty: {element_name_as_property} subPropertyOf {element_type_lowercase}")
            self.subproperty_dictionary[element_name_as_property] = element_type_lowercase

            next_node = self.root.find(f'.//{{http://www.w3.org/2001/XMLSchema}}simpleType[@name="{element_type_name}"]')
            # redirect current process to the next root (simple type)
            return next_node 
            
        return xsd_element

    def transEleComplex(self, xsd_element):
        self.debug_print("DEBUG| transEleComplex:", xsd_element.tag)
        """A function to translate XSD element with complex type to SHACL node shape"""

        element_name = xsd_element.get("name")
        # Complex elements that are just implementing another complexType are used as properties to point to the final complexType class
        element_type = xsd_element.get("type")
        if element_type != None:
            # This element references a named complexType - create a PropertyShape that points to it
            self.debug_print(f"DEBUG| element {element_name} references complexType {element_type}, creating PropertyShape")

            ps_subject = None
            if self.shapes != []:
                if "NodeShape" in str(self.shapes[-1]):
                    pre_subject_path = self.shapes[-1].split("NodeShape/")[1]
                elif "PropertyShape" in str(self.shapes[-1]):
                    pre_subject_path = self.shapes[-1].split("PropertyShape/")[1]

                ps_subject = self.NS[f'PropertyShape/{pre_subject_path}/{element_name}']

                if ps_subject not in self.choiceShapes:
                    self.SHACL.add((self.shapes[-1], self.shaclNS.property, ps_subject))
            else:
                ps_subject = self.NS[f'PropertyShape/{element_name}']

            self.transAnnotation(xsd_element, ps_subject)
            self.append_to_shapes_hierarchy(ps_subject)
            self.SHACL.add((ps_subject, self.rdfSyntax['type'], self.shaclNS.PropertyShape))

            # Format the element name for labels
            formatted_label = create_formatted_label(element_name, self.custom_abbreviations)
            self.SHACL.add((ps_subject, self.shaclNS.name, Literal(formatted_label, lang=self.language)))

            self.SHACL.add((ps_subject, self.shaclNS.path, self.xsdTargetNS[create_property_iri_suffix(element_name, self.has_prefix_for_properties)]))
            self.SHACL.add((ps_subject, self.shaclNS.nodeKind, self.shaclNS.IRI))

            # Add sh:node pointing to the referenced complexType's NodeShape
            element_type_name = element_type.split(":")[-1]
            self.SHACL.add((ps_subject, self.shaclNS.node, self.NS[f'NodeShape/{element_type_name}']))

            # Add min/max count constraints
            if "attribute" not in xsd_element.tag:
                element_min_occurs = Literal(int(xsd_element.get("minOccurs", "1")))
                self.SHACL.add((ps_subject, self.shaclNS.minCount, element_min_occurs))
                element_max_occurs = xsd_element.get("maxOccurs", "1")
                if element_max_occurs != "unbounded" and (isinstance(element_max_occurs, int) or isinstance(element_max_occurs, str)):
                    element_max_occurs = Literal(int(element_max_occurs))
                    self.SHACL.add((ps_subject, self.shaclNS.maxCount, element_max_occurs))

            if self.order_list != []:
                self.SHACL.add((ps_subject, self.shaclNS.order, Literal(self.order_list.pop())))

            for name in xsd_element.attrib:
                if "type" not in name and "name" not in name:
                    self.transRestriction(name, xsd_element.attrib[name])

            return xsd_element

        subject = self.NS[f'NodeShape/{element_name}']
        ps_subject = self.NS[f'PropertyShape/{element_name}']

        if self.shapes != []:
            if "NodeShape" in str(self.shapes[-1]):
                pre_subject_path = self.shapes[-1].split("NodeShape/")[1]
            elif "PropertyShape" in str(self.shapes[-1]):
                pre_subject_path = self.shapes[-1].split("PropertyShape/")[1]

            subject = self.NS[f'NodeShape/{pre_subject_path}/{element_name}']
            ps_subject = self.NS[f'PropertyShape/{pre_subject_path}/{element_name}']
            
            if subject not in self.choiceShapes:
                self.debug_print(f"DEBUG| add subclass: {self.shapes[-1]} subClassOf {subject}")
                self.SHACL.add((self.shapes[-1], self.shaclNS.node, subject))

        self.transAnnotation(xsd_element, subject)
        self.append_to_shapes_hierarchy(subject)
        self.SHACL.add((subject, self.rdfSyntax['type'], self.shaclNS.NodeShape))
        
        # Format the element name for labels
        formatted_label = create_formatted_label(element_name, self.custom_abbreviations)
        self.SHACL.add((subject, self.shaclNS.name, Literal(formatted_label, lang=self.language)))
        
        self.SHACL.add((subject, self.shaclNS.nodeKind, self.shaclNS.IRI))
        self.SHACL.add((subject, self.shaclNS.targetClass, self.xsdTargetNS[element_name]))
    
        for name in xsd_element.attrib:
            if "type" not in name:
                self.transRestriction(name, xsd_element.attrib[name], ps_subject)

        return xsd_element
    
    def transEleComplexSimpleContent(self, xsd_element):
        self.debug_print("DEBUG| transEleComplexSimpleContent:", xsd_element.tag)
        """A function to translate XSD element with complex type simple Content to SHACL node shape
        This is a special case where the element has a complex type with simple content.
        The XML data implementation of the xsd will look like <elementName attribute="attrValue">ElementValue</elementName>
        To convert this, we need a Nodeshape for the elementName, a PropertyShape for the attrValue AND another PropertyShape for the ElementValue."""
        
        element_name = xsd_element.get("name")
        subject = self.NS[f'NodeShape/{element_name}']
        ps_subject = self.NS[f'PropertyShape/{element_name}Value']

        if self.shapes != []:
            if "NodeShape" in str(self.shapes[-1]):
                pre_subject_path = self.shapes[-1].split("NodeShape/")[1]
            elif "PropertyShape" in str(self.shapes[-1]):
                pre_subject_path = self.shapes[-1].split("PropertyShape/")[1]

            subject = self.NS[f'NodeShape/{pre_subject_path}/{element_name}']
            ps_subject = self.NS[f'PropertyShape/{pre_subject_path}/{element_name}Value']

            if subject not in self.choiceShapes:
                self.debug_print(f"DEBUG| add subclass: {self.shapes[-1]} subClassOf {subject}")
                self.SHACL.add((self.shapes[-1], self.shaclNS.node, subject))

        self.transAnnotation(xsd_element, subject)

        self.append_to_shapes_hierarchy(subject)
        
        self.SHACL.add((subject, self.rdfSyntax['type'], self.shaclNS.NodeShape))
        formatted_label = create_formatted_label(element_name, self.custom_abbreviations)
        self.SHACL.add((subject, self.shaclNS.name, Literal(formatted_label, lang=self.language)))

        # complex type does not have target, element can
        self.SHACL.add((subject, self.shaclNS.nodeKind, self.shaclNS.IRI))
        self.SHACL.add((subject, self.shaclNS.targetClass, self.xsdTargetNS[element_name]))

        if not xsd_element.findall(f".//{{http://www.w3.org/2001/XMLSchema}}simpleContent/{{http://www.w3.org/2001/XMLSchema}}extension"):
            # Add one more property shape
            self.SHACL.add((subject, self.shaclNS.property, ps_subject))
            self.SHACL.add((ps_subject, self.rdfSyntax['type'], self.shaclNS.PropertyShape))
            # Format the element name for labels
            formatted_label = f"Value of {create_formatted_label(element_name, self.custom_abbreviations)}"
            self.SHACL.add((ps_subject, self.shaclNS.name, Literal(formatted_label, lang=self.language)))
            self.SHACL.add((ps_subject, self.shaclNS.path, self.xsdTargetNS[create_property_iri_suffix(element_name, self.has_prefix_for_properties) + "Value"]))
            element_min_occurs = Literal(int(xsd_element.get("minOccurs", "1")))
            self.SHACL.add((ps_subject, self.shaclNS.minCount, element_min_occurs))
            element_max_occurs = xsd_element.get("maxOccurs", "1")
            if element_max_occurs != "unbounded" and (isinstance(element_max_occurs, int) or isinstance(element_max_occurs, str)):
                element_max_occurs = Literal(int(element_max_occurs))    
                self.SHACL.add((ps_subject, self.shaclNS.maxCount, element_max_occurs))
        
            for name in xsd_element.attrib:
                if "type" not in name:
                    self.transRestriction(name, xsd_element.attrib[name], ps_subject)

        element_type = xsd_element.get("type")
        if element_type == None:
            for i in xsd_element.findall(f".//{{http://www.w3.org/2001/XMLSchema}}simpleContent/{{http://www.w3.org/2001/XMLSchema}}extension"):
                type_name = i.get("base")
                if not type_name.split(":")[-1] in self.type_list:
                #     self.SHACL.add((ps_subject, self.shaclNS.datatype, self.xsdNS[type_name.split(":")[-1]]))
                # else:
                    type_name_local = type_name.split(":")[-1]
                    extension_node = self.root.find(f".//*[@name='{type_name_local}']")
                    extension_node_type = self.isSimpleComplex(extension_node)
                    if extension_node_type == 0:
                        next_node = self.root.find(f'.//{{http://www.w3.org/2001/XMLSchema}}simpleType[@name="{type_name}"]')
                        # self.SHACL.add((subject, self.shaclNS.node, self.NS[f'NodeShape/{type_name}']))
                        # redirect current process to the next node (simple type) to add its restrictions to the PropertyShape
                        # self.append_to_shapes_hierarchy(ps_subject)
                        # self.translate(next_node)
                        # self.pop_from_shapes_hierarchy()
                    elif extension_node_type == 1:
                        raise ValueError(f"Element {element_name} has a complex type with simple content, but the extension type {type_name} is not a simple type. This should not happen?!")
                        self.SHACL.add((ps_subject, self.shaclNS.node, self.NS[f'NodeShape/{type_name}']))
            return xsd_element
        else:
            self.debug_print(f"DEBUG| add subclass: {subject} subClassOf {element_type}")
            self.SHACL.add((subject, self.shaclNS.node, self.NS[f'NodeShape/{element_type}'])) #Will be translated later

            for i in self.root.findall(f".//*[@name='{element_type}']/{{http://www.w3.org/2001/XMLSchema}}simpleContent/{{http://www.w3.org/2001/XMLSchema}}restriction"):
                type_name = i.get("base")
                if type_name.split(":")[-1] in self.type_list:
                    self.SHACL.add((ps_subject, self.shaclNS.datatype, self.xsdNS[type_name.split(":")[-1]]))
            for i in self.root.findall(f".//*[@name='{element_type}']/{{http://www.w3.org/2001/XMLSchema}}simpleContent/{{http://www.w3.org/2001/XMLSchema}}extension"):
                type_name = i.get("base")
                if type_name.split(":")[-1] in self.type_list:
                    self.SHACL.add((ps_subject, self.shaclNS.datatype, self.xsdNS[type_name.split(":")[-1]]))
                else:
                    type_name_local2 = type_name.split(':')[-1]
                    extension_node = self.root.find(f".//*[@name='{type_name_local2}']")
                    extension_node_type = self.isSimpleComplex(extension_node)
                    if extension_node_type == 0:
                        next_node = extension_node
                        # redirect current process to the next root (simple type)
                        return next_node 
                    elif extension_node_type == 1:
                        self.debug_print(f"DEBUG| add subclass: {ps_subject} subClassOf {type_name}")
                        self.SHACL.add((ps_subject, self.shaclNS.node, self.NS[f'NodeShape/{type_name}']))

            return xsd_element
        return xsd_element

    def transComplexType(self, xsd_element):
        self.debug_print("DEBUG| transComplexType:", xsd_element.tag)
        """A function to translate XSD complex type to SHACL node shape""" 

        # Check if we need to process this complex type as a complex type with simple content
        element_type = self.isSimpleComplex(xsd_element)
        if element_type == 0:
            self.debug_print("DEBUG| Warning: Element has a simple type, while it's being processed as a complex type.")
            # raise ValueError(f"Element {xsd_element.get('name')} has a simple type, but it is being processed as a complex type. This should not happen!")
        
        if element_type == "simpleContent" or element_type == "mixed":
            return self.transEleComplexSimpleContent(xsd_element)
        #elif element_type == 1:
        else:
            element_name = xsd_element.get("name")
            subject = self.NS[f'NodeShape/{element_name}']
            if self.shapes != []:
                if "NodeShape" in str(self.shapes[-1]):
                    pre_subject_path = self.shapes[-1].split("NodeShape/")[1]
                elif "PropertyShape" in str(self.shapes[-1]):
                    pre_subject_path = self.shapes[-1].split("PropertyShape/")[1]

                subject = self.NS[f'NodeShape/{pre_subject_path}/{element_name}']

                # To solve that it is the child node of any element
                if subject not in self.choiceShapes:
                    self.debug_print(f"DEBUG| add subclass: {self.shapes[-1]} subClassOf {subject}")
                    self.SHACL.add((self.shapes[-1], self.shaclNS.node, subject))

            self.transAnnotation(xsd_element, subject)
            self.append_to_shapes_hierarchy(subject)
            self.SHACL.add((subject, self.rdfSyntax['type'], self.shaclNS.NodeShape))
            formatted_label = create_formatted_label(element_name, self.custom_abbreviations)
            self.SHACL.add((subject, self.shaclNS.name, Literal(formatted_label, lang=self.language)))
            self.SHACL.add((subject, self.shaclNS.targetClass, self.xsdTargetNS[element_name]))

            for name in xsd_element.attrib:
                self.transRestriction(name, xsd_element.attrib[name])

            return xsd_element   

    def transGroup(self, xsd_element):
        self.debug_print("DEBUG| transGroup:", xsd_element.tag)
        """A function to translate XSD complex type to SHACL node shape""" 
        element_name = xsd_element.get("name")
        if element_name == None:
            element_name = xsd_element.get("id")
        subject = self.NS[f'NodeShape/{element_name}']
        self.append_to_shapes_hierarchy(subject)
        self.SHACL.add((subject, self.rdfSyntax['type'], self.shaclNS.NodeShape))
        formatted_label = create_formatted_label(element_name, self.custom_abbreviations)
        self.SHACL.add((subject, self.shaclNS.name, Literal(formatted_label, lang=self.language)))
        # complex type does not have target, element can

        for name in xsd_element.attrib:
            self.transRestriction(name, xsd_element.attrib[name])

        return xsd_element    

    def transExtension(self, xsd_element):
        self.debug_print("DEBUG| transExtension:", xsd_element.tag)
        """A function to translate XSD extension"""
        element_name = xsd_element.get("base")
        # xsd_type = xsd_element.get("type")
        # if element_name in self.extensionShapes:
        #     return xsd_element
        if element_name.split(":")[-1] in self.type_list:
            if "PropertyShape" in str(self.shapes[-1]):
                self.SHACL.add((self.shapes[-1], self.shaclNS.datatype, self.xsdNS[element_name.split(":")[-1]]))
            else:
                pre_subject_path = self.shapes[-1].split("NodeShape/")[1]
                ps_subject = self.NS[f'PropertyShape/{pre_subject_path}/{pre_subject_path.split("/")[-1]}Value']                
                subject = self.shapes[-1]
                self.SHACL.add((subject, self.shaclNS.property, ps_subject)) 
                self.SHACL.add((ps_subject, self.rdfSyntax['type'], self.shaclNS.PropertyShape))
                # Format the element name for labels
                pre_subject_name = pre_subject_path.split("/")[-1]
                formatted_label = create_formatted_label(f"{pre_subject_name}Value", self.custom_abbreviations)
                self.SHACL.add((ps_subject, self.shaclNS.name, Literal(formatted_label, lang=self.language)))
                self.SHACL.add((ps_subject, self.shaclNS.datatype, self.xsdNS[element_name.split(":")[-1]]))
                self.SHACL.add((ps_subject, self.shaclNS.path, self.xsdTargetNS[create_property_iri_suffix(pre_subject_path, self.has_prefix_for_properties)+"Value"]))
                self.SHACL.add((ps_subject, self.shaclNS.minCount, Literal(int(1))))
                self.SHACL.add((ps_subject, self.shaclNS.maxCount, Literal(int(1))))

            return xsd_element
        else:
            # self.extensionShapes.append(element_name)
            sub_node = self.root.find(f'.//*[@name="{element_name.split(":")[-1]}"]', self.xsdNSdict)
            element_type = self.isSimpleComplex(sub_node, element_name.split(":")[-1])
            subject = self.shapes[-1]

            if element_type == 1 or element_type == "subClassOf":
                # complexType will be translated separately so we just need to add the node shape
                self.debug_print(f"DEBUG| add subclass: {subject} subClassOf {element_name}")
                self.SHACL.add((subject, self.shaclNS.node, self.NS[f'NodeShape/{element_name}'])) 
                return xsd_element
            else:
                pre_subject_path = self.shapes[-1].split("NodeShape/")[1]
                ps_subject = self.NS[f'PropertyShape/{pre_subject_path}/{element_name}']
                self.SHACL.add((subject, self.shaclNS.property, ps_subject)) 
                self.SHACL.add((ps_subject, self.rdfSyntax['type'], self.shaclNS.PropertyShape))
                # Format the element name for labels
                formatted_label = create_formatted_label(element_name, self.custom_abbreviations)
                self.SHACL.add((ps_subject, self.shaclNS.name, Literal(formatted_label, lang=self.language)))
                self.SHACL.add((ps_subject, self.shaclNS.path, self.xsdTargetNS[create_property_iri_suffix(element_name, self.has_prefix_for_properties)]))
                self.SHACL.add((ps_subject, self.shaclNS.minCount, Literal(int(1))))
                self.SHACL.add((ps_subject, self.shaclNS.maxCount, Literal(int(1))))
                self.append_to_shapes_hierarchy(ps_subject)
                self.translate(sub_node)
                self.pop_from_shapes_hierarchy()

        return xsd_element

    def transUnion(self, xsd_element):
        self.debug_print("DEBUG| transUnion:", xsd_element.tag)
        values = []
        subject = self.shapes[-1]

        if xsd_element.get("memberTypes") and len(xsd_element)==0:
            memberTypes = xsd_element.get("memberTypes").split(" ")

            current_BN = BNode()
            self.SHACL.add((subject, self.shaclNS["or"], current_BN))

            for index in range(len(memberTypes)):
                memberType = memberTypes[index]
                if memberType.split(":")[-1] in self.type_list:
                    shape_BN = BNode()
                    self.SHACL.add((current_BN, RDF.first, shape_BN)) 
                    self.SHACL.add((shape_BN, self.shaclNS.datatype, self.xsdNS[memberType.split(":")[-1]])) 
                    next_BN = BNode()
                    if index == len(memberTypes)-1:
                        self.SHACL.add((current_BN, RDF.rest, RDF.nil)) 
                    else:   
                        self.SHACL.add((current_BN, RDF.rest, next_BN))
                    current_BN = next_BN
                else:
                    sub_node = self.root.find(f'.//*[@name="{memberType.split(":")[-1]}"]', self.xsdNSdict)
                    element_type = self.isSimpleComplex(sub_node, memberType)
                    if element_type == 1:
                        self.SHACL.add((current_BN, RDF.first, self.NS[f'NodeShape/{memberType}'])) 
                        next_BN = BNode()
                        if index == len(memberTypes)-1:
                            self.SHACL.add((current_BN, RDF.rest, RDF.nil)) 
                        else:   
                            self.SHACL.add((current_BN, RDF.rest, next_BN))
                        current_BN = next_BN
                    elif element_type == 0:
                        sub_BN = BNode()
                        self.SHACL.add((current_BN, RDF.first, sub_BN))
                        self.append_to_shapes_hierarchy(sub_BN)
                        self.translate(sub_node)
                        self.pop_from_shapes_hierarchy()
                        next_BN = BNode()
                        if index == len(memberTypes)-1:
                            self.SHACL.add((current_BN, RDF.rest, RDF.nil)) 
                        else:   
                            self.SHACL.add((current_BN, RDF.rest, next_BN))
                        current_BN = next_BN
        elif xsd_element.get("memberTypes") and len(xsd_element)>0:
            memberTypes = xsd_element.get("memberTypes").split(" ")

            current_BN = BNode()
            self.SHACL.add((subject, self.shaclNS["or"], current_BN))

            for index in range(len(memberTypes)):
                memberType = memberTypes[index]
                if memberType.split(":")[-1] in self.type_list:
                    shape_BN = BNode()
                    self.SHACL.add((current_BN, RDF.first, shape_BN)) 
                    self.SHACL.add((shape_BN, self.shaclNS.datatype, self.xsdNS[memberType.split(":")[-1]])) 
                    next_BN = BNode()
                    self.SHACL.add((current_BN, RDF.rest, next_BN))
                    current_BN = next_BN
                else:
                    sub_node = self.root.find(f'.//*[@name="{memberType}"]', self.xsdNSdict)
                    element_type = self.isSimpleComplex(sub_node, memberType)
                    if element_type == 1:
                        self.SHACL.add((current_BN, RDF.first, self.NS[f'NodeShape/{memberType}'])) 
                        next_BN = BNode()  
                        self.SHACL.add((current_BN, RDF.rest, next_BN))
                        current_BN = next_BN
                    elif element_type == 0:
                        sub_BN = BNode()
                        self.SHACL.add((current_BN, RDF.first, sub_BN))
                        self.append_to_shapes_hierarchy(sub_BN)
                        self.translate(sub_node)
                        self.pop_from_shapes_hierarchy()
                        next_BN = BNode()
                        self.SHACL.add((current_BN, RDF.rest, next_BN))
                        current_BN = next_BN         
            index = 0
            for sub_node in xsd_element:
                index += 1
                element_type = self.isSimpleComplex(sub_node)
                if element_type == 1:
                    self.SHACL.add((current_BN, RDF.first, self.NS[f'NodeShape/{memberType}'])) 
                    next_BN = BNode()
                    if index == len(xsd_element):
                        self.SHACL.add((current_BN, RDF.rest, RDF.nil)) 
                    else:   
                        self.SHACL.add((current_BN, RDF.rest, next_BN))
                    current_BN = next_BN
                elif element_type == 0:
                    sub_BN = BNode()
                    self.SHACL.add((current_BN, RDF.first, sub_BN))
                    self.append_to_shapes_hierarchy(sub_BN)
                    self.translate(sub_node)
                    self.pop_from_shapes_hierarchy()
                    next_BN = BNode()
                    if index == len(xsd_element):
                        self.SHACL.add((current_BN, RDF.rest, RDF.nil)) 
                    else:   
                        self.SHACL.add((current_BN, RDF.rest, next_BN))
                    current_BN = next_BN        
        else:
            current_BN = BNode()
            self.SHACL.add((subject, self.shaclNS["or"], current_BN))
            index = 0
            for sub_node in xsd_element:
                index += 1
                element_type = self.isSimpleComplex(sub_node)
                if element_type == 1:
                    self.SHACL.add((current_BN, RDF.first, self.NS[f'NodeShape/{memberType}'])) 
                    next_BN = BNode()
                    if index == len(memberTypes)-1:
                        self.SHACL.add((current_BN, RDF.rest, RDF.nil)) 
                    else:   
                        self.SHACL.add((current_BN, RDF.rest, next_BN))
                    current_BN = next_BN
                elif element_type == 0:
                    sub_BN = BNode()
                    self.SHACL.add((current_BN, RDF.first, sub_BN))
                    self.append_to_shapes_hierarchy(sub_BN)
                    self.translate(sub_node)
                    self.pop_from_shapes_hierarchy()
                    next_BN = BNode()
                    if index == len(xsd_element):
                        self.SHACL.add((current_BN, RDF.rest, RDF.nil)) 
                    else:   
                        self.SHACL.add((current_BN, RDF.rest, next_BN))
                    current_BN = next_BN         

    def transChoice(self, xsd_element):
        self.debug_print("DEBUG| transChoice:", xsd_element.tag)
        values = []
        subject = self.shapes[-1]
        if "NodeShape" in str(subject):
            pre_subject_path = subject.split("NodeShape/")[1]
        elif "PropertyShape" in str(subject):
            pre_subject_path = subject.split("PropertyShape/")[1]

        for child in xsd_element.findall("./"):
            tag = child.tag
            if "element" in tag:
                element_type = self.isSimpleComplex(child)
                if element_type == 0:
                    # values.append(self.NS[f'PropertyShape/{child.get("name")}'])
                    temp = self.NS[f'PropertyShape/{pre_subject_path}/{child.get("name")}']
                    values.append(temp)
                else:
                    # values.append(self.NS[f'NodeShape/{child.get("name")}'])
                    temp = self.NS[f'NodeShape/{pre_subject_path}/{child.get("name")}']
                    values.append(temp)
                self.choiceShapes.append(temp)
            elif "group" in tag:
                temp = child.get("ref")
                if temp == None:
                    temp = child.get("id")
                if temp == None:
                    temp = child.get("name")
                self.choiceShapes.append(temp)
                values.append(self.NS[f'NodeShape/{temp}'])

        values = [i for i in values if not i.endswith("None")]
        if values == []:
            return xsd_element
        else:
            current_BN = BNode()
            self.SHACL.add((subject, self.shaclNS["xone"], current_BN))
            for index in range(len(values))[0:-1]:
                self.SHACL.add((current_BN, RDF.first, URIRef(values[index]))) 
                next_BN = BNode()
                self.SHACL.add((current_BN, RDF.rest, next_BN)) 
                current_BN = next_BN

            self.SHACL.add((current_BN, RDF.first, URIRef(values[-1]))) 
            self.SHACL.add((current_BN, RDF.rest, RDF.nil)) 
            return xsd_element 

    def transEleComplexRef(self, xsd_element):
        self.debug_print("DEBUG| transComplexTypeReference:", xsd_element.tag)
        """A function to translate a reference to a complex XSD element to SHACL property shape"""
        
        element_name = xsd_element.get("ref")

        subject = self.NS[f'PropertyShape/{element_name}']

        if self.shapes != []:
            if "NodeShape" in str(self.shapes[-1]):
                pre_subject_path = self.shapes[-1].split("NodeShape/")[1]
            elif "PropertyShape" in str(self.shapes[-1]):
                pre_subject_path = self.shapes[-1].split("PropertyShape/")[1]

            subject = self.NS[f'PropertyShape/{pre_subject_path}/{element_name}']
            
            if subject not in self.choiceShapes:
                subject_ns = self.shapes[-2] if "PropertyShape" in str(self.shapes[-1]) and len(self.shapes) > 1 else self.shapes[-1]
                self.SHACL.add((subject_ns, self.shaclNS.property, subject))

        self.transAnnotation(xsd_element, subject)
        self.append_to_shapes_hierarchy(subject)
        self.SHACL.add((subject, self.rdfSyntax['type'], self.shaclNS.PropertyShape))
   
        self.SHACL.add((subject, self.shaclNS.path, self.xsdTargetNS[create_property_iri_suffix(element_name, self.has_prefix_for_properties)]))
        self.SHACL.add((subject, self.shaclNS.nodeKind, self.shaclNS.IRI))
        
        if "attribute" not in xsd_element.tag:
            element_min_occurs = Literal(int(xsd_element.get("minOccurs", "1")))
            self.SHACL.add((subject, self.shaclNS.minCount, element_min_occurs))
            element_max_occurs = xsd_element.get("maxOccurs", "1")
            if element_max_occurs != "unbounded" and (isinstance(element_max_occurs, int) or isinstance(element_max_occurs, str)):
                element_max_occurs = Literal(int(element_max_occurs))    
                self.SHACL.add((subject, self.shaclNS.maxCount, element_max_occurs))          

        elif xsd_element.get("use") == "required":
            self.SHACL.add((subject, self.shaclNS.minCount, Literal(1)))
            self.SHACL.add((subject, self.shaclNS.maxCount, Literal(1)))        
        elif xsd_element.get("use") == "optional":
            self.SHACL.add((subject, self.shaclNS.minCount, Literal(0)))
            self.SHACL.add((subject, self.shaclNS.maxCount, Literal(1)))
        elif xsd_element.get("use") == "prohibited":
            self.SHACL.add((subject, self.shaclNS.minCount, Literal(0)))
            self.SHACL.add((subject, self.shaclNS.maxCount, Literal(0)))
        elif "fixed" in xsd_element.attrib:
            self.SHACL.add((subject, self.shaclNS.minCount, Literal(1)))
            self.SHACL.add((subject, self.shaclNS.maxCount, Literal(1)))
            
        # Format the element name for labels
        formatted_label = create_formatted_label(element_name, self.custom_abbreviations)
        self.SHACL.add((subject, self.shaclNS.name, Literal(formatted_label, lang=self.language)))

        if self.order_list != []:
            self.SHACL.add((subject, self.shaclNS.order, Literal(self.order_list.pop())))

        for name in xsd_element.attrib:
            self.transRestriction(name, xsd_element.attrib[name])


        # Get the 'type' attribute of the referenced element
        ref_node = self.root.find(f'.//{{http://www.w3.org/2001/XMLSchema}}element[@name="{element_name}"]')
        element_type = None
        if ref_node is not None:
            element_type = ref_node.get("type")
        if element_type is not None:
            self.SHACL.add((subject, URIRef("http://www.w3.org/ns/shacl#class"), self.xsdTargetNS[element_type]))
        else:
            self.SHACL.add((subject, URIRef("http://www.w3.org/ns/shacl#class"), self.xsdTargetNS[element_name]))

        return xsd_element

    def transEleSimpleRef(self, xsd_element):       
        self.debug_print("DEBUG| transComplexTypeReference:", xsd_element.tag)
        """A function to translate a reference to a simple XSD element to SHACL property shape"""
        element_name = xsd_element.get("ref")

        subject = self.NS[f'PropertyShape/{element_name}']

        if self.shapes != []:            
            shapes_origin = self.shapes[-2] if "PropertyShape" in str(self.shapes[-1]) and len(self.shapes) > 1 else self.shapes[-1]
            pre_subject_path = shapes_origin.split("NodeShape/")[1]
            
            subject = self.NS[f'PropertyShape/{pre_subject_path}/{element_name}']
            
            if subject not in self.choiceShapes:
                self.SHACL.add((shapes_origin, self.shaclNS.property, subject))

        self.transAnnotation(xsd_element, subject)
        self.append_to_shapes_hierarchy(subject)
        self.SHACL.add((subject, self.rdfSyntax['type'], self.shaclNS.PropertyShape))

        self.SHACL.add((subject, self.shaclNS.path, self.xsdTargetNS[create_property_iri_suffix(element_name, self.has_prefix_for_properties)]))

        if "attribute" not in xsd_element.tag:
            element_min_occurs = Literal(int(xsd_element.get("minOccurs", "1")))
            self.SHACL.add((subject, self.shaclNS.minCount, element_min_occurs))
            element_max_occurs = xsd_element.get("maxOccurs", "1")
            if element_max_occurs != "unbounded" and (isinstance(element_max_occurs, int) or isinstance(element_max_occurs, str)):
                element_max_occurs = Literal(int(element_max_occurs))    
                self.SHACL.add((subject, self.shaclNS.maxCount, element_max_occurs))          

        elif xsd_element.get("use") == "required":
            self.SHACL.add((subject, self.shaclNS.minCount, Literal(1)))
            self.SHACL.add((subject, self.shaclNS.maxCount, Literal(1)))        
        elif xsd_element.get("use") == "optional":
            self.SHACL.add((subject, self.shaclNS.minCount, Literal(0)))
            self.SHACL.add((subject, self.shaclNS.maxCount, Literal(1)))
        elif xsd_element.get("use") == "prohibited":
            self.SHACL.add((subject, self.shaclNS.minCount, Literal(0)))
            self.SHACL.add((subject, self.shaclNS.maxCount, Literal(0)))
        elif "fixed" in xsd_element.attrib:
            self.SHACL.add((subject, self.shaclNS.minCount, Literal(1)))
            self.SHACL.add((subject, self.shaclNS.maxCount, Literal(1)))
            
        # Format the element name for labels
        formatted_label = create_formatted_label(element_name, self.custom_abbreviations)
        self.SHACL.add((subject, self.shaclNS.name, Literal(formatted_label, lang=self.language)))

        if self.order_list != []:
            self.SHACL.add((subject, self.shaclNS.order, Literal(self.order_list.pop())))

        for name in xsd_element.attrib:
            self.transRestriction(name, xsd_element.attrib[name], subject)

        # start a new translation session for the referenced element
        # Find the referenced element or attribute by name
        ref_node = self.root.find(f'.//{{http://www.w3.org/2001/XMLSchema}}element[@name="{element_name}"]')
        if ref_node is None:
            ref_node = self.root.find(f'.//{{http://www.w3.org/2001/XMLSchema}}attribute[@name="{element_name}"]')
        
        if ref_node is not None:
            self.transAnnotation(ref_node, subject)        
            for name in ref_node.attrib:
                self.transRestriction(name, ref_node.attrib[name], subject)
            self.translate(ref_node)
        else:
            self.debug_print(f"DEBUG| Warning: Referenced element or attribute '{element_name}' not found in XSD")

        return xsd_element

    def translate(self, current_node):
        """A function to iteratively translate XSD to SHACL and SKOS"""        
        
        # For all children of the current node, translate them based on their tag
        # While translating a child, we may come back to this function to translate the children of that child
        # This is a recursive-like structure, but we use a self.shapes to track the hierarchy
        # We will pop or append to this variable depending on the context of the translation 
        for child in current_node.findall("*"):
            self.debug_print(f"DEBUG| Translating: {child.tag} {child.get('name', '')}{child.get('ref', '')}")
            tag = child.tag
            next_node = child
            pop_needed = False
            if ("element" in tag) or (("attribute" in tag) and ("attributeGroup" not in tag)):
                if child.get("ref"):
                    ref = child.get("ref")
                    if ":" in ref:
                        ref = ref.split(":")[-1]
                    ref_node = self.root.find(f".//*[@name='{ref}']")
                    if ref_node != None:
                        element_type = self.isSimpleComplex(ref_node)
                        if element_type != 0:
                            next_node = self.transEleComplexRef(child)
                            pop_needed = True
                        else:
                            next_node = self.transEleSimpleRef(child)
                            pop_needed = True

                else:
                    element_type = self.isSimpleComplex(child)
                    if element_type == 0:
                        next_node = self.transEleSimple(child)
                    elif element_type == 1:                        
                        possible_next_node = self.transEleComplex(child)
                        if possible_next_node is not None:
                            next_node = possible_next_node
                        else: 
                            continue
                    elif element_type == "simpleContent" or element_type == "mixed":
                        next_node = self.transEleComplexSimpleContent(child)
            elif ("simpleType" in tag) and (self.shapes == []):
                # Skip processing simpleTypes that are only used as union memberTypes
                type_name = child.get("name")
                if type_name and type_name in self.union_member_types:
                    # Check if this type is directly referenced by any element
                    is_directly_referenced = False
                    for elem in self.root.findall('.//*[@type]', self.xsdNSdict):
                        elem_type = elem.get('type')
                        if elem_type:
                            elem_type_name = elem_type.split(':')[-1]
                            if elem_type_name == type_name and 'element' in elem.tag:
                                is_directly_referenced = True
                                break

                    if not is_directly_referenced:
                        self.debug_print(f"DEBUG| Skipping simpleType '{type_name}' (only used as union memberType)")
                        continue

                next_node = self.transEleSimple(child)
                pop_needed = True
            elif ("extension" in tag):
                next_node = self.transExtension(child)
            elif ("complexType" in tag) and (child.get("name")):
                next_node = self.transComplexType(child)
            elif ("attributeGroup" in tag):
                if child.get("ref"):
                    # next_node = self.root.find(f".//*[@name='{child.get('ref')}']")
                    ref_value = child.get("ref")
                    self.debug_print(f"DEBUG| add subclass: {self.shapes[-1]} subClassOf {ref_value}")
                    self.SHACL.add((self.shapes[-1], self.shaclNS.node, self.NS[f'NodeShape/{ref_value}']))
                else:
                    next_node = self.transComplexType(child)
            elif ("group" in tag):
                ref = child.get("ref")
                if ref:
                    if ref in self.choiceShapes:
                        pass
                    else:
                        self.debug_print(f"DEBUG| add subclass: {self.shapes[-1]} subClassOf {ref}")
                        self.SHACL.add((self.shapes[-1], self.shaclNS.node, self.NS[f'NodeShape/{ref}']))
                else:
                    next_node = self.transGroup(child)
            #combine with prev?
            elif ("simpleType" in tag):
                next_node=self.transEleSimple(child)
                self.process_enumeration_for_skos(child)
            elif ("complexType" in tag): 
                pass
            elif ("restriction" in tag):
                value = child.get("base")
                self.transRestriction(tag, value)
            elif ("enumeration" in tag):
                self.transEnumeration(child)
            elif ("sequence" in tag):
                pass
            elif ("choice" in tag):
                self.transChoice(child)
            elif ("all" in tag):
                pass
            elif ("union" in tag):
                self.transUnion(child)
                continue
            elif ("appinfo" in tag) or ("documentation" in tag) or ("annotation" in tag):
                continue
            else:
                value = child.get("value")
                self.transRestriction(tag, value)
                
            # Translate next node
            self.translate(next_node)

            # Removed: or self.extension
            # an <xs:extension> is always inside another case that will return true below
            if pop_needed or (("element" in tag) and (child.get("name"))) or (("attribute" in tag) and ("attributeGroup" not in tag) and not child.get("ref")) or (("complexType" in tag) and (child.get("name"))) or (("attributeGroup" in tag) and (child.get("name"))) or (("group" in tag) and (child.get("name") or child.get("id"))):
                self.pop_from_shapes_hierarchy()
                self.enumerationShapes.clear()
        
        if self.backUp != None:
            self.pop_from_shapes_hierarchy()
            temp = self.backUp
            self.backUp = None
            self.translate(temp)

    def parseXSD(self, ref_root, current_base_path=None):
        """Parse XSD to handle imports and includes, resolving relative paths correctly."""
        if current_base_path is None:
            current_base_path = self.BASE_PATH

        # Process xs:include
        for include_import_elem in ref_root.findall(".//xs:include", namespaces={"xs": "http://www.w3.org/2001/XMLSchema"}):
            self.root.remove(include_import_elem)
            included_imported_xsd_path = include_import_elem.get("schemaLocation")
            if included_imported_xsd_path and included_imported_xsd_path not in self.processed_files:
                try:
                    # Resolve path relative to the current base path
                    include_abs_path = os.path.join(current_base_path, included_imported_xsd_path)
                    next_ref_root = ET.parse(include_abs_path).getroot()
                    self.processed_files.append(included_imported_xsd_path)
                except Exception as e:
                    print("Error: parse include error file:", included_imported_xsd_path)
                    print("Complete exception follows below. Processing stopped")
                    raise e

                # The new base path for further includes/imports is the directory of the included file
                next_base_path = os.path.dirname(include_abs_path)
                for child in next_ref_root.findall("./"):
                    if ("import" not in child.tag) or ("include" not in child.tag):
                        self.root.append(child)
                self.parseXSD(next_ref_root, current_base_path=next_base_path)
        
        # Process xs:import
        for include_import_elem in ref_root.findall(".//xs:import", namespaces={"xs": "http://www.w3.org/2001/XMLSchema"}):
            self.root.remove(include_import_elem)
            included_imported_xsd_path = include_import_elem.get("schemaLocation")
            if included_imported_xsd_path and included_imported_xsd_path not in self.processed_files:
                try:
                    import_abs_path = os.path.join(current_base_path, included_imported_xsd_path)
                    next_ref_root = ET.parse(import_abs_path).getroot()
                    self.processed_files.append(included_imported_xsd_path)
                except Exception as e:
                    print("Parse error import file:", included_imported_xsd_path)
                    self.processed_files.append(included_imported_xsd_path)
                    continue

                next_base_path = os.path.dirname(import_abs_path)
                for child in next_ref_root.findall("./"):
                    if ("import" not in child.tag) or ("include" not in child.tag):
                        self.root.append(child)
                self.parseXSD(next_ref_root, current_base_path=next_base_path)

    def collect_union_member_types(self):
        """
        Collect all simpleType names that are used as memberTypes in union elements.
        These types should not be created as standalone properties.
        """
        # Find all union elements with memberTypes attribute
        for union_elem in self.root.findall('.//*[@memberTypes]', self.xsdNSdict):
            member_types_str = union_elem.get('memberTypes')
            if member_types_str:
                # memberTypes is a space-separated list
                member_types = member_types_str.split()
                for member_type in member_types:
                    # Remove namespace prefix if present (e.g., "xs:string" -> "string")
                    type_name = member_type.split(':')[-1]
                    # Only track if it's not a built-in XSD type
                    if type_name not in self.type_list:
                        self.union_member_types.add(type_name)

        self.debug_print(f"DEBUG| Union member types found: {self.union_member_types}")

    def writeShapeToFile(self, file_name):
        """Write SHACL shapes to file"""
        for prefix in self.xsdNSdict:
            self.SHACL.bind(prefix, self.xsdNSdict[prefix])
        self.SHACL.bind("ex", self.xsdTargetNS)
        self.SHACL.bind("shapes", self.NS)
        self.SHACL.bind("nodeshapes", self.NS + 'NodeShape/')
        self.SHACL.bind("propertyshapes", self.NS + 'PropertyShape/')
        self.SHACL.bind('era', 'http://data.europa.eu/949/')
        self.SHACL.bind('sh', 'http://www.w3.org/ns/shacl#', False)
        self.SHACL.bind('skos', 'http://www.w3.org/2004/02/skos/core#')

        self.SHACL.serialize(destination=file_name, format='turtle')

    def writeSkosToFile(self, output_dir):
        """Save each concept scheme to a separate file."""
        if not self.concept_schemes:
            print("No concept schemes found to save.")
            return
            
        # Create output directory if it doesn't exist
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)
            
        base_filename = os.path.basename(self.xsd_file)
        
        # Save each concept scheme to a separate file
        for name, scheme_data in self.concept_schemes.items():
            # Create a new graph for this concept scheme
            graph = self.initialize_skos_graph()
            # Add the concept scheme first
            scheme_uri = scheme_data['uri']
            
            # Create formatted label for the concept scheme
            formatted_name = create_formatted_label(name, self.custom_abbreviations)
            conceptscheme_label = "Concept Scheme for " + formatted_name
            
            graph.add((scheme_uri, RDF.type, self.skosNS.ConceptScheme))
            graph.add((scheme_uri, self.rdfsNS.label, Literal(conceptscheme_label, lang=self.language)))
            
            # Add Dublin Core metadata
            graph.add((scheme_uri, self.dctNS.title, Literal(conceptscheme_label, lang=self.language)))
            graph.add((scheme_uri, self.dctNS.issued, Literal(self.current_date, datatype=self.xsdNS.date)))
            graph.add((scheme_uri, self.dctNS.modified, Literal(self.current_date, datatype=self.xsdNS.date)))
            
            # Add Creative Commons license
            graph.add((scheme_uri, self.ccNS.license, self.cc_license))
            
            # Add documentation if available
            if scheme_data['doc']:
                graph.add((scheme_uri, self.skosNS.definition, Literal(scheme_data['doc'], lang=self.language)))
            
            # Add all concepts for this scheme
            for concept in scheme_data['concepts']:
                # Create formatted label for the concept
                formatted_value = create_formatted_label(concept['value'], self.custom_abbreviations)
                
                graph.add((concept['uri'], RDF.type, self.skosNS.Concept))
                graph.add((concept['uri'], self.skosNS.notation, Literal(formatted_value, datatype=self.xsdNS.token)))
                graph.add((concept['uri'], self.skosNS.inScheme, scheme_uri))
                graph.add((concept['uri'], self.skosNS.topConceptOf, scheme_uri))
                
                if concept['definition']:
                    graph.add((concept['uri'], self.skosNS.prefLabel, Literal(concept['definition'], lang=self.language)))
                else:
                    graph.add((concept['uri'], self.skosNS.prefLabel, Literal(formatted_value, lang=self.language)))

            # Save the graph to a file
            file_path = os.path.join(output_dir, f"{base_filename}.skos.{name}.ttl")
            graph.serialize(destination=file_path, format="turtle")
            print(f"Saved concept scheme '{name}' to {file_path}")

    def initialize_owl_ontology(self):
        """Initialize the OWL ontology with namespace bindings and ontology declaration"""
        # Add namespace bindings
        self.OWL_Graph.bind('era', self.era)
        self.OWL_Graph.bind('owl', self.owlNS)
        self.OWL_Graph.bind('rdf', self.rdfSyntax)
        self.OWL_Graph.bind('rdfs', self.rdfsNS)
        self.OWL_Graph.bind('xsd', self.xsdNS)
        self.OWL_Graph.bind('dct', self.dctNS)
        self.OWL_Graph.bind('cc', self.ccNS)
        self.OWL_Graph.bind('', self.xsdTargetNS)
        
        # Create ontology declaration
        ontology_uri = URIRef(self.xsdTargetNS)
        self.OWL_Graph.add((ontology_uri, RDF.type, OWL.Ontology))
        
        # Add ontology label based on the XSD file name
        xsd_name = os.path.splitext(os.path.basename(self.xsd_file))[0]
        formatted_name = create_formatted_label(xsd_name,self.custom_abbreviations)
        self.OWL_Graph.add((ontology_uri, self.rdfsNS.label, Literal(f"Ontology generated from {formatted_name} XSD", lang="en")))
        
        # Extract all Dublin Core terms from the XSD annotation
        dcterms = self.extract_dcterms_from_annotation()
        
        # Add all extracted dcterms to the ontology
        # If specific terms are not found, use default values
        
        # Set default values for common dcterms if they don't exist in the extracted data
        defaults = {
            'description': f"Ontology generated from {formatted_name} XSD",
            'title': f"Ontology generated from {formatted_name} XSD",
            'created': self.current_date,
            'modified': self.current_date,
            'issued': self.current_date
        }
        
        # Add all dcterms from the annotation element
        for term, value in dcterms.items():
            if isinstance(value, list):
                # Add each value separately for repeated terms
                for val in value:
                    # Try to detect if the value should be a literal with language tag
                    if term in ['title', 'description', 'abstract', 'subject', 'creator', 'publisher', 'contributor', 'rights']:
                        self.OWL_Graph.add((ontology_uri, getattr(self.dctNS, term), Literal(val, lang=self.language)))
                    else:
                        # For dates and other non-language tagged terms
                        self.OWL_Graph.add((ontology_uri, getattr(self.dctNS, term), Literal(val)))
            else:
                # Add single value
                if term in ['title', 'description', 'abstract', 'subject', 'creator', 'publisher', 'contributor', 'rights']:
                    self.OWL_Graph.add((ontology_uri, getattr(self.dctNS, term), Literal(value, lang=self.language)))
                else:
                    # For dates and other non-language tagged terms
                    self.OWL_Graph.add((ontology_uri, getattr(self.dctNS, term), Literal(value)))
        
        # Add default values for missing common dcterms
        for term, default_value in defaults.items():
            if term not in dcterms:
                if term in ['title', 'description']:
                    self.OWL_Graph.add((ontology_uri, getattr(self.dctNS, term), Literal(default_value, lang=self.language)))
                else:
                    self.OWL_Graph.add((ontology_uri, getattr(self.dctNS, term), Literal(default_value)))
    
    def extract_dcterms_from_annotation(self):
        """Extract Dublin Core terms from the XSD schema's first annotation element"""
        dcterms_dict = {}
        
        if self.root is not None:
            # Find the first annotation element in the schema
            annotation = self.root.find(".//{http://www.w3.org/2001/XMLSchema}annotation")
            if annotation is not None:
                # Look for any elements that are dcterms
                for element in annotation.findall(".//*"):
                    # Check if element namespace is Dublin Core terms
                    if element.tag.startswith("{http://purl.org/dc/terms/}"):
                        # Extract term name from namespace URI
                        term = element.tag.split('}')[1]
                        if element.text and element.text.strip():
                            # Store the term and its value
                            # If the term already exists in the dictionary, make it a list or append to existing list
                            if term in dcterms_dict:
                                if isinstance(dcterms_dict[term], list):
                                    dcterms_dict[term].append(element.text.strip())
                                else:
                                    # Convert single value to list with both values
                                    dcterms_dict[term] = [dcterms_dict[term], element.text.strip()]
                            else:
                                # Store single value
                                dcterms_dict[term] = element.text.strip()
        
        return dcterms_dict

    def generate_owl_graph(self):
        """Generate OWL graph from SHACL shapes"""
        
        print("    Step 1/7: Generating OWL classes from NodeShapes...")
        owl_classes = self.SHACL.query("""
            prefix owl: <http://www.w3.org/2002/07/owl#>
            prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            prefix sh: <http://www.w3.org/ns/shacl#>

            construct {
            ?classIRI a owl:Class;
                rdfs:label ?classLabel;
                rdfs:comment ?classComment.
            }
            where {
            ?nodeshape a sh:NodeShape;
                sh:targetClass ?classIRI;
                sh:name ?classLabel.
                OPTIONAL{?nodeshape sh:description ?classComment . } 
            }"""
        )
        
        # Add the results of the OWL class query to the OWL graph
        class_count = 0
        for s, p, o in owl_classes:
            self.OWL_Graph.add((s, p, o))
            class_count += 1
        print(f"    Created {class_count} OWL classes")

        print("    Step 2/7: Generating OWL subclass relationships...")
        owl_subclasses = self.SHACL.query("""
                prefix owl: <http://www.w3.org/2002/07/owl#>
                prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                prefix sh: <http://www.w3.org/ns/shacl#>

                construct {
                ?classIRI rdfs:subClassOf ?superClassIRI.
                }
                where {
                    ?nodeshape a sh:NodeShape;
                        sh:targetClass ?classIRI;
                        sh:node ?superNodeShapeIRI.

                    ?superNodeShapeIRI a sh:NodeShape;
                        sh:targetClass ?superClassIRI.
                }
            """
        )
        # Add the results of the OWL class query to the OWL graph
        subclass_count = 0
        for s, p, o in owl_subclasses:
            self.OWL_Graph.add((s, p, o))
            subclass_count += 1
        print(f"    Created {subclass_count} subclass relationships")

        print("    Step 3/7: Generating OWL datatype properties...")
        owl_dataproperties = self.SHACL.query("""
            prefix owl: <http://www.w3.org/2002/07/owl#>
            prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            prefix sh: <http://www.w3.org/ns/shacl#>

            construct {
                ?propertyIRI a owl:DatatypeProperty;
                    rdfs:label ?propertyLabel;
                    rdfs:comment ?propertyComment.

                    # We'll create the domain/range relationships separately to handle properly
            }
            where {
                {
                    # Regular datatype properties with direct sh:datatype
                    ?datatypeProperty a sh:PropertyShape;
                        sh:path ?propertyIRI;
                        sh:datatype ?datatype.

                    OPTIONAL{?datatypeProperty sh:name ?propertyLabel;}
                    OPTIONAL{?datatypeProperty sh:description ?propertyComment;}
                }
                UNION {
                    # Union datatype properties (sh:or with datatypes inside)
                    ?datatypeProperty a sh:PropertyShape;
                        sh:path ?propertyIRI;
                        sh:or ?orList.

                    OPTIONAL{?datatypeProperty sh:name ?propertyLabel;}
                    OPTIONAL{?datatypeProperty sh:description ?propertyComment;}
                }
            }
            """)

        # Add the results of the OWL data property query to the OWL graph
        dataprop_count = 0
        for s, p, o in owl_dataproperties:
            self.OWL_Graph.add((s, p, o))
            dataprop_count += 1
        print(f"    Created {dataprop_count} datatype properties (including union types)")

        print("    Step 4/7: Generating functional properties...")
        # Add functional properties
        # This query is a bit special because a propertyIRI can be used in multiple PropertyShapes (linked to a NodeShape!)
        # If that's the case, the propertyIRI is only a owl:FunctionalProperty if all of those PropertyShapes have the same maxCount = 1
        owl_functional_properties = self.SHACL.query("""
            prefix owl: <http://www.w3.org/2002/07/owl#>
            prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            prefix sh: <http://www.w3.org/ns/shacl#>
            prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

            construct {
                ?propertyIRI a owl:FunctionalProperty.
            }
            where {
                {
                    select ?propertyIRI 
                    where {
                        {
                            ?nodeshape a sh:NodeShape;
                                sh:property ?propertyShape;
                                .
                        }
                        union {
                            ?nodeshape a sh:NodeShape;
                                sh:xone ?xone_list;
                            .
                            ?xone_list rdf:rest*/rdf:first ?propertyShape.
                        }
                        ?propertyShape a sh:PropertyShape;
                            sh:path ?propertyIRI;
                            sh:maxCount ?maxCount;
                            .
                    }
                    GROUP BY ?propertyIRI
                    HAVING (COUNT(distinct ?maxCount) = 1 && AVG(?maxCount) = 1) 
                }
            }
        """)

        # Add the results of the OWL functional properties query to the OWL graph
        functional_count = 0
        for s, p, o in owl_functional_properties:
            self.OWL_Graph.add((s, p, o))
            functional_count += 1
        print(f"    Created {functional_count} functional properties")

        print("    Step 5/7: Generating OWL object properties...")
        # Create additional query for object properties
        owl_objectproperties = self.SHACL.query("""
            prefix owl: <http://www.w3.org/2002/07/owl#>
            prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            prefix sh: <http://www.w3.org/ns/shacl#>

            construct {
                ?propertyIRI a owl:ObjectProperty;
                    rdfs:label ?propertyLabel;
                    rdfs:comment ?propertyComment.
                
                # We'll create the domain/range relationships separately to handle properly
            }
            where {
                ?objectProperty a sh:PropertyShape;
                    sh:path ?propertyIRI;    
                    sh:nodeKind ?propertyNodekind.

                    OPTIONAL{?objectProperty sh:name ?propertyLabel;}
                    OPTIONAL{?objectProperty sh:description ?propertyComment;}
                    
                    FILTER(?propertyNodekind = sh:IRI)
            }
        """)

        # Add the basic object property triples from the query
        objectprop_count = 0
        for s, p, o in owl_objectproperties:
            self.OWL_Graph.add((s, p, o))
            objectprop_count += 1
        print(f"    Created {objectprop_count} object properties")

        # Additional step: Ensure all properties referenced in SHACL have explicit types
        # This catches edge cases like union types that might have been missed
        print("    Step 5.5/7: Ensuring all SHACL properties have OWL types...")
        all_shacl_properties = self.SHACL.query("""
            prefix owl: <http://www.w3.org/2002/07/owl#>
            prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            prefix sh: <http://www.w3.org/ns/shacl#>

            select distinct ?propertyIRI ?propertyLabel ?propertyComment
            where {
                ?propertyShape a sh:PropertyShape;
                    sh:path ?propertyIRI.
                OPTIONAL{?propertyShape sh:name ?propertyLabel;}
                OPTIONAL{?propertyShape sh:description ?propertyComment;}
            }
        """)

        # Check each property and add a default type if missing
        properties_typed_count = 0
        for row in all_shacl_properties:
            prop_iri = row.propertyIRI
            # Check if this property already has an OWL type
            has_datatype = (prop_iri, RDF.type, OWL.DatatypeProperty) in self.OWL_Graph
            has_objecttype = (prop_iri, RDF.type, OWL.ObjectProperty) in self.OWL_Graph

            if not has_datatype and not has_objecttype:
                # Property has no type - add it as DatatypeProperty by default
                # (most union types and edge cases are datatype properties)
                self.OWL_Graph.add((prop_iri, RDF.type, OWL.DatatypeProperty))

                # Also add label and comment if available
                if row.propertyLabel:
                    self.OWL_Graph.add((prop_iri, self.rdfsNS.label, row.propertyLabel))
                if row.propertyComment:
                    self.OWL_Graph.add((prop_iri, self.rdfsNS.comment, row.propertyComment))

                properties_typed_count += 1
                self.debug_print(f"DEBUG| Added missing type for property: {prop_iri}")

        if properties_typed_count > 0:
            print(f"    Added missing types for {properties_typed_count} properties")

        print("    Step 6/7: Generating property domains...")
        # Now handle domain and range separately to properly create owl:unionOf when needed
        domain_query = self.SHACL.query("""
            prefix owl: <http://www.w3.org/2002/07/owl#>
            prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            prefix sh: <http://www.w3.org/ns/shacl#>

            select ?propertyIRI ?domainClass
            where {
                ?nodeshape a sh:NodeShape;
                    sh:targetClass ?domainClass;
                    sh:property ?propertyShapeIri .

                ?propertyShapeIri a sh:PropertyShape;
                    sh:path ?propertyIRI.
            }
            GROUP BY ?propertyIRI ?domainClass
        """)

        # Group domains by property
        domains_by_property = {}
        domain_count = 0
        for row in domain_query:
            property_iri = row.propertyIRI
            class_iri = row.domainClass
            domain_count += 1
            
            if property_iri not in domains_by_property:
                domains_by_property[property_iri] = []
            domains_by_property[property_iri].append(class_iri)
        
        print(f"    Processing {len(domains_by_property)} properties with domains ({domain_count} total domain relationships)...")

        # Create domain relationships with owl:unionOf when needed
        domain_relationships = 0
        for property_iri, classes in domains_by_property.items():
            if len(classes) == 1:
                # Single domain
                self.OWL_Graph.add((property_iri, self.rdfsNS.domain, classes[0]))
                domain_relationships += 1
            else:
                # Multiple domains need owl:unionOf
                union_node = BNode()
                self.OWL_Graph.add((property_iri, self.rdfsNS.domain, union_node))
                self.OWL_Graph.add((union_node, RDF.type, OWL.Class))
                self.OWL_Graph.add((union_node, OWL.unionOf, self.create_rdf_list(classes)))
                domain_relationships += 1
        print(f"    Created {domain_relationships} domain relationships")

        print("    Step 7/7: Generating property ranges...")
        # Handle ranges similarly
        range_query = self.SHACL.query("""
            prefix owl: <http://www.w3.org/2002/07/owl#>
            prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            prefix sh: <http://www.w3.org/ns/shacl#>
            prefix skos: <http://www.w3.org/2004/02/skos/core#>

            select ?propertyIRI ?rangeClass
            where {
                {
                    ?objectProperty a sh:PropertyShape;
                        sh:path ?propertyIRI;    
                        sh:nodeKind sh:IRI.
                                            
                    {
                        ?objectProperty sh:class ?rangeClass.
                    } 
                    UNION {
                        ?objectProperty sh:sparql ?propertySparql.
                        ?propertySparql sh:select ?query.
                        FILTER(CONTAINS(?query, "skos:inScheme"))
                        BIND(skos:Concept AS ?rangeClass)
                    }
                }  
                UNION {
                    ?datatypeProperty a sh:PropertyShape;
                        sh:path ?propertyIRI;    
                        sh:datatype ?rangeClass.        
                }
            }
            GROUP BY ?propertyIRI ?rangeClass
        """)

        # Group ranges by property
        ranges_by_property = {}
        range_count = 0
        for row in range_query:
            property_iri = row.propertyIRI
            class_iri = row.rangeClass
            range_count += 1
            
            if property_iri not in ranges_by_property:
                ranges_by_property[property_iri] = []
            ranges_by_property[property_iri].append(class_iri)

        print(f"    Processing {len(ranges_by_property)} properties with ranges ({range_count} total range relationships)...")

        # Create range relationships with owl:unionOf when needed
        range_relationships = 0
        for property_iri, classes in ranges_by_property.items():
            if len(classes) == 1:
                # Single range
                self.OWL_Graph.add((property_iri, self.rdfsNS.range, classes[0]))
                range_relationships += 1
            else:
                # Multiple classes need owl:unionOf
                union_node = BNode()
                self.OWL_Graph.add((property_iri, self.rdfsNS.range, union_node))
                self.OWL_Graph.add((union_node, RDF.type, OWL.Class))
                self.OWL_Graph.add((union_node, OWL.unionOf, self.create_rdf_list(classes)))
                range_relationships += 1
        print(f"    Created {range_relationships} range relationships")

        # Loop over subPropertyOf dictionary and add subPropertyOf relationships
        subprop_count = 0
        for sub_property, super_property in self.subproperty_dictionary.items():
            # Convert property strings to proper IRIs with the target namespace
            sub_property_iri = self.xsdTargetNS[sub_property]
            super_property_iri = self.xsdTargetNS[super_property]
            self.OWL_Graph.add((sub_property_iri, self.rdfsNS.subPropertyOf, super_property_iri))
            subprop_count += 1
        
        if subprop_count > 0:
            print(f"    Created {subprop_count} subPropertyOf relationships")
        
        print(f"    OWL generation completed! Total triples in OWL graph: {len(self.OWL_Graph)}")
    
    def create_rdf_list(self, items):
        """
        Create an RDF list from a list of items.
        """
        if not items:
            return RDF.nil
        
        head = BNode()
        self.OWL_Graph.add((head, RDF.first, items[0]))
        
        if len(items) == 1:
            self.OWL_Graph.add((head, RDF.rest, RDF.nil))
        else:
            tail = self.create_rdf_list(items[1:])
            self.OWL_Graph.add((head, RDF.rest, tail))
        
        return head
    
    def writeOWLToFile(self, file_name):       
        # Save OWL ontology to file
        self.OWL_Graph.serialize(destination=file_name, format='turtle')
        print(f"Saved OWL ontology in {file_name}!")

    def evaluate_file(self, xsd_file, output_dir=None):
        """
        Parse the given XSD file and generate both SHACL shapes and SKOS concepts
        
        Args:
            xsd_file: Path to the XSD file to be converted
            output_dir: Directory to save the generated files (optional)
        """
        self.xsd_file = xsd_file
        self.BASE_PATH = os.path.dirname(xsd_file)
        self.xsdTree = ET.parse(xsd_file)
        self.root = self.xsdTree.getroot()

        recursiceCheck(self.root)

        self.xsdNSdict = dict([node for (_, node) in ET.iterparse(xsd_file, events=['start-ns'])])

        self.parse_language()
        print(f"Using language tag: {self.language}")

        # Parse XSD to handle imports and includes
        print("#########Start parsing XSD file")
        self.parseXSD(self.root)

        # Collect union member types to avoid creating them as standalone properties
        self.collect_union_member_types()

        # Extract namespaces from the XSD
        xmlns = self.root.get('xmlns')
        if xmlns:
            # Normalize namespace by removing trailing / (if present) and then adding it back
            normalized_ns = xmlns.rstrip('/') + '/'
            self.NS = Namespace(f"{normalized_ns}shapes/")
            
        # Extract the target namespace
        for key in self.root.attrib:
            if key == "targetNamespace":
                # Normalize namespace by removing trailing / (if present) and then adding it back
                normalized_ns = self.root.attrib[key].rstrip('/') + '/'
                self.xsdTargetNS = Namespace(normalized_ns)
                if not xmlns:  # Only update NS if xmlns was not found
                    self.NS = Namespace(f"{normalized_ns}shapes/")

        print("#########Start translating XSD to RDF (SHACL + SKOS)")
        start = time.time()
        self.translate(self.root)
        end = time.time()
        print(f"RDF conversion completed in {end - start:.2f} seconds")

        print("#########Start validating SHACL shapes syntax")
        shaclValidation = Graph()
        shaclValidation.parse("https://www.w3.org/ns/shacl-shacl")
        
        if len(self.SHACL) < 10000:
            r = validate(self.SHACL, shacl_graph=shaclValidation)
            if not r[0]:
                print(r[2])
            else:
                print("Well formed SHACL shapes!")
        else:
            print("Skip SHACL shape syntax check using pyshacl due to the size of SHACL shapes is too large!")

        print("#########Start creating OWL graph")
        self.initialize_owl_ontology()
        self.generate_owl_graph()

        # Determine output directory
        if output_dir is None:
            output_dir = self.BASE_PATH
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        # Compose output file paths
        base_filename = os.path.basename(xsd_file)
        shacl_file = os.path.join(output_dir, base_filename + ".shape.ttl")
        owl_file = os.path.join(output_dir, base_filename + ".owl.ttl")

        print("#########Start writing SHACL shapes to file")
        self.writeShapeToFile(shacl_file)
        print(f"Saved SHACL shapes in {shacl_file}!")
        
        print("#########Start writing SKOS concepts to files")
        self.writeSkosToFile(output_dir)
        
        print("#########Start writing OWL to file")
        self.writeOWLToFile(owl_file)

        return {
            'shacl': self.SHACL,
            'concept_schemes': self.concept_schemes
        }
