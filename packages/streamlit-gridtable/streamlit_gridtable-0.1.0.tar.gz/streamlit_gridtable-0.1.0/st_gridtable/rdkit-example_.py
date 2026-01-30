import streamlit as st
import json
import re

from st_gridtable import st_gridtable

import pandas as pd
import os

from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit.Chem.Draw import rdMolDraw2D
from rdkit.Chem import Draw as RDDraw

st.set_page_config(layout="wide")

pattern = re.compile("<\?xml.*\?>")

st.session_state.setdefault("prev_selected_id", None)
st.session_state.setdefault("curr_selected_id", None)


if "cards_data" not in st.session_state:
  st.session_state.cards_data = []

@st.dialog("Record Detail", width="large")
def show_record_dialog(rec: dict):
    def render_image(val):
        if not val:
            return
        s = str(val).strip()
        if s.startswith("<svg"):
            st.image(rec.get("structure_svg"))
            st.markdown(s, unsafe_allow_html=True)
        elif s.startswith("data:image/svg+xml"):
            st.markdown(f"<img src='{s}' style='max-width:100%;height:auto;'/>",
                        unsafe_allow_html=True)
        else:
            st.image(s)

    cols = st.columns([1, 2], gap="small")
    with cols[0]:
        render_image(rec.get("structure_svg"))
    with cols[1]:
        display_cols = ["SMILES", "INCHI", "INCHIKEY","MOLWT","NUM_ATOMS"]
        display_items = {k: rec[k] for k in display_cols if k in rec}
        for k, v in display_items.items():
            st.markdown(f"・ **{k}**: {v}")



def normalize(v):
    if v is None:
        return None
    return json.dumps(v, sort_keys=True, ensure_ascii=False)

def smiles_to_svg(smiles: str, w: int = 110, h: int = 80) -> str:
    if not smiles or Chem is None:
        return f"<svg width=\"{w}\" height=\"{h}\"></svg>"
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return f"<svg width=\"{w}\" height=\"{h}\"></svg>"
        AllChem.Compute2DCoords(mol)
        drawer = rdMolDraw2D.MolDraw2DSVG(w, h)
        drawer.DrawMolecule(mol)
        drawer.FinishDrawing()
        svg = drawer.GetDrawingText()
        svg = re.sub(pattern, '', svg)
        return svg
    except Exception:
        return f"<svg width=\"{w}\" height=\"{h}\"></svg>"

@st.cache_data(show_spinner=False)
def build_df_with_assets(df: pd.DataFrame, w: int = 110, h: int = 80) -> pd.DataFrame:
    svg_list: list[str] = []
    for smi in df["SMILES"].astype(str).fillna(""):
        svg_list.append(smiles_to_svg(smi, w=w, h=h))
    out = df.copy()
    out.insert(0, "structure_svg", svg_list)
    return out


state_key = "table1_prev"
if state_key not in st.session_state:
    st.session_state[state_key] = 0
    # st.session_state[state_key] = None

# st.write(os.listdir())

# selected_row = my_component("World")
df = pd.read_csv("./st_gridtable/frontend/public/smiles.csv")
# df.drop(["PATTERN_FP","CANONICAL_SMILES"], axis=1, inplace=True)
df_with_assets = build_df_with_assets(df, w=200, h=200)
# st.dataframe(df_with_assets)

args = {
    "columns": ["MOLWT", "INCHI", "SMILES"],
    "data": df_with_assets.to_dict(orient="records"),
    "titleKey": "INCHIKEY",
    "imageKey": "structure_svg",
    "badgeKeys": ["NUM_ATOMS"],
    "detailKeys": ["MOLWT", "NUM_ATOMS"],
    "cardSize":200,
    "cardGap":16,
    "fontSize":14,
    "fontColor":"rgba(0, 0, 0, .6)",
    "pageSize":10,
    "pageSizeOptions":[10,20,50,100],
}

ret = st_gridtable(**args, key="cards1")

if isinstance(ret, dict) and ret.get("event") == "card_click":
    rec = ret.get("record") or {}
    curr = ret.get("event_id")
    prev = st.session_state["prev_selected_id"]
    changed = len(rec) >0 and curr != prev
    st.session_state["prev_selected_id"] = curr
    if changed:
        st.session_state["selected_record"] = rec
        show_record_dialog(rec)
