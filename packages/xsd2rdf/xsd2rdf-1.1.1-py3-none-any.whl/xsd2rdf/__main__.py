import argparse
import os
import sys
import glob
from .XSDtoRDF import XSDtoRDF


def define_args():
    parser = argparse.ArgumentParser(description='Convert XSD to RDF formats (SHACL, OWL, SKOS)')

    parser.add_argument("--XSD_FILE", "-x", type=str, 
                        help="XSD file to be converted into RDF")
    parser.add_argument("--OUTPUT_DIR", "-o", type=str, 
                        help="Output directory for generated files (default: same as XSD file)")
    parser.add_argument("--ABBREVIATIONS_FILE", "-a", type=str, 
                        help="File containing custom abbreviations, one per line")
    parser.add_argument("--FOLDER", "-f", type=str, help="Folder containing non related XSD files to be converted")
    parser.add_argument("--debug", "-d", action="store_true", 
                        help="Enable debug output")
    parser.add_argument("--namespaced_concepts", "-nc", action="store_true",
                        help="Use namespaced IRIs for SKOS concepts (targetnamespace/concepts/conceptschemename/conceptname) instead of flat IRIs (targetnamespace/concepts/conceptschemename_conceptname)")
    parser.add_argument("--has_prefix_for_properties", "-hp", action="store_true",
                        help="Add 'has' as prefix for property IRIs")
    return parser.parse_args()

def main():
    args = define_args()
    
    if args.XSD_FILE:

        if not os.path.isfile(args.XSD_FILE):
            print(f"Error: XSD file {args.XSD_FILE} not found")
            sys.exit(1)
            
        if args.ABBREVIATIONS_FILE and not os.path.exists(args.ABBREVIATIONS_FILE):
            print(f"Warning: Abbreviations file {args.ABBREVIATIONS_FILE} not found. Using default abbreviations.")
            args.ABBREVIATIONS_FILE = None
            
        # If output directory is not provided, use the directory of the XSD file
        if not args.OUTPUT_DIR:
            output_dir = os.path.dirname(os.path.abspath(args.XSD_FILE))
            # If the dirname is empty (running in same dir as file), use current directory
            if not args.OUTPUT_DIR:
                output_dir = os.getcwd()
        else:
            output_dir = os.path.abspath(args.OUTPUT_DIR)

        # Create output directory if it doesn't exist
        if output_dir and not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        print(f"Converting {args.XSD_FILE} to SHACL, SKOS and OWL...")
        
        xsd2rdf = XSDtoRDF(args.ABBREVIATIONS_FILE, debug=args.debug, namespaced_concepts=args.namespaced_concepts, 
                           has_prefix_for_properties=args.has_prefix_for_properties)
        xsd2rdf.evaluate_file(args.XSD_FILE, output_dir)
        
        print(f"All conversions completed successfully! Output files saved in: {output_dir}")

    elif args.FOLDER:
        if not os.path.isdir(args.FOLDER):
            print(f"Error: Folder {args.FOLDER} not found")
            sys.exit(1)

        xsd_files = glob.glob(os.path.join(args.FOLDER, "*.xsd"))
        if not xsd_files:
            print(f"No XSD files found in folder {args.FOLDER}")
            sys.exit(1)

        for xsd_file in xsd_files:
            output_dir = args.OUTPUT_DIR or os.path.dirname(xsd_file)
            if output_dir and not os.path.isdir(output_dir):
                os.makedirs(output_dir)

            file_name = os.path.basename(xsd_file)
            shacl_file = os.path.join(output_dir, file_name + ".shape.ttl")
            print(f"Converting {xsd_file} to SHACL, SKOS and OWL...")
            xsd2rdf = XSDtoRDF(args.ABBREVIATIONS_FILE, debug=args.debug, namespaced_concepts=args.namespaced_concepts, 
                           has_prefix_for_properties=args.has_prefix_for_properties)
            xsd2rdf.evaluate_file(xsd_file, output_dir)

        print(f"All conversions completed successfully! Output files saved in: {output_dir}")

    else:
        # If no command is provided, show help
        define_args()
        print("Please specify a command. Use --help for more information.")
        sys.exit(1)

if __name__ == "__main__":
    main()
