import logging
from hnt_sap_gui.RPA_HNT_Constants import COD_LIBERACAO_LIBERADO

logger = logging.getLogger(__name__)
TAB_ESTRAGIA_LIBERACAO = "wnd[0]/usr/subSUB0:SAPLMEGUI:0013/subSUB1:SAPLMEVIEWS:1100/subSUB2:SAPLMEVIEWS:1200/subSUB1:SAPLMEGUI:1102/tabsHEADER_DETAIL/tabpTABHDT11"
class Me21nQueryTransaction:
    def __init__(selft) -> None:
        pass

    def execute(self, sapGuiLib, codigo_pedido):
        logger.info(f"Enter execute codigo_pedido:{codigo_pedido}")
        sapGuiLib.run_transaction('/nME21N')
        sapGuiLib.session.findById("wnd[0]/tbar[1]/btn[17]").press()
        sapGuiLib.session.findById("wnd[1]/usr/subSUB0:SAPLMEGUI:0003/ctxtMEPO_SELECT-EBELN").Text = codigo_pedido
        sapGuiLib.send_vkey(0)
        # REORGANIZA ELEMENTOS PARA GARANTIR QUE CABEÇALHO ESTEJA ABERTO
        sapGuiLib.send_vkey(29) # Fechar Cabeçalho
        sapGuiLib.send_vkey(30) # Fechar Síntese de itens
        sapGuiLib.send_vkey(31) # Fechar Detahe de item
        sapGuiLib.send_vkey(26) # Abrir Cabeçalho

        if sapGuiLib.session.findById(TAB_ESTRAGIA_LIBERACAO, False) is None:
            return {
                'error': 'Sem Estrat.liberacao'
            }

        sapGuiLib.session.findById(TAB_ESTRAGIA_LIBERACAO).select()
        indicadorLiberacao = sapGuiLib.session.findById("wnd[0]/usr/subSUB0:SAPLMEGUI:0013/subSUB1:SAPLMEVIEWS:1100/subSUB2:SAPLMEVIEWS:1200/subSUB1:SAPLMEGUI:1102/tabsHEADER_DETAIL/tabpTABHDT11/ssubTABSTRIPCONTROL2SUB:SAPLMERELVI:1100/txtMEPO_REL_GENERAL-FRGKX").Text
        logger.info(f"indicadorLiberacao:{indicadorLiberacao}")
        if indicadorLiberacao == COD_LIBERACAO_LIBERADO:
            return {
                'indicador_liberacao': indicadorLiberacao
            }

        responsavel = None
        responsavel_email = None

        shell = sapGuiLib.session.findById("wnd[0]/titl/shellcont/shell")
        shell.SetFocus()
        shell.pressContextButton("%GOS_TOOLBOX")
        shell.selectContextMenuItem("%GOS_WF_OVERVIEW")
        sapGuiLib.session.findById("wnd[1]/usr/cntlCONTAINER/shellcont/shell/shellcont[1]/shell").sapEvent("","","sapevent:STEP_AGENT:0001")
        responsavelObj = sapGuiLib.session.findById("wnd[2]/usr/lbl[8,3]", False)
        if responsavelObj is not None:
            sapGuiLib.session.findById("wnd[2]/tbar[0]/btn[5]").press()
            if sapGuiLib.session.findById("wnd[2]/usr/lbl[49,3]", False) is not None:
                sapGuiLib.session.findById("wnd[2]/usr/lbl[49,3]").setFocus()
                responsavel = sapGuiLib.session.findById("wnd[2]/usr/lbl[8,3]", False).Text
            elif sapGuiLib.session.findById("wnd[2]/usr/lbl[49,4]", False) is not None:
                sapGuiLib.session.findById("wnd[2]/usr/lbl[49,4]").setFocus()
                responsavel = sapGuiLib.session.findById("wnd[2]/usr/lbl[8,4]", False).Text
            elif sapGuiLib.session.findById("wnd[2]/usr/lbl[49,5]", False) is not None:
                sapGuiLib.session.findById("wnd[2]/usr/lbl[49,5]").setFocus()
                responsavel = sapGuiLib.session.findById("wnd[2]/usr/lbl[8,5]", False).Text
            elif sapGuiLib.session.findById("wnd[2]/usr/lbl[49,6]", False) is not None:
                sapGuiLib.session.findById("wnd[2]/usr/lbl[49,6]").setFocus()
                responsavel = sapGuiLib.session.findById("wnd[2]/usr/lbl[8,6]", False).Text
            elif sapGuiLib.session.findById("wnd[2]/usr/lbl[49,7]", False) is not None:
                sapGuiLib.session.findById("wnd[2]/usr/lbl[49,7]").setFocus()
                responsavel = sapGuiLib.session.findById("wnd[2]/usr/lbl[8,7]", False).Text
            else:
                return {
                    'indicador_liberacao': indicadorLiberacao,
                    'responsavel': None,
                    'responsavel_email': None,
                    'error': 'Valida até 4 aprovadores, verificar o número de aprovadores'
                }
            sapGuiLib.session.findById("wnd[2]").sendVKey(2)
            sapGuiLib.session.findById("wnd[0]/tbar[1]/btn[7]").press()
            sapGuiLib.session.findById("wnd[0]/usr/tabsTABSTRIP1/tabpADDR/ssubMAINAREA:SAPLSUID_MAINTENANCE:1900/txtSUID_ST_NODE_COMM_DATA-SMTP_ADDR").setFocus()
            responsavel_email = sapGuiLib.session.findById("wnd[0]/usr/tabsTABSTRIP1/tabpADDR/ssubMAINAREA:SAPLSUID_MAINTENANCE:1900/txtSUID_ST_NODE_COMM_DATA-SMTP_ADDR").Text
            sapGuiLib.session.findById("wnd[0]/tbar[0]/btn[3]").press()
            sapGuiLib.session.findById("wnd[0]/tbar[0]/btn[3]").press()
        else:
            if sapGuiLib.session.findById("wnd[2]/usr/txtADDR3_DATA-NAME_TEXT", False) is not None:
                responsavel = sapGuiLib.session.findById("wnd[2]/usr/txtADDR3_DATA-NAME_TEXT").Text
                responsavel_email = sapGuiLib.session.findById("wnd[2]/usr/txtSZA5_D0700-SMTP_ADDR").Text
            else:
                sapGuiLib.session.findById("wnd[1]").close()
                return {
                    'indicador_liberacao': indicadorLiberacao,
                    'responsavel': None,
                    'responsavel_email': None,
                    'error': 'Sem responsável definido no SAP'
                }    
        sapGuiLib.session.findById("wnd[2]").close()
        sapGuiLib.session.findById("wnd[1]").close()
        return {
            'indicador_liberacao': indicadorLiberacao,
            'responsavel': responsavel,
            'responsavel_email': responsavel_email
        }
