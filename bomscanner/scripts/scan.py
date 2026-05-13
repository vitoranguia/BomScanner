"""Scan project dependencies against local NVD JSON feeds.

Only supports `package==version` entries in requirements and simple pom artifactId->version mapping.
"""
import json
import os
from glob import glob
import xml.etree.ElementTree as ET
from pathlib import Path

# Project root: two levels up from this script (bomscanner/scripts/.. -> project)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = str(PROJECT_ROOT / "data")


def read_requirements(path):
    reqs = {}
    if not os.path.exists(path):
        return reqs
    with open(path, "r", encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln or ln.startswith("#"):
                continue
            if "==" in ln:
                pkg, ver = ln.split("==", 1)
                reqs[pkg.strip().lower()] = ver.strip()
    return reqs


def read_pom(path):
    deps = {}
    if not os.path.exists(path):
        return deps
    try:
        tree = ET.parse(path)
        root = tree.getroot()
    except Exception:
        return deps
    ns = ''
    if root.tag.startswith('{'):
        ns = root.tag.split('}')[0] + '}'
    for dep in root.findall('.//{}dependency'.format(ns)):
        aid = dep.find('{}artifactId'.format(ns))
        ver = dep.find('{}version'.format(ns))
        if aid is not None and ver is not None:
            deps[aid.text.strip().lower()] = ver.text.strip()
    return deps


def match_versions(req_ver, cpe_ver):
    if not req_ver:
        return False
    if req_ver == cpe_ver:
        return True
    if '-' in req_ver and ':' in cpe_ver:
        if req_ver.replace('-', ':') == cpe_ver:
            return True
        left_req = req_ver.split('-', 1)[0]
        left_cpe = cpe_ver.split(':', 1)[0]
        right_req = req_ver.split('-', 1)[1]
        right_cpe = cpe_ver.split(':', 1)[1]
        if left_req == left_cpe and right_req == right_cpe:
            return True
    if ':' in cpe_ver and '-' in req_ver:
        if cpe_ver.replace(':', '-') == req_ver:
            return True
    return False


def find_matches(requirements):
    matches = []
    for jf in glob(os.path.join(DATA_DIR, "*.json")):
        try:
            with open(jf, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue
        vulns = data.get("vulnerabilities") or []
        for v in vulns:
            cve = v.get("cve", {})
            published = cve.get("published", "")
            cve_id = cve.get("id", "")
            vulnStatus = cve.get("vulnStatus", "")
            descs = cve.get("descriptions", [])
            en_desc = ""
            for d in descs:
                if d.get("lang") == "en":
                    en_desc = d.get("value", "")
                    break
            baseSeverity = ""
            metrics = cve.get("metrics", {})
            cvss2 = metrics.get("cvssMetricV2") or metrics.get("cvssMetricV2")
            if cvss2 and isinstance(cvss2, list) and len(cvss2) > 0:
                baseSeverity = cvss2[0].get("baseSeverity", "")
            configs = cve.get("configurations", [])
            for cfg in configs:
                nodes = cfg.get("nodes", [])
                for node in nodes:
                    for cm in node.get("cpeMatch", []) or []:
                        criteria = cm.get("criteria", "")
                        if not criteria:
                            continue
                        parts = criteria.split(":")
                        if len(parts) >= 6:
                            product = parts[4].lower()
                            version = parts[5]
                            if product in requirements:
                                req_ver = requirements[product]
                                if match_versions(req_ver, version):
                                    matches.append((published, product, req_ver, cve.get("id", ""), vulnStatus, en_desc, baseSeverity))
    return matches


def run_scan_for_requirements(path):
    reqs = read_requirements(path)
    return find_matches(reqs)


def run_scan_for_pom(path):
    reqs = read_pom(path)
    return find_matches(reqs)


if __name__ == '__main__':
    import sys
    arg = sys.argv[1] if len(sys.argv) > 1 else 'requirements.txt'
    if arg.endswith('.xml'):
        matches = run_scan_for_pom(arg)
    else:
        matches = run_scan_for_requirements(arg)
    import json
    # write results to nvd_log.json at project root
    out_path = Path(__file__).resolve().parents[2] / 'nvd_log.json'
    try:
        with open(out_path, 'w', encoding='utf-8') as out_f:
            json.dump(matches, out_f, indent=2)
        print(f"Wrote {out_path}")
    except Exception as e:
        print(f"Error writing log: {e}")
