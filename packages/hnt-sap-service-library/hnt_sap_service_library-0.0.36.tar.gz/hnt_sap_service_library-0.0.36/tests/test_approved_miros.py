import json
from os import getcwd, makedirs, path
from hnt_sap_gui import SapGui

def test_create():
    with open("./devdata/json/approved_miros_4.json", "r", encoding="utf-8") as miro_arquivo_json: issues = json.load(miro_arquivo_json)
    miros_results = SapGui().hnt_run_transaction_approved_miros(issues)
    with open(f"./output/json/miros_results_{len(miros_results)}.json", "w", encoding="utf-8") as json_file:
        json.dump( miros_results, json_file, ensure_ascii=False, indent=4)

