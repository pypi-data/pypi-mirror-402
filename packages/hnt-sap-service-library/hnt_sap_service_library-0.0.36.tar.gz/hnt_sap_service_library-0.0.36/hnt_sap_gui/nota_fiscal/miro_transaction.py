import logging
from hnt_sap_gui.common.sap_status_bar import sbar_extracted_text
from hnt_sap_gui.common.tx_result import TxResult
from hnt_sap_gui.hnt_sap_exception import HntSapException

logger = logging.getLogger(__name__)
MSG_SAP_EXIST_DOC = '^Verificar se fatura já foi registrada sob documento contábil ([0-9]{10,15}) ([0-9]+)$'
MSG_SAP_CODIGO_DOCUMENTO = '^O documento do faturamento ([0-9]{10,15}) foi registrado  \( Doc.contábil ([0-9]{10,15}) \)$'
MSG_MIRO_SEM_ESTRAGIA_DE_APROVACAO = "^Doc.faturamento ([0-9]+) lançado; bloqueado para pagamento  \( Doc.contábil ([0-9]+) \)$"
MSG_MIRO_VALID_PERIOD = "Períodos contábeis permitidos:"
MSG_CFOP_INVALIDO = "^Primeiro dígito do CFOP em item ([0-9]+) está errado$"
MSG_DOC_AINDA_CONTEM_MSG = "Doc.faturamento ainda contém mensagens"
class MiroTransaction:
    def __init__(self) -> None:
        pass

    def execute(self, sapGuiLib, miro, numero_pedido):
        logger.info(f"enter execute miro:{miro}")
        #ABRE TRANSAÇÃO
        sapGuiLib.session.findById("wnd[0]/tbar[0]/okcd").Text = "/nMIRO"
        sapGuiLib.session.findById("wnd[0]").sendVKey(0)
        if sapGuiLib.session.findById("wnd[1]/usr/ctxtBKPF-BUKRS", False) != None:
            sapGuiLib.session.findById("wnd[1]/usr/ctxtBKPF-BUKRS").Text = "HFNT"
            sapGuiLib.session.findById("wnd[1]/tbar[0]/btn[0]").press()
        
        sapGuiLib.session.findById("wnd[0]/usr/cmbRM08M-VORGANG").Key = "1"  #Operação: "Fatura"


    #====================================
    #         Aba | DdsBásicos
    #====================================

        sapGuiLib.session.findById("wnd[0]/usr/subHEADER_AND_ITEMS:SAPLMR1M:6005/tabsHEADER/tabpHEADER_TOTAL/ssubHEADER_SCREEN:SAPLFDCB:0010/ctxtINVFO-BLDAT").Text = miro["dados_basicos"]["data_da_fatura"] #Data da fatura Form.Data Emissão
        sapGuiLib.session.findById("wnd[0]").sendVKey(0)
        sapGuiLib.session.findById("wnd[0]").sendVKey(0)

        if sapGuiLib.session.findById("wnd[1]/usr/txtMESSTXT1", False) != None:
            msg1 = sapGuiLib.session.findById("wnd[1]/usr/txtMESSTXT1").Text
            msg2 = sapGuiLib.session.findById("wnd[1]/usr/txtMESSTXT2").Text
            sapGuiLib.send_vkey(0)
            if MSG_MIRO_VALID_PERIOD == msg1:
                raise HntSapException(f"{msg1} : {msg2}")
            
        sapGuiLib.session.findById("wnd[0]/usr/subHEADER_AND_ITEMS:SAPLMR1M:6005/tabsHEADER/tabpHEADER_TOTAL/ssubHEADER_SCREEN:SAPLFDCB:0010/txtINVFO-XBLNR").Text = miro["dados_basicos"]["referencia"]  #Referência (Nº NF | Formato: 9 dígitos + "-" + série com 3 dígitos) Form.Nº Nota Fiscal (Ver regra em consumo)
        sapGuiLib.session.findById("wnd[0]/usr/subHEADER_AND_ITEMS:SAPLMR1M:6005/tabsHEADER/tabpHEADER_TOTAL/ssubHEADER_SCREEN:SAPLFDCB:0010/txtINVFO-WRBTR").Text = sapGuiLib.format_float(miro["dados_basicos"]["montante"])  #Montante Form.Valor Nota
        sapGuiLib.session.findById("wnd[0]/usr/subHEADER_AND_ITEMS:SAPLMR1M:6005/tabsHEADER/tabpHEADER_TOTAL/ssubHEADER_SCREEN:SAPLFDCB:0010/ctxtINVFO-SGTXT").Text = miro["dados_basicos"]["texto"]  #Texto (Mês de referência + Dt leitura anterior + Dt leitura atual) TODO
        sapGuiLib.session.findById("wnd[0]").sendVKey(0)


    #====================================
    #    ABA | REFERÊNCIA AO PEDIDO
    #====================================
    
        sapGuiLib.session.findById("wnd[0]/usr/subHEADER_AND_ITEMS:SAPLMR1M:6005/subITEMS:SAPLMR1M:6010/tabsITEMTAB/tabpITEMS_PO/ssubTABS:SAPLMR1M:6020/subREFERENZBELEG:SAPLMR1M:6211/ctxtRM08M-EBELN").Text = numero_pedido  #Nº Pedido
        sapGuiLib.session.findById("wnd[0]").sendVKey(0)
        sapGuiLib.session.findById("wnd[0]").sendVKey(0)
        sapGuiLib.session.findById("wnd[0]").sendVKey(0)
    
    #Caso haja pendência de liberação, o SAP exibirá a seguinte mensagem na barra de status:
    #O documento de compra 4505629357 ainda não está liberado

    #Caso o SAP identifique fatura registrada com os mesmos dados, será exibida a seguinte mensagem impeditiva na barra de status:
    #Verificar se fatura já foi registrada sob documento contábil 5100528501 2024  (O nº de doc exibido na msg refere a MIRO criada anteriormente com os mesmos dados)


    #====================================
    #           Aba | Detalhe
    #====================================

  #Exibe cabeçalho
        sapGuiLib.session.findById("wnd[0]/usr/subHEADER_AND_ITEMS:SAPLMR1M:6005/tabsHEADER/tabpHEADER_FI").Select()  #Exibe cabeçalho
        if sapGuiLib.session.findById("wnd[0]/usr/subHEADER_AND_ITEMS:SAPLMR1M:6005/tabsHEADER/tabpHEADER_FI/ssubHEADER_SCREEN:SAPLFDCB:0150/ctxtINVFO-J_1BNFTYPE", False) == None:
            msg = sapGuiLib.session.findById("wnd[0]/sbar").Text
            if sbar_extracted_text(MSG_SAP_EXIST_DOC, msg) != None:
                raise HntSapException(msg)

        sapGuiLib.session.findById("wnd[0]/usr/subHEADER_AND_ITEMS:SAPLMR1M:6005/tabsHEADER/tabpHEADER_FI/ssubHEADER_SCREEN:SAPLFDCB:0150/ctxtINVFO-J_1BNFTYPE").Text = miro["detalhe"]["ctg_nf"]   #Ctg.NF Form.Forncedor categoria NF
        sapGuiLib.session.findById("wnd[0]").sendVKey(0)


    #====================================
    #        Botão | Nota Fiscal
    #====================================

        sapGuiLib.session.findById("wnd[0]/tbar[1]/btn[21]").press()  #Botão [Nota Fiscal] \ Menu superior SAP
    
    #Aba | Síntese
    #====================================
        sapGuiLib.session.findById("wnd[0]").sendVKey(0)
        msg = sapGuiLib.session.findById("wnd[0]/sbar").Text
        if sbar_extracted_text(MSG_CFOP_INVALIDO, msg) != None:
                raise HntSapException(msg)

        sapGuiLib.session.findById("wnd[0]/tbar[0]/btn[3]").press()  #Voltar
        if 'imposto' in miro and miro['imposto'] is not None and 'sem_retencao' in miro['imposto'] and miro['imposto']['sem_retencao']:
            try:
                sapGuiLib.session.findById("wnd[0]/usr/subHEADER_AND_ITEMS:SAPLMR1M:6005/tabsHEADER/tabpHEADER_WT").Select()
                pos = 0
                while sapGuiLib.session.findById(f"wnd[0]/usr/subHEADER_AND_ITEMS:SAPLMR1M:6005/tabsHEADER/tabpHEADER_WT/ssubHEADER_SCREEN:SAPLFDCB:0080/subSUB_WT:SAPLFWTD:0120/tblSAPLFWTDWT_DIALOG/txtACWT_ITEM-WT_TYPE[0,{pos}]").Text != '________________________________________':
                    if len(sapGuiLib.session.findById(f"wnd[0]/usr/subHEADER_AND_ITEMS:SAPLMR1M:6005/tabsHEADER/tabpHEADER_WT/ssubHEADER_SCREEN:SAPLFDCB:0080/subSUB_WT:SAPLFWTD:0120/tblSAPLFWTDWT_DIALOG/ctxtACWT_ITEM-WT_WITHCD[1,{pos}]").Text) > 0:
                        sapGuiLib.session.findById(f"wnd[0]/usr/subHEADER_AND_ITEMS:SAPLMR1M:6005/tabsHEADER/tabpHEADER_WT/ssubHEADER_SCREEN:SAPLFDCB:0080/subSUB_WT:SAPLFWTD:0120/tblSAPLFWTDWT_DIALOG/ctxtACWT_ITEM-WT_WITHCD[1,{pos}]").Text = ""
                    pos += 1
                    if pos >= 6:
                        break
            except Exception as ex:
                logger.error(str(ex))
                raise HntSapException(str(ex))

        sapGuiLib.session.findById("wnd[0]/tbar[0]/btn[11]").press()  #Gravar
        sbar = sapGuiLib.session.findById("wnd[0]/sbar").Text
        if sbar == MSG_DOC_AINDA_CONTEM_MSG:
            raise HntSapException(f"SAP status bar: '{sbar}'")
        documento = None
        for patter in [MSG_SAP_CODIGO_DOCUMENTO, MSG_MIRO_SEM_ESTRAGIA_DE_APROVACAO, MSG_DOC_AINDA_CONTEM_MSG]: 
            documento = sbar_extracted_text(patter, sbar)
            if documento != None:
                break
        if documento == None:
            raise HntSapException(f"SAP status bar: '{sbar}'")
        tx_result = TxResult(documento, sbar)
        logger.info(f"Leave execute código do miro:{tx_result}")
        return tx_result