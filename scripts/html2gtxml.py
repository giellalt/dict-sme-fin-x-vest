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


def clean_lemma_text(text: str):
    """Remove ´, ~, text within parentheses and trailing/leading whitespace"""
    return re.sub("´|~|[(][^)]*[)]", "", text).strip()


def clean_content_text(text: str):
    """Remove ´, trailing/leading whitespace and trailing commas."""
    return re.sub(",$", "", text.replace("´", "").strip())


def insert_lemmas(lemmaList: list, lemmaText: str):
    """Split lemma text and insert lemmas into lemma list"""
    lemmas = re.split(', | ~ ', lemmaText)
    lemmaList.extend([clean_lemma_text(lemma) for lemma in lemmas])


def create_lemma_list(tree):
    lemmaList = []

    lemmas = tree.xpath("strong")
    for lemma in lemmas:
        insert_lemmas(lemmaList, lemma.text)
    
    # Remove empty lemmas
    lemmaList = [lemma for lemma in lemmaList if lemma != ""]

    return lemmaList

def extract_translations(mg):
    ts = []
    geo = gramm = restr = None
    for t in mg.split(","):
        t = t.strip()
        # Look for and eat country
        if match := re.match("^[(](R|S|N)[)]", t):
            geo = re.sub("[()]", "", match.group(0))
            t = re.sub("^[(](R|S|N)[)]", "", t)
        # Remove POS or similar
        t = re.sub("^[(][^)]*[.][)]", "", t).strip()
        # Look for and eat grammar info
        if match := re.match("^[(][^)]*[)]", t):
            gramm = re.sub("[()]", "", match.group(0))
            t = re.sub("^[(][^)]*[)]", "", t)
        # Extract text before parenthesis and add as t
        ts.append(clean_content_text(re.match("^[^(]*", t).group(0)))
        t = re.sub("^[^(]*", "", t)
        # Look for and save restr
        if match := re.match("^[(].*", t):
            restr = re.sub("[()]", "", match.group(0))
    
    return (ts, geo, gramm, restr)

def extract_examples(mg):
    xgs = []
    x = xt = None
    for xg in mg.split("<em>"):
        if xg.strip() == "":
            continue
        # Look for and eat example
        if match := re.match("^.*</em>", xg):
            x = clean_content_text(re.sub("<[^>]*>", "", match.group(0)))
            xg = re.sub("^.*</em>", "", xg)
        # Save example translation
        xt = clean_content_text(xg)
        xgs.append({
            "x": x,
            "xt": xt,
        })
        x = xt = None

    return xgs

def extract_translations_and_examples(line):
    # Extract translation and example part
    tr_and_ex = re.sub("^.*</strong>", "", line).replace("</p>", "").strip()
    mgs = []
    # Split by ';', but consider that sometimes ',' is instead used before <em>
    for mg in re.split(";|, <|  <", tr_and_ex):
        if mg.startswith("em>"):
            mg = "<" + mg
        if mg.strip().startswith("<em>"):
            # Treat as examples connected to previous mg
            xgs = extract_examples(mg)

            try:
                last_mg = mgs[-1]
                if last_mg["xgs"] is not None:
                    last_mg["xgs"].extend(xgs)
                else:
                    last_mg["xgs"] = xgs
                mgs[-1] = last_mg
            except IndexError:
                print(f"no corresponding mg for {xgs}")
        else:
            # Treat as translation
            (ts, geo, gramm, restr) = extract_translations(mg)

            mgs.append({
                "ts": ts,
                "geo": geo,
                "gramm": gramm,
                "restr": restr,
                "xgs": None
            })
    
    return(mgs)


def add_entry(root, lemma: str, translations_and_examples: list):
    """Create xml nodes for dictionary entry and insert into tree"""
    e = SubElement(root, "e")
    
    lg = SubElement(e, "lg")
    l = SubElement(lg, "l")
    l.text = lemma

    for mg_dict in translations_and_examples:
        mg = SubElement(e, "mg")
        tg = SubElement(mg, "tg")
        tg.set('{http://www.w3.org/XML/1998/namespace}lang', "fin")
        if mg_dict["restr"] is not None:
            re = SubElement(mg, "re")
            re.text = mg_dict["restr"]
        if mg_dict["geo"] is not None:
            geo = SubElement(mg, "geo")
            geo.text = mg_dict["geo"]
        if mg_dict["gramm"] is not None:
            gramm = SubElement(mg, "gramm")
            gramm.text = mg_dict["gramm"]
        for t_text in mg_dict["ts"]:
            t = SubElement(tg, "t")
            t.text = t_text
        if mg_dict["xgs"] is not None:
            for ex in mg_dict["xgs"]:
                xg = SubElement(mg, "xg")
                x = SubElement(xg, "x")
                x.text = ex["x"]
                xt = SubElement(xg, "xt")
                xt.text = ex["xt"]

            


def add_entries(root: Element, line: str):
    tree = fromstring(line)
    lemmaList = create_lemma_list(tree)
    translations_and_examples = extract_translations_and_examples(line)
    for lemma in lemmaList:
        add_entry(root, lemma, translations_and_examples)


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
