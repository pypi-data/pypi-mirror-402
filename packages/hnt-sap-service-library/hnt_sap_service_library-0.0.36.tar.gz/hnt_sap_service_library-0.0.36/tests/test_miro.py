import json
from os import getcwd, makedirs, path
from hnt_sap_gui import SapGui

def test_create():
    with open("./devdata/json/miro_GHN-38789.json", "r", encoding="utf-8") as miro_arquivo_json: miro = json.load(miro_arquivo_json)

    data = {
        "miro": miro,
    }
    result = SapGui().hnt_run_transaction_miro( "4507017248", data["miro"])
    print(result)
    assert result is not None