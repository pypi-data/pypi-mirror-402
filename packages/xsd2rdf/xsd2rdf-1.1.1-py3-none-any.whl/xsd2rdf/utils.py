import os

def recursiceCheck(node):
    """
    A recursive function to check the correctness of XSD Element
    """
    identifyXSD(node)
    for child in node.findall("./"):
        recursiceCheck(child)

def identifyXSD(element):
    """
    A function to identify and check the type and correctness of XSD Element
    """
    tag = element.tag.split("}")[-1]
    if "all" == tag:
        allowed_tags = ["element"]
        if False in [child.tag.split("}")[-1] in allowed_tags for child in element.findall("*")]:
            raise Exception("Invalid XSD file: all should only contain element")
    elif "annotation" == tag:
        allowed_tags = ["appinfo", "documentation"]
        if False in [child.tag.split("}")[-1] in allowed_tags for child in element.findall("*")]:
            raise Exception("Invalid XSD file: annotation should only contain appinfo or documentation")
    elif "any" == tag or "anyAttribute" == tag or "field" == tag or "import" == tag or "include" == tag or "notation" == tag or "selector" == tag:
        allowed_tags = ["annotation"]
        if False in [child.tag.split("}")[-1] in allowed_tags for child in element.findall("*")]:
            raise Exception("Invalid XSD file: any or anyAttribute or field or import or include or notation or selector should only contain annotation")
    elif "attribute" == tag:
        allowed_tags = ["annotation", "simpleType"]
        if False in [child.tag.split("}")[-1] in allowed_tags for child in element.findall("*")]:
            raise Exception("Invalid XSD file: attribute should only contain annotation or simpleType")
    elif "attributeGroup" == tag:
        allowed_tags = ["annotation", "attribute", "attributeGroup", "anyAttribute"]
        if False in [child.tag.split("}")[-1] in allowed_tags for child in element.findall("*")]:
            raise Exception("Invalid XSD file: attributeGroup should only contain annotation, attribute, attributeGroup or anyAttribute")
    elif "choice" == tag:
        allowed_tags = ["annotation", "element", "group", "choice", "sequence", "any"]
        if False in [child.tag.split("}")[-1] in allowed_tags for child in element.findall("*")]:
            raise Exception("Invalid XSD file: choice should only contain annotation, element, group, choice, sequence or any")
    elif "complexContent" == tag:
        allowed_tags = ["annotation", "restriction", "extension"]
        if False in [child.tag.split("}")[-1] in allowed_tags for child in element.findall("*")]:
            raise Exception("Invalid XSD file: complexContent should only contain annotation, restriction or extension")
    elif "complexType" == tag:
        allowed_tags = ["annotation", "simpleContent", "complexContent", "group", "all", "choice", "sequence", "attribute", "attributeGroup", "anyAttribute"]
        if False in [child.tag.split("}")[-1] in allowed_tags for child in element.findall("*")]:
            raise Exception("Invalid XSD file: complexType should only contain annotation, simpleContent, complexContent, group, all, choice, sequence, attribute, attributeGroup or anyAttribute")
    elif "element" == tag:
        allowed_tags = ["annotation", "simpleType", "complexType", "unique", "key", "keyref"]
        if False in [child.tag.split("}")[-1] in allowed_tags for child in element.findall("*")]:
            raise Exception("Invalid XSD file: element should only contain annotation, simpleType, complexType, unique, key or keyref")
    elif "extension" == tag:
        allowed_tags = ["annotation", "group", "all", "choice", "sequence", "attribute", "attributeGroup", "anyAttribute"]
        if False in [child.tag.split("}")[-1] in allowed_tags for child in element.findall("*")]:
            raise Exception("Invalid XSD file: extension should only contain annotation, group, all, choice, sequence, attribute, attributeGroup or anyAttribute")
    elif "group" == tag:
        allowed_tags = ["annotation", "all", "choice", "sequence"]
        if False in [child.tag.split("}")[-1] in allowed_tags for child in element.findall("*")]:
            raise Exception("Invalid XSD file: group should only contain annotation, all, choice or sequence")
    elif "key" == tag or "keyref" == tag or "unique" == tag:
        allowed_tags = ["annotation", "selector", "field"]
        if False in [child.tag.split("}")[-1] in allowed_tags for child in element.findall("*")]:
            raise Exception("Invalid XSD file: key or keyref or unique should only contain annotation, selector or field")
    elif "list" == tag or "union" == tag:
        allowed_tags = ["annotation", "simpleType"]
        if False in [child.tag.split("}")[-1] in allowed_tags for child in element.findall("*")]:
            raise Exception("Invalid XSD file: list or union should only contain annotation or simpleType")
    elif "redefine" == tag:
        allowed_tags = ["annotation", "simpleType", "complexType", "group", "attributeGroup"]
        if False in [child.tag.split("}")[-1] in allowed_tags for child in element.findall("*")]:
            raise Exception("Invalid XSD file: redefine should only contain annotation, simpleType, complexType, group or attributeGroup")
    elif "restriction" == tag:
        allowed_tags = ["annotation", "group", "all", "choice", "sequence", "attribute", "attributeGroup", "anyAttribute", "enumeration", "fractionDigits", "length", "maxExclusive", "maxInclusive", "maxLength", "minExclusive", "minInclusive", "minLength", "pattern", "simpleType", "totalDigits", "whiteSpace"]
        if False in [child.tag.split("}")[-1] in allowed_tags for child in element.findall("*")]:
            raise Exception("Invalid XSD file: restriction should only contain annotation,  group, all, choice, sequence, attribute, attributeGroup, anyAttribute, enumeration, fractionDigits, length, maxExclusive, maxInclusive, maxLength, minExclusive, minInclusive, minLength, pattern, simpleType, totalDigits, or whiteSpace")
    elif "schema" == tag:
        allowed_tags = ["annotation", "include", "import", "redefine", "annotation", "simpleType", "complexType", "group", "attributeGroup", "element", "attribute", "notation"]
        if False in [child.tag.split("}")[-1] in allowed_tags for child in element.findall("*")]:
            raise Exception("Invalid XSD file: schema should only contain annotation, include, import, redefine, annotation, simpleType, complexType, group, attributeGroup, element, attribute or notation")
    elif "sequence" == tag:
        allowed_tags = ["annotation", "element", "group", "choice", "sequence", "any"]
        if False in [child.tag.split("}")[-1] in allowed_tags for child in element.findall("*")]:
            raise Exception("Invalid XSD file: sequence should only contain annotation, element, group, choice, sequence or any")
    elif "simpleContent" == tag:
        allowed_tags = ["annotation", "restriction", "extension"]
        if False in [child.tag.split("}")[-1] in allowed_tags for child in element.findall("*")]:
            raise Exception("Invalid XSD file: simpleContent should only contain annotation, restriction or extension")
    elif "simpleType" == tag:
        allowed_tags = ["annotation", "restriction", "list", "union"]
        if False in [child.tag.split("}")[-1] in allowed_tags for child in element.findall("*")]:
            raise Exception("Invalid XSD file: simpleType should only contain annotation, restriction, list or union")

