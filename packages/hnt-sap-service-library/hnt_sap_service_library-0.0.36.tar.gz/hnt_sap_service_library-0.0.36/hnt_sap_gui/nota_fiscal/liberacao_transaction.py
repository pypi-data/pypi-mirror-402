from datetime import datetime
import logging

from hnt_sap_gui.common.tx_result import TxResult
logger = logging.getLogger(__name__)

class LiberacaoTransaction:
    def __init__(self) -> None:
        pass

    def execute(self, sapGuiLib, codigo_pedido):
        sapGuiLib.run_transaction('/nME2N')
        sapGuiLib.send_vkey(0)
        
        # Preenche doc pedido
        sapGuiLib.session.findById("wnd[0]/usr/ctxtEN_EBELN-LOW").Text = codigo_pedido
        sapGuiLib.session.findById("wnd[0]/usr/ctxtLISTU").Text = "ALV"
        sapGuiLib.session.findById("wnd[0]/tbar[1]/btn[8]").press()
            
        # Altera o tipo de visualização
        sapGuiLib.session.findById("wnd[0]/tbar[1]/btn[46]").press()
        # Captura cód. liberação
        cod_liberacao = sapGuiLib.session.findById("wnd[0]/usr/lbl[1,3]").Text
        tx_result = TxResult(cod_liberacao)
        logger.info(f"Leave execute obtem código de liberação:'{str(tx_result)}'")
        return tx_result
