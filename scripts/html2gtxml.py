"""
Convert sme-fin html to GT-style xml.
"""
import argparse
from pathlib import Path
import re

MISSING_DEP_HELP = """
cannot run due to missing dependencies. hint, run:
python -m venv venv && . venv/bin/activate && pip install lxml
...and then try again. (remember to run `deactivate` in the shell when you're done)
"""

try:
    from lxml.etree import Element, SubElement, tostring, fromstring
except ImportError:
    exit(MISSING_DEP_HELP)

def prettyprint(element, **kwargs):
    """Pretty print function for testing"""
    xml = tostring(element, encoding="utf-8", pretty_print=True, **kwargs)
    print(xml.decode(), end='')


def clean_text(text: str):
    """Remove ´, ~, text within parentheses and trailing/leading whitespace"""
    return re.sub("´|~|[(][^)]*[)]", "", text).strip()


def insert_lemmas(lemmaList: list, lemmaText: str):
    """Split lemma text and insert lemmas into lemma list"""
    lemmas = re.split(', | ~ ', lemmaText)
    lemmaList.extend([clean_text(lemma) for lemma in lemmas])


def create_lemma_list(tree):
    lemmaList = []

    lemmas = tree.xpath("strong")
    for lemma in lemmas:
        insert_lemmas(lemmaList, lemma.text)
    
    # Remove empty lemmas
    lemmaList = [lemma for lemma in lemmaList if lemma != ""]

    return lemmaList

def extract_translations_and_examples(tree):
    pass


def add_entry(lemma: str, translations_and_examples):
    pass


def add_entries(root: Element, line: str):
    tree = fromstring(line)
    lemmaList = create_lemma_list(tree)
    translations_and_examples = extract_translations_and_examples(tree)
    for lemma in lemmaList:
        add_entry(lemma, translations_and_examples)


def lines_to_xml_bytestring(lines):
    root = Element("r")

    for line in lines:
        if not line.startswith("<p>"):
            continue
        add_entries(root, line)

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