def built_in_types():
    """
    A function return a list of built-in XSD types.
    """
    return ['string', 'normalizedString', 'token', 'base64Binary', 'hexBinary', 'integer', 'positiveInteger', 'negativeInteger', 
        'nonNegativeInteger', 'nonPositiveInteger', 'long', 'unsignedLong', 'int', 'unsignedInt', 'short', 'unsignedShort', 
        'byte', 'unsignedByte', 'decimal', 'float', 'double', 'boolean', 'duration', 'dateTime', 'date', 'time', 'gYear', 
        'gYearMonth', 'gMonth', 'gMonthDay', 'gDay', 'Name', 'QName', 'NCName', 'anyURI', 'language', 'ID', 'IDREF', 
        'IDREFS', 'ENTITY', 'ENTITIES', 'NOTATION', 'NMTOKEN', 'NMTOKENS', 'anyType', 'anySimpleType', 'dateTimeStamp',
        'IDREF', 'yearMonthDuration', 'dayTimeDuration']

def create_formatted_label(name, custom_abbreviations=None):
    """Create a human-readable label from a camelCase or PascalCase string
    
    Args:
        name: The string to format
        custom_abbreviations: Optional set of custom abbreviations to keep uppercase
    """
    if not name:
        return name
        
    known_abbreviations = {
        "ASAP", # As Soon As Possible
        "FYI", # For Your Information
        "BRB", # Be Right Back
        "DIY", # Do It Yourself
        "ETA", # Estimated Time of Arrival
        "FAQ", # Frequently Asked Questions
        "TBA", # To Be Announced
        "RSVP", # Répondez S'il Vous Plaît (Please Respond)
        "TBD", # To Be Determined
        "AKA", # Also Known As
        "DOB", # Date Of Birth
        "EOD", # End Of Day
        "HR",# Human Resources
        "IT",# Information Technology
        "PTO", # Paid Time Off
        "CEO", # Chief Executive Officer
        "CFO", # Chief Financial Officer
        "COO", # Chief Operating Officer
        "CTO", # Chief Technology Officer
        "KPI", # Key Performance Indicator
        "ROI", # Return On Investment
        "SaaS", # Software as a Service
        "B2B", # Business to Business
        "B2C", # Business to Consumer
        "CRM", # Customer Relationship Management
        "ERP", # Enterprise Resource Planning
        "IPO", # Initial Public Offering
        "MVP", # Minimum Viable Product
        "P&L", # Profit and Loss
        "SWOT", # Strengths, Weaknesses, Opportunities, Threats
        "ATEX",
        "SKU",
        "US",
        "ID"
    }
    
    # Add custom abbreviations if provided
    if custom_abbreviations:
        known_abbreviations.update(custom_abbreviations)
    
    # Replace underscores with spaces first
    name = name.replace('_', ' ')
    
    words = []
    # If the name ends with "Type", remove it and add "Type of" to the words list, but only if the name is not exactly "Type"
    if name.endswith("Type") and len(name) > 4:
        name = name[:-4].strip()
        words.append("Type")
        words.append("of")
        
    current_word = ''
    
    i = 0
    while i < len(name):
        char = name[i]
        if char.isupper():
            # Check if it's part of a known abbreviation
            for abbrev in sorted(known_abbreviations, key=len, reverse=True):
                if name[i:].startswith(abbrev):
                    if current_word:
                        words.append(current_word)
                    words.append(abbrev)  # Keep abbreviation as one word
                    current_word = ''
                    i += len(abbrev)
                    break
            else:  # No abbreviation found
                if current_word:
                    words.append(current_word)
                current_word = char
                i += 1
        elif char == ' ':
            if current_word:
                words.append(current_word)
            current_word = ''
            i += 1
        else:
            current_word += char
            i += 1
    
    if current_word:
        words.append(current_word)
    
    # Format each word
    formatted_words = []
    for word in words:
        if word in known_abbreviations:
            formatted_words.append(word)  # Keep abbreviation as is
        else:
            if len(formatted_words) == 0:
                # Capitalize first letter, keep rest in original case (only for the first word)
                formatted_words.append(word[0].upper() + word[1:] if word else '')
            else:
                formatted_words.append(word[0].lower() + word[1:] if word else '')
    
    result = ' '.join(formatted_words)
    # Remove any multiple spaces and ensure proper spacing after 'has'
    return f"{result.strip()}"

def create_property_iri_suffix(element_name, activate_has_prefix=False):
    """
    Create a property IRI suffix from an element name.

    Args:
        element_name: The name of the element
        activate_has_prefix: If True, prefix the IRI with 'has'
        
    Returns:
        The suffix for the property IRI
    """
    if not element_name:
        return None
        
    if activate_has_prefix:
        return f"has{element_name[0].upper() + element_name[1:]}"
    
    return f"{element_name[0].lower() + element_name[1:]}"

def load_abbreviations_from_file(file_path):
    """
    Load abbreviations from a file, one abbreviation per line.
    
    Args:
        file_path: Path to the file containing abbreviations
        
    Returns:
        A set of abbreviations
    """
    if not file_path or not os.path.exists(file_path):
        return set()
        
    abbreviations = set()
    try:
        with open(file_path, 'r') as f:
            for line in f:
                # Remove whitespace and add non-empty lines to set
                abbr = line.strip()
                if abbr:
                    abbreviations.add(abbr)
        return abbreviations
    except Exception as e:
        print(f"Error loading abbreviations file: {e}")
        return set()