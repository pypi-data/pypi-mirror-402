# XSD2RDF

[![License](https://img.shields.io/badge/license-EUPL_1.2-blue)](http://data.europa.eu/eli/dec_impl/2017/863/oj)

A tool to convert XML Schema (XSD) files into various RDF formats (SHACL, OWL, SKOS) with integrated validation capabilities.

## Overview

XSD2RDF allows you to convert XML Schema definitions into:

- **SHACL** (Shapes Constraint Language) for RDF data validation
- **OWL** (Web Ontology Language) for ontology representation
- **SKOS** (Simple Knowledge Organization System) for concept schemes and taxonomies

## Features

- Convert XSD to SHACL, OWL, and SKOS based on integrated principles
- SHACL shape constraints are linked to SKOS concept schemes when applicable
- Handle complex XSD structures (choices, unions, complex types, enumerations, etc.)
- SHACL shapes are validated according to SHACL-SHACL

This repository also includes a validation script to check RDF data against the generated SHACL shapes and SKOS concepts.

## Installation

### From PyPI

```bash
pip install xsd2rdf
```

### From Source

```bash
git clone https://github.com/YourUsername/xsd2rdf.git
cd xsd2rdf
python -m pip install poetry
poetry install
```

## Basic Usage

Convert an XSD file to all RDF formats (SHACL, OWL, SKOS):

```bash
python -m xsd2rdf -x path/to/schema.xsd
```

This generates the following files:

- `schema.xsd.shape.ttl` (SHACL shapes)
- `schema.xsd.owl.ttl` (OWL ontology)
- `schema.xsd.*.skos.ttl` (SKOS concept schemes, one file per enumeration)

## Command Line Parameters

- `-x, --XSD_FILE`: XSD file to be converted
- `-f, --FOLDER`: Folder containing non-related XSD files to be converted
- `-o, --OUTPUT_DIR`: Output directory for generated files (default: same as XSD file)
- `-a, --ABBREVIATIONS_FILE`: File containing custom abbreviations, one per line
- `-d, --debug`: Enable debug output
- `-nc, --namespaced-concepts`: Use namespaced IRIs for SKOS concepts

Either -x or -f must be specified, but not both. If both are specified, -x takes precedence.

### SKOS IRI Options

By default, SKOS concept IRIs are created using a flat structure:

```
targetnamespace/concepts/conceptschemename_conceptname
```

With the `--namespaced-concepts` flag, concepts use a hierarchical structure:

```
targetnamespace/concepts/conceptschemename/conceptname
```

## Examples

With custom output directory:

```bash
python -m xsd2rdf  -x path/to/schema.xsd -o output/directory
```

With folder containing multiple unrelated XSD files:

```bash
python -m xsd2rdf -f path/to/folder
```

Using a custom abbreviations file:

```bash
python -m xsd2rdf -x path/to/schema.xsd -a path/to/abbreviations.txt
```

A practical way to generate a list of abbreviations on a Windows machine using Powershell is with this command:

```powershell
 Select-String -Path "c:\Users\mathi\Git\era\xsd2rdf\debug\SFERA_v3.00.xsd" -Pattern "\b[A-Z]{2,}\b" -AllMatches | ForEach-Object { $_.Matches } | ForEach-Object { $_.Value } | Where-Object { $_ -cmatch "^[A-Z]{2,}$" } | Sort-Object -Unique | Where-Object { $_.Length -ge 2 -and $_.Length -le 10 }
```

Using namespaced concept IRIs:

```bash
python -m xsd2rdf -x path/to/schema.xsd --namespaced-concepts
```

The abbreviations file should contain one abbreviation per line. These abbreviations will be preserved as uppercase when creating human-readable labels from camelCase or PascalCase strings.

## Validation

This feature is only available from source as it is meant for development purposes.

Prerequisites:

- Create sample data for validation `schema.xsd.shape.ttl` in the same directory as the xsd file

To validate RDF data against SHACL shapes with SKOS concepts:

```bash
python shacl-validation.py path/to/schema.xsd
```

This result will:

1. Load the data from `schema.xsd.sample.ttl`
2. Include all related SKOS files (`schema.xsd.*.skos.ttl`)
3. Perform validation using the generated SHACL shapes (`schema.xsd.shape.ttl`)
4. Report results in the command line

## Example

Converting an XSD file with enumerations:

```bash
python -m xsd2rdf xsd2rdf -x comparison/enumerations.xsd
```

Validating data using generated shapes and concepts:

```bash
python shacl-validation.py comparison/enumerations.xsd
```

## Wiki Pages
Some [wiki pages](https://gitlab.com/era-europa-eu/public/interoperable-data-programme/era-ontology/xsd2rdf/-/wikis/home) explain the inner workings of the convertor and the list of 
mapping rules implemented within the tool.

## License

[EUPL 1.2](http://data.europa.eu/eli/dec_impl/2017/863/oj)
