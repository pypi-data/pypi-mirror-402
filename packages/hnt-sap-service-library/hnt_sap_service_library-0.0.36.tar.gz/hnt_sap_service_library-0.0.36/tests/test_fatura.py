import json
from hnt_sap_gui import SapGui
# from hnt_sap_gui.nota_fiscal.nota_pedido_transaction import NotaPedidoTransaction

def test_create():
    with open("./devdata/json/fatura_expected.json", "r", encoding="utf-8") as fatura_arquivo_json: fatura = json.load(fatura_arquivo_json)

    data = {
        "fatura": fatura,
    }
    result = SapGui().hnt_run_transaction_FV60(data)
    assert result is not None

def test_create_1325():
    with open("./tests/expected_fatura_GHN-1325.json", "r", encoding="utf-8") as fatura_arquivo_json: fatura = json.load(fatura_arquivo_json)
    result = SapGui().hnt_run_transaction_FV60(fatura)
    assert result is not None

def test_create_1326():
    with open("./tests/expected_fatura_GHN-1326.json", "r", encoding="utf-8") as fatura_arquivo_json: fatura = json.load(fatura_arquivo_json)
    result = SapGui().hnt_run_transaction_FV60(fatura)
    assert result is not None

def test_create_1327():
    with open("./tests/expected_fatura_GHN-1327.json", "r", encoding="utf-8") as fatura_arquivo_json: fatura = json.load(fatura_arquivo_json)
    result = SapGui().hnt_run_transaction_FV60(fatura)
    assert result is not None