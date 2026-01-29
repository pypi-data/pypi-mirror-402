import json
from os import getcwd, makedirs, path
from hnt_sap_gui import SapGui

def test_create_pedido_centro_de_custo():
    issues = [
        {
            "key": 'GHN-72658',
            "nro_pedido": '4507524641',
        }
    ]
    issues_estrategia_liberacao = SapGui().hnt_aguardando_aprovacao_sap_com_estragia_liberacao(issues)
    with open(f"./output/json/aguardando_aprovacao_sap_com_estragia_liberacao_{len(issues_estrategia_liberacao)}.json", "w", encoding="utf-8") as json_file:
        json.dump( issues_estrategia_liberacao, json_file, ensure_ascii=False, indent=4)
