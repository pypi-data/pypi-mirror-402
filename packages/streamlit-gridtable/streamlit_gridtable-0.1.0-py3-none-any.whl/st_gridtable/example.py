import streamlit as st
from st_gridtable import st_gridtable
import pandas as pd

st.set_page_config(layout="wide")

if "cards_data" not in st.session_state:
  st.session_state.cards_data = []

@st.dialog("Record Detail", width="large")
def show_record_dialog(rec: dict):
    def render_image(val):
        if not val:
            return
        s = str(val).strip()
        if s.startswith("<svg"):
            st.markdown(s, unsafe_allow_html=True)  # Raw SVG
        elif s.startswith("data:image/svg+xml"):
            st.markdown(f"<img src='{s}' style='max-width:100%;height:auto;'/>",
                        unsafe_allow_html=True)      # data URI SVG
        else:
            st.image(s)      # URL or Binary

    cols = st.columns([1, 2], gap="small")
    with cols[0]:
        render_image(rec.get("image_url"))
    with cols[1]:
        title = rec.get("name") or rec.get("title") or rec.get("id") or "Record"
        st.subheader(title)
        badges = []
        for k in ("types", "dose_form", "category", "tags"):
            v = rec.get(k)
            if v is None: 
                continue
            badges += (v if isinstance(v, list) else [v])
        if badges:
            st.write(" ".join([f"<span style='display:inline-block;padding:2px 8px;border-radius:999px;background:#e3e8f0;margin-right:6px'>{b}</span>" 
                               for b in badges]),
                     unsafe_allow_html=True)

    kv = {k: (", ".join(v) if isinstance(v, list) else v) for k, v in rec.items()}
    df = pd.DataFrame({"Key": list(kv.keys()), "Value": list(kv.values())})
    st.dataframe(df, use_container_width=True)


