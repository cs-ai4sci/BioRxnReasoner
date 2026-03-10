

import argparse
import json
import os
import csv
from typing import Any, Dict, List, Tuple, Optional
from collections import OrderedDict, defaultdict


def safe_list(x):
    return x if isinstance(x, list) else []


def flatten_molecules(top: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    top["molecules"] looks like:
      [
        {"molecules": [ {bbox, score, smiles, molfile, ...}, ... ] }
      ]
    """
    out = []
    for blk in safe_list(top.get("molecules")):
        if isinstance(blk, dict) and isinstance(blk.get("molecules"), list):
            for m in blk["molecules"]:
                if isinstance(m, dict):
                    out.append(m)
    return out


def flatten_reactions(top: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    top["reactions"] looks like:
      [
        {
          "figure": "...",
          "reactions": [
            { "reactants": [...], "products": [...], "conditions": [...] , ... },
            ...
          ]
        }
      ]
    """
    out = []
    for figblk in safe_list(top.get("reactions")):
        if isinstance(figblk, dict):
            for rxn in safe_list(figblk.get("reactions")):
                if isinstance(rxn, dict):
                    out.append(rxn)
    return out


def flatten_coref_blocks(top: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    top["corefs"] typically looks like:
      [
        {
          "bboxes": [ {...}, {...}, ... ],
          "corefs": [ [i, j], [k, l], ... ]
        }
      ]
    """
    out = []
    for blk in safe_list(top.get("corefs")):
        if isinstance(blk, dict):
            out.append(blk)
    return out


def ensure_out_dir(p: str):
    os.makedirs(p, exist_ok=True)


def stable_mol_id_map(smiles_list: List[str]) -> Dict[str, str]:
    """
    Given a list of smiles (may contain duplicates), create stable mol_id mapping by first occurrence.
    """
    mapping = OrderedDict()
    idx = 1
    for s in smiles_list:
        if not s:
            continue
        if s not in mapping:
            mapping[s] = f"M{idx}"
            idx += 1
    return dict(mapping)


def extract_smiles_from_entries(entries: List[Dict[str, Any]]) -> List[str]:
    smiles = []
    for e in entries:
        if isinstance(e, dict):
            s = e.get("smiles")
            if isinstance(s, str) and s.strip():
                smiles.append(s.strip())
    return smiles


def extract_conditions_text(entries: List[Dict[str, Any]]) -> List[str]:
    """
    conditions entry often has 'text' field (category like [Idt]).
    """
    out = []
    for e in entries:
        if isinstance(e, dict):
            t = e.get("text")
            if isinstance(t, str) and t.strip():
                out.append(t.strip())
    return out


def build_label_to_smiles_from_corefs(coref_blocks: List[Dict[str, Any]]) -> Tuple[List[Tuple[str, str]], List[str], List[Tuple[int, int]]]:
    """
    Try to infer label_to_smiles mapping from coreference pairs.
    Strategy:
      - nodes = coref_block["bboxes"]
      - each node may have fields: category, text (labels), smiles (molecules)
      - coref pairs link indices in nodes
      - if one node has text and the other has smiles => label_to_smiles
    Returns:
      label_to_smiles_pairs: List[(label_text, smiles)]
      label_texts: all unique label texts seen (from nodes)
      coref_pairs_raw: List[(i, j)] raw index pairs
    """
    label_to_smiles_pairs = []
    label_texts = []
    coref_pairs_raw = []

    seen_label_text = set()
    seen_pairs = set()

    for blk in coref_blocks:
        nodes = safe_list(blk.get("bboxes"))
        pairs = safe_list(blk.get("corefs"))

        # collect label_texts from nodes
        for n in nodes:
            if isinstance(n, dict):
                t = n.get("text")
                if isinstance(t, str) and t.strip():
                    tt = t.strip()
                    if tt not in seen_label_text:
                        label_texts.append(tt)
                        seen_label_text.add(tt)

        # collect pairs
        for p in pairs:
            if isinstance(p, list) and len(p) == 2 and all(isinstance(x, int) for x in p):
                i, j = p[0], p[1]
                coref_pairs_raw.append((i, j))

                if 0 <= i < len(nodes) and 0 <= j < len(nodes):
                    a = nodes[i] if isinstance(nodes[i], dict) else {}
                    b = nodes[j] if isinstance(nodes[j], dict) else {}

                    a_text = a.get("text") if isinstance(a.get("text"), str) else None
                    b_text = b.get("text") if isinstance(b.get("text"), str) else None
                    a_smiles = a.get("smiles") if isinstance(a.get("smiles"), str) else None
                    b_smiles = b.get("smiles") if isinstance(b.get("smiles"), str) else None

                    # label-text <-> smiles
                    if a_text and b_smiles:
                        key = (a_text.strip(), b_smiles.strip())
                        if key not in seen_pairs:
                            label_to_smiles_pairs.append(key)
                            seen_pairs.add(key)
                    if b_text and a_smiles:
                        key = (b_text.strip(), a_smiles.strip())
                        if key not in seen_pairs:
                            label_to_smiles_pairs.append(key)
                            seen_pairs.add(key)

    return label_to_smiles_pairs, label_texts, coref_pairs_raw


def write_csv(path: str, headers: List[str], rows: List[Dict[str, Any]]):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for r in rows:
            w.writerow({h: r.get(h, "") for h in headers})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="output JSON (result.json)")
    ap.add_argument("--out_dir", default="out", help="output directory")
    args = ap.parse_args()

    ensure_out_dir(args.out_dir)

    with open(args.input, "r", encoding="utf-8") as f:
        top = json.load(f)

    image_id = top.get("image_id") or top.get("image") or "unknown"

    # -------- molecules --------
    mol_objs = flatten_molecules(top)
    mol_smiles_all = extract_smiles_from_entries(mol_objs)

    # also include smiles appearing inside reactions (sometimes molecules list is incomplete)
    rxn_objs = flatten_reactions(top)
    for rxn in rxn_objs:
        mol_smiles_all += extract_smiles_from_entries(safe_list(rxn.get("reactants")))
        mol_smiles_all += extract_smiles_from_entries(safe_list(rxn.get("products")))

    mol_id_map = stable_mol_id_map(mol_smiles_all)  # smiles -> mol_id

    molecules_csv_rows = []
    # Keep optional "source": where it came from (molecules/reactions/corefs)
    # Here we emit one row per unique smiles
    for smiles, mol_id in mol_id_map.items():
        molecules_csv_rows.append({
            "image_id": image_id,
            "mol_id": mol_id,
            "smiles": smiles,
            "source": "dedup_union(molecules+reactions)"  # optional but useful
        })

    # -------- reactions --------
    reactions_csv_rows = []
    for idx, rxn in enumerate(rxn_objs, start=1):
        reactants = safe_list(rxn.get("reactants"))
        products = safe_list(rxn.get("products"))
        conditions = safe_list(rxn.get("conditions"))

        reactant_smiles = [s for s in extract_smiles_from_entries(reactants) if s]
        product_smiles = [s for s in extract_smiles_from_entries(products) if s]
        conditions_text = extract_conditions_text(conditions)

        # optional: reaction_smiles
        # join lists with '.' to align with common reaction-smiles style
        rxn_smiles = f"{'.'.join(reactant_smiles)}>>{'.'.join(product_smiles)}"

        reactions_csv_rows.append({
            "image_id": image_id,
            "rxn_id": f"R{idx}",
            "reactant_smiles": "|".join(reactant_smiles),
            "product_smiles": "|".join(product_smiles),
            "conditions_text": " ; ".join(conditions_text),
            "reaction_smiles": rxn_smiles,  # optional (kept)
        })

    # -------- corefs / labels (optional kept) --------
    coref_blocks = flatten_coref_blocks(top)
    label_to_smiles_pairs, label_texts, coref_pairs_raw = build_label_to_smiles_from_corefs(coref_blocks)

    # coref_pairs (optional kept): map to mol_id if smiles exists, else keep raw indices
    # We output raw indices too, because sometimes nodes are text-only.
    corefs_csv_rows = []
    for (i, j) in coref_pairs_raw:
        corefs_csv_rows.append({
            "image_id": image_id,
            "i": i,
            "j": j,
        })

    label_to_smiles_csv_rows = []
    for (label, smiles) in label_to_smiles_pairs:
        label_to_smiles_csv_rows.append({
            "image_id": image_id,
            "label_text": label,
            "smiles": smiles,
            "mol_id": mol_id_map.get(smiles, ""),  # optional convenience
        })

    # -------- simplified.json (keep all optionals) --------
    simplified = {
        "image_id": image_id,
        "num_molecules": len(mol_id_map),
        "num_reactions": len(rxn_objs),

        # molecule table (minimal but sufficient for QA/graph)
        "molecules": [
            {"mol_id": mol_id_map[s], "smiles": s, "source": "dedup_union(molecules+reactions)"}
            for s in mol_id_map
        ],

        # reaction table (keep optional reaction_smiles)
        "reactions": [
            {
                "rxn_id": f"R{idx}",
                "reactant_smiles": extract_smiles_from_entries(safe_list(r.get("reactants"))),
                "product_smiles": extract_smiles_from_entries(safe_list(r.get("products"))),
                "conditions_text": extract_conditions_text(safe_list(r.get("conditions"))),
                "reaction_smiles": f"{'.'.join(extract_smiles_from_entries(safe_list(r.get('reactants'))))}>>{'.'.join(extract_smiles_from_entries(safe_list(r.get('products'))))}"
            }
            for idx, r in enumerate(rxn_objs, start=1)
        ],

        # coref optionals kept
        "coref_pairs_raw": coref_pairs_raw,   # (i, j) in coref nodes list
        "label_texts": label_texts,           # all texts seen in coref nodes
        "label_to_smiles": [
            {"label_text": label, "smiles": smiles, "mol_id": mol_id_map.get(smiles, "")}
            for (label, smiles) in label_to_smiles_pairs
        ],
    }

    # write outputs
    with open(os.path.join(args.out_dir, "simplified.json"), "w", encoding="utf-8") as f:
        json.dump(simplified, f, ensure_ascii=False, indent=2)

    write_csv(
        os.path.join(args.out_dir, "molecules.csv"),
        headers=["image_id", "mol_id", "smiles", "source"],
        rows=molecules_csv_rows
    )

    write_csv(
        os.path.join(args.out_dir, "reactions.csv"),
        headers=["image_id", "rxn_id", "reactant_smiles", "product_smiles", "conditions_text", "reaction_smiles"],
        rows=reactions_csv_rows
    )

    write_csv(
        os.path.join(args.out_dir, "corefs.csv"),
        headers=["image_id", "i", "j"],
        rows=corefs_csv_rows
    )

    write_csv(
        os.path.join(args.out_dir, "label_to_smiles.csv"),
        headers=["image_id", "label_text", "smiles", "mol_id"],
        rows=label_to_smiles_csv_rows
    )

    print("Done. Wrote:")
    print(" - simplified.json")
    print(" - molecules.csv")
    print(" - reactions.csv")
    print(" - corefs.csv")
    print(" - label_to_smiles.csv")


if __name__ == "__main__":
    main()
