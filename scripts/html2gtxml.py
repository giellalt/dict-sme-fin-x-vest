"""
Convert sme-fin html to GT-style xml.
"""
import argparse
from pathlib import Path

MISSING_DEP_HELP = """
cannot run due to missing dependencies. hint, run:
python -m venv venv && . venv/bin/activate && pip install lxml
...and then try again. (remember to run `deactivate` in the shell when you're done)
"""

try:
    from lxml.etree import Element, SubElement, tostring
except ImportError:
    exit(MISSING_DEP_HELP)

def lines_to_xml_bytestring(lines):
    root = Element("r")
    doctype = (
        '<!DOCTYPE r PUBLIC "-//DivvunGiellatekno//DTD '
        'Dictionaries//Multilingual" "../dtd/spasme.dtd">'
    )
    return tostring(root, encoding="utf-8", pretty_print=True, doctype=doctype)

def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputfile")
    parser.add_argument("--outputfile", "-o", type=Path, default="sme-fin.xml")

    return parser.parse_args()


def main(args):
    with open(args.inputfile) as f:
        lines = f.readlines()
    
    xml_bytestring = lines_to_xml_bytestring(lines)

    with open(args.outputfile, "wb") as f:
        f.write(xml_bytestring)


if __name__ == "__main__":
    raise SystemExit(main(parse_args()))