dummy_data = [
  {
    "name": "Aspirin",
    "image_url": "https://www.ebi.ac.uk/chembl/api/data/image/CHEMBL178234.svg",
    "types": [
      "Analgesic",
      "NSAID"
    ],
    "formula": "C9H8O4",
    "weight": 200.16,
    "source": "DrugBank",
    "dose_form": "Tabletkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk",
    "atc": "N02BA01"
  },
  {
    "name": "Ibuprofen",
    "image_url": "https://www.ebi.ac.uk/chembl/api/data/image/CHEMBL178236.svg",
    "types": [
      "Analgesic",
      "NSAID"
    ],
    "formula": "C13H18O2",
    "weight": 206.28,
    "source": "DrugBankaaaaaaaaaaaaaaaaaaaaaaafjpowjowpwffpwe",
    "dose_form": "Tablet",
    "atc": "M01AE01"
  },
  {
    "name": "Paracetamolfwefwefewwefwefwefw",
    "image_url": "https://www.ebi.ac.uk/chembl/api/data/image/CHEMBL178237.svg",
    "types": [
      "Analgesic",
      "Antipyretic"
    ],
    "formula": "C8H9NO2",
    "weight": 151.16,
    "source": "DrugBank",
    "dose_form": "Tablet",
    "atc": "N02BE01"
  },
  {
    "name": "Amoxicillin",
    "image_url": "https://www.ebi.ac.uk/chembl/api/data/image/CHEMBL178238.svg",
    "types": [
      "Antibiotic",
      "β-lactam"
    ],
    "formula": "C16H19N3O5S",
    "weight": 365.4,
    "source": "DrugBank",
    "dose_form": "Capsule",
    "atc": "J01CA04"
  },
  {
    "name": "Metformin",
    "image_url": "https://www.ebi.ac.uk/chembl/api/data/image/CHEMBL178239.svg",
    "types": [
      "Antidiabetic"
    ],
    "formula": "C4H11N5",
    "weight": 129.16,
    "source": "DrugBank",
    "dose_form": "Tablet",
    "atc": "A10BA02"
  },
  {
    "name": "Atorvastatin",
    "image_url": "https://www.ebi.ac.uk/chembl/api/data/image/CHEMBL178240.svg",
    "types": [
      "Statin"
    ],
    "formula": "C33H35FN2O5",
    "weight": 558.64,
    "source": "DrugBank",
    "dose_form": "Tablet",
    "atc": "C10AA05"
  },
  {
    "name": "Omeprazole",
    "image_url": "https://www.ebi.ac.uk/chembl/api/data/image/CHEMBL178250.svg",
    "types": [
      "PPI"
    ],
    "formula": "C17H19N3O3S",
    "weight": 345.42,
    "source": "DrugBank",
    "dose_form": "Capsule",
    "atc": "A02BC01"
  },
  {
    "name": "Losartan",
    "image_url": "https://www.ebi.ac.uk/chembl/api/data/image/CHEMBL178242.svg",
    "types": [
      "ARB"
    ],
    "formula": "C22H23ClN6O",
    "weight": 422.91,
    "source": "DrugBank",
    "dose_form": "Tablet",
    "atc": "C09CA01"
  },
  {
    "name": "Sertraline",
    "image_url": "https://www.ebi.ac.uk/chembl/api/data/image/CHEMBL178243.svg",
    "types": [
      "SSRI"
    ],
    "formula": "C17H17Cl2N",
    "weight": 306.23,
    "source": "DrugBank",
    "dose_form": "Tablet",
    "atc": "N06AB06"
  },
  {
    "name": "Dexamethasone",
    "image_url": "https://www.ebi.ac.uk/chembl/api/data/image/CHEMBL178245.svg",
    "types": [
      "Corticosteroid"
    ],
    "formula": "C22H29FO5",
    "weight": 392.46,
    "source": "DrugBank",
    "dose_form": "Tablet",
    "atc": "H02AB02"
  },
  {
    "name": "Aspirin",
    "image_url": "https://www.ebi.ac.uk/chembl/api/data/image/CHEMBL178234.svg",
    "types": [
      "Analgesic",
      "NSAID"
    ],
    "formula": "C9H8O4",
    "weight": 200.16,
    "source": "DrugBank",
    "dose_form": "Tabletkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk",
    "atc": "N02BA01"
  },
  {
    "name": "Ibuprofen",
    "image_url": "https://www.ebi.ac.uk/chembl/api/data/image/CHEMBL178236.svg",
    "types": [
      "Analgesic",
      "NSAID"
    ],
    "formula": "C13H18O2",
    "weight": 206.28,
    "source": "DrugBank",
    "dose_form": "Tablet",
    "atc": "M01AE01"
  },
  {
    "name": "Paracetamol",
    "image_url": "https://www.ebi.ac.uk/chembl/api/data/image/CHEMBL178237.svg",
    "types": [
      "Analgesic",
      "Antipyretic"
    ],
    "formula": "C8H9NO2",
    "weight": 151.16,
    "source": "DrugBank",
    "dose_form": "Tablet",
    "atc": "N02BE01"
  },
  {
    "name": "Amoxicillin",
    "image_url": "https://www.ebi.ac.uk/chembl/api/data/image/CHEMBL178238.svg",
    "types": [
      "Antibiotic",
      "β-lactam"
    ],
    "formula": "C16H19N3O5S",
    "weight": 365.4,
    "source": "DrugBank",
    "dose_form": "Capsule",
    "atc": "J01CA04"
  },
  {
    "name": "Metformin",
    "image_url": "https://www.ebi.ac.uk/chembl/api/data/image/CHEMBL178239.svg",
    "types": [
      "Antidiabetic"
    ],
    "formula": "C4H11N5",
    "weight": 129.16,
    "source": "DrugBank",
    "dose_form": "Tablet",
    "atc": "A10BA02"
  },
  {
    "name": "Atorvastatin",
    "image_url": "https://www.ebi.ac.uk/chembl/api/data/image/CHEMBL178240.svg",
    "types": [
      "Statin"
    ],
    "formula": "C33H35FN2O5",
    "weight": 558.64,
    "source": "DrugBank",
    "dose_form": "Tablet",
    "atc": "C10AA05"
  },
  {
    "name": "Omeprazole",
    "image_url": "https://www.ebi.ac.uk/chembl/api/data/image/CHEMBL178250.svg",
    "types": [
      "PPI"
    ],
    "formula": "C17H19N3O3S",
    "weight": 345.42,
    "source": "DrugBank",
    "dose_form": "Capsule",
    "atc": "A02BC01"
  },
  {
    "name": "Losartan",
    "image_url": "https://www.ebi.ac.uk/chembl/api/data/image/CHEMBL178242.svg",
    "types": [
      "ARB"
    ],
    "formula": "C22H23ClN6O",
    "weight": 422.91,
    "source": "DrugBank",
    "dose_form": "Tablet",
    "atc": "C09CA01"
  },
  {
    "name": "Sertraline",
    "image_url": "https://www.ebi.ac.uk/chembl/api/data/image/CHEMBL178243.svg",
    "types": [
      "SSRI"
    ],
    "formula": "C17H17Cl2N",
    "weight": 306.23,
    "source": "DrugBank",
    "dose_form": "Tablet",
    "atc": "N06AB06"
  },
  {
    "name": "Dexamethasone",
    "image_url": "https://www.ebi.ac.uk/chembl/api/data/image/CHEMBL178245.svg",
    "types": [
      "Corticosteroid"
    ],
    "formula": "C22H29FO5",
    "weight": 392.46,
    "source": "DrugBank",
    "dose_form": "Tablet",
    "atc": "H02AB02"
  },
    {
    "name": "Aspirin",
    "image_url": "https://www.ebi.ac.uk/chembl/api/data/image/CHEMBL178234.svg",
    "types": [
      "Analgesic",
      "NSAID"
    ],
    "formula": "C9H8O4",
    "weight": 200.16,
    "source": "DrugBank",
    "dose_form": "Tabletkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk",
    "atc": "N02BA01"
  },
  {
    "name": "Ibuprofen",
    "image_url": "https://www.ebi.ac.uk/chembl/api/data/image/CHEMBL178236.svg",
    "types": [
      "Analgesic",
      "NSAID"
    ],
    "formula": "C13H18O2",
    "weight": 206.28,
    "source": "DrugBank",
    "dose_form": "Tablet",
    "atc": "M01AE01"
  },
  {
    "name": "Paracetamol",
    "image_url": "https://www.ebi.ac.uk/chembl/api/data/image/CHEMBL178237.svg",
    "types": [
      "Analgesic",
      "Antipyretic"
    ],
    "formula": "C8H9NO2",
    "weight": 151.16,
    "source": "DrugBank",
    "dose_form": "Tablet",
    "atc": "N02BE01"
  },
  {
    "name": "Amoxicillin",
    "image_url": "https://www.ebi.ac.uk/chembl/api/data/image/CHEMBL178238.svg",
    "types": [
      "Antibiotic",
      "β-lactam"
    ],
    "formula": "C16H19N3O5S",
    "weight": 365.4,
    "source": "DrugBank",
    "dose_form": "Capsule",
    "atc": "J01CA04"
  },
  {
    "name": "Metformin",
    "image_url": "https://www.ebi.ac.uk/chembl/api/data/image/CHEMBL178239.svg",
    "types": [
      "Antidiabetic"
    ],
    "formula": "C4H11N5",
    "weight": 129.16,
    "source": "DrugBank",
    "dose_form": "Tablet",
    "atc": "A10BA02"
  },
  {
    "name": "Atorvastatin",
    "image_url": "https://www.ebi.ac.uk/chembl/api/data/image/CHEMBL178240.svg",
    "types": [
      "Statin"
    ],
    "formula": "C33H35FN2O5",
    "weight": 558.64,
    "source": "DrugBank",
    "dose_form": "Tablet",
    "atc": "C10AA05"
  },
  {
    "name": "Omeprazole",
    "image_url": "https://www.ebi.ac.uk/chembl/api/data/image/CHEMBL178250.svg",
    "types": [
      "PPI"
    ],
    "formula": "C17H19N3O3S",
    "weight": 345.42,
    "source": "DrugBank",
    "dose_form": "Capsule",
    "atc": "A02BC01"
  },
  {
    "name": "Losartan",
    "image_url": "https://www.ebi.ac.uk/chembl/api/data/image/CHEMBL178242.svg",
    "types": [
      "ARB"
    ],
    "formula": "C22H23ClN6O",
    "weight": 422.91,
    "source": "DrugBank",
    "dose_form": "Tablet",
    "atc": "C09CA01"
  },
  {
    "name": "Sertraline",
    "image_url": "https://www.ebi.ac.uk/chembl/api/data/image/CHEMBL178243.svg",
    "types": [
      "SSRI"
    ],
    "formula": "C17H17Cl2N",
    "weight": 306.23,
    "source": "DrugBank",
    "dose_form": "Tablet",
    "atc": "N06AB06"
  },
  {
    "name": "Dexamethasone",
    "image_url": "https://www.ebi.ac.uk/chembl/api/data/image/CHEMBL178245.svg",
    "types": [
      "Corticosteroid"
    ],
    "formula": "C22H29FO5",
    "weight": 392.46,
    "source": "DrugBank",
    "dose_form": "Tablet",
    "atc": "H02AB02"
  },
    {
    "name": "Aspirin",
    "image_url": "https://www.ebi.ac.uk/chembl/api/data/image/CHEMBL178234.svg",
    "types": [
      "Analgesic",
      "NSAID"
    ],
    "formula": "C9H8O4",
    "weight": 200.16,
    "source": "DrugBank",
    "dose_form": "Tabletkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk",
    "atc": "N02BA01"
  },
  {
    "name": "Ibuprofen",
    "image_url": "https://www.ebi.ac.uk/chembl/api/data/image/CHEMBL178236.svg",
    "types": [
      "Analgesic",
      "NSAID"
    ],
    "formula": "C13H18O2",
    "weight": 206.28,
    "source": "DrugBank",
    "dose_form": "Tablet",
    "atc": "M01AE01"
  },
  {
    "name": "Paracetamol",
    "image_url": "https://www.ebi.ac.uk/chembl/api/data/image/CHEMBL178237.svg",
    "types": [
      "Analgesic",
      "Antipyretic"
    ],
    "formula": "C8H9NO2",
    "weight": 151.16,
    "source": "DrugBank",
    "dose_form": "Tablet",
    "atc": "N02BE01"
  },
  {
    "name": "Amoxicillin",
    "image_url": "https://www.ebi.ac.uk/chembl/api/data/image/CHEMBL178238.svg",
    "types": [
      "Antibiotic",
      "β-lactam"
    ],
    "formula": "C16H19N3O5S",
    "weight": 365.4,
    "source": "DrugBank",
    "dose_form": "Capsule",
    "atc": "J01CA04"
  },
  {
    "name": "Metformin",
    "image_url": "https://www.ebi.ac.uk/chembl/api/data/image/CHEMBL178239.svg",
    "types": [
      "Antidiabetic"
    ],
    "formula": "C4H11N5",
    "weight": 129.16,
    "source": "DrugBank",
    "dose_form": "Tablet",
    "atc": "A10BA02"
  },
  {
    "name": "Atorvastatin",
    "image_url": "https://www.ebi.ac.uk/chembl/api/data/image/CHEMBL178240.svg",
    "types": [
      "Statin"
    ],
    "formula": "C33H35FN2O5",
    "weight": 558.64,
    "source": "DrugBank",
    "dose_form": "Tablet",
    "atc": "C10AA05"
  },
  {
    "name": "Omeprazole",
    "image_url": "https://www.ebi.ac.uk/chembl/api/data/image/CHEMBL178250.svg",
    "types": [
      "PPI"
    ],
    "formula": "C17H19N3O3S",
    "weight": 345.42,
    "source": "DrugBank",
    "dose_form": "Capsule",
    "atc": "A02BC01"
  },
  {
    "name": "Losartan",
    "image_url": "https://www.ebi.ac.uk/chembl/api/data/image/CHEMBL178242.svg",
    "types": [
      "ARB"
    ],
    "formula": "C22H23ClN6O",
    "weight": 422.91,
    "source": "DrugBank",
    "dose_form": "Tablet",
    "atc": "C09CA01"
  },
  {
    "name": "Sertraline",
    "image_url": "https://www.ebi.ac.uk/chembl/api/data/image/CHEMBL178243.svg",
    "types": [
      "SSRI"
    ],
    "formula": "C17H17Cl2N",
    "weight": 306.23,
    "source": "DrugBank",
    "dose_form": "Tablet",
    "atc": "N06AB06"
  },
  {
    "name": "Dexamethasone",
    "image_url": "https://www.ebi.ac.uk/chembl/api/data/image/CHEMBL178245.svg",
    "types": [
      "Corticosteroid"
    ],
    "formula": "C22H29FO5",
    "weight": 392.46,
    "source": "DrugBank",
    "dose_form": "Tablet",
    "atc": "H02AB02"
  },
  ]

# columns = list(df.columns)
# data = df.values.tolist()
columns = ["name", "image_url", "types", "weight", "formula", "source"]

args = {
    "columns": columns,
    "data": dummy_data,
    "titleKey": "name",
    "imageKey": "image_url",
    "badgeKeys": ["types", "dose_form"],
    "detailKeys": ["weight", "formula", "source","atc"],
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
    # 必要ならセッションに保持（再利用/編集用）
    st.session_state["selected_record"] = rec
    show_record_dialog(rec)
