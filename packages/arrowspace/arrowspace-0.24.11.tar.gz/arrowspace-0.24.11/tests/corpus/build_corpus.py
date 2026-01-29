"""
Integrate the CVE dataset and tne CWE vocabulary

CWE™ is free to use by any organization or individual for any research, development, and/or commercial purposes,
 per these CWE Terms of Use. Accordingly, The MITRE Corporation hereby grants you a non-exclusive, royalty-free license
 to use CWE for research, development, and commercial purposes. Any copy you make for such purposes is authorized on
 the condition that you reproduce MITRE's copyright designation and this license in any such copy. CWE is a trademark
 of The MITRE Corporation. Please contact cwe@mitre.org if you require further clarification on this issue.

DISCLAIMERS
By accessing information through this site you (as “the user”) hereby agrees the site and the information is provided on
 an “as is” basis only without warranty of any kind, express or implied, including but not limited to implied warranties
 of merchantability, availability, accuracy, noninfringement, or fitness for a particular purpose. Use of this site and
 the information is at the user's own risk. The user shall comply with all applicable laws, rules, and regulations, and
 the data source's restrictions, when using the site.

By contributing information to this site you (as “the contributor”) hereby represents and warrants the contributor has
 obtained all necessary permissions from copyright holders and other third parties to allow the contributor to contribute,
 and this site to host and display, the information and any such contribution, hosting, and displaying will not violate any
 law, rule, or regulation. Additionally, the contributor hereby grants all users of such information a perpetual, worldwide,
 non-exclusive, no-charge, royalty-free, irrevocable license to reproduce, prepare derivative works of, publicly display,
 publicly perform, sublicense, and distribute such information and all derivative works.

The MITRE Corporation expressly disclaims any liability for any damages arising from the contributor's contribution of
 such information, the user's use of the site or such information, and The MITRE Corporation's hosting the tool and
 displaying the information. The foregoing disclaimer specifically includes but is not limited to general, consequential,
 indirect, incidental, exemplary, or special or punitive damages (including but not limited to loss of income, program
 interruption, loss of information, or other pecuniary loss) arising out of use of this information, no matter the cause
 of action, even if The MITRE Corporation has been advised of the possibility of such damages.
"""
import os, re, json, glob, argparse
from urllib.request import urlopen

CWE_GLOSSARY_URL = "https://cwe.mitre.org/documents/glossary/index.html"

# ============================================================================
# Data Loading
# ============================================================================
def iter_cve_json(root_dir, start=2009, end=2025):
    """Iterate over CVE JSON files in date range."""
    for path in glob.glob(os.path.join(root_dir, "**", "*.json"), recursive=True):
        if any(str(y) in path for y in range(start, end+1)):
            with open(path, "r", encoding="utf-8") as f:
                try:
                    yield path, json.load(f)
                except Exception:
                    continue

def extract_text(j):
    """Extract searchable text from CVE JSON."""
    cve_id = j.get("cveMetadata", {}).get("cveId", "")
    cna = j.get("containers", {}).get("cna", {})
    title = cna.get("title", "") or ""

    # Descriptions
    descs = []
    for d in cna.get("descriptions", []) or []:
        if isinstance(d, dict):
            val = d.get("value") or ""
            if val:
                descs.append(val)
    description = " ".join(descs)

    # CWE IDs
    cwes = []
    for pt in cna.get("problemTypes", []) or []:
        for d in pt.get("descriptions", []) or []:
            cwe = d.get("cweId")
            if cwe:
                cwes.append(cwe)
    cwe_str = " ".join(cwes)

    # CVSS vector
    cvss_vec = ""
    for m in cna.get("metrics", []) or []:
        v31 = m.get("cvssV3_1")
        if isinstance(v31, dict):
            vs = v31.get("vectorString")
            if vs:
                cvss_vec = vs
                break

    # Affected products
    affected = cna.get("affected", []) or []
    products = []
    for a in affected:
        vendor = a.get("vendor") or ""
        product = a.get("product") or ""
        if vendor or product:
            products.append(f"{vendor} {product}".strip())
    prod_str = " ".join(products)

    text = " | ".join(
        [s for s in [cve_id, title, description, cwe_str, cvss_vec, prod_str] if s]
    )
    return cve_id or "(unknown)", title or "(no title)", text

def fetch_cwe_glossary_text():
    html = urlopen(CWE_GLOSSARY_URL).read().decode("utf-8", errors="ignore")
    # Page has a consistent “## Term Definition ... ## NextTerm ...” shape in the text view
    # We extract pairs conservatively; you can tighten the regex if needed.
    text = re.sub(r"<[^>]+>", " ", html)  # strip tags (rough but works)
    text = re.sub(r"\s+", " ", text).strip()

    # Find "## TERM definition" blocks
    # This relies on the observed structure of the page content.
    blocks = re.findall(r"##\s*([^#]+?)\s+(.+?)(?=\s+##\s*[^#]+?\s+|$)", text)
    out = []
    breakpoint()
    for term, definition in blocks:
        term = term.strip()
        definition = definition.strip()
        if term and definition and len(term) < 80:
            out.append((term, definition))
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cve_root", required=True, help="Root directory with CVE JSON files")
    ap.add_argument("--out_dir", default="data_out")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    # 1) CWE glossary
    glossary = fetch_cwe_glossary_text()
    glossary_txt = os.path.join(args.out_dir, "cwe_glossary.txt")
    with open(glossary_txt, "w", encoding="utf-8") as f:
        for term, definition in glossary:
            f.write(f"{term}: {definition}\n")

    # # 2) Training JSONL (CVE docs + glossary docs)
    # train_jsonl = os.path.join(args.out_dir, "train.jsonl")
    # with open(train_jsonl, "w", encoding="utf-8") as f:
    #     for _, j in iter_cve_json(args.cve_root):
    #         text = extract_text(j)
    #         if text:
    #             f.write(json.dumps({"text": text}) + "\n")
    #     for term, definition in glossary:
    #         f.write(json.dumps({"text": f"{term}: {definition}"}) + "\n")

    print("Wrote:", glossary_txt)
    # print("Wrote:", train_jsonl)

if __name__ == "__main__":
    main()
