import logging
from hnt_sap_gui.common.sap_status_bar import sbar_extracted_text
from hnt_sap_gui.common.tx_result import TxResult
from hnt_sap_gui.hnt_sap_exception import HntSapException

logger = logging.getLogger(__name__)
MSG_SAP_CODIGO_NOTA_PEDIDO_ZCOR = "^Ped.C.Custo\\/Ordem criado sob o nº ([0-9]{10,11})$"
MSG_SAP_CODIGO_NOTA_PEDIDO_ZAIM = "^Ped.Ativo Imobilizad criado sob o nº ([0-9]{10,11})$"
MSG_SAP_FORNECEDOR_NAO_CRIADO = "^Fornecedor ([0-9]+) não foi criado" 
MSG_SAP_FORNECEDOR_BLOQUEADO = "^Fornecedor ([0-9]+) bloqueado" 
MSG_ORDEM_BLOQUEADA = "^Status de sistema BLOQ está ativo \(ORD ([0-9]+)\)$"
class NotaPedidoTransaction:
    def __init__(self) -> None:
        pass

    def execute(self, sapGuiLib, nota_pedido):
        logger.info(f"enter execute nota_pedido:{nota_pedido}")
        # ABRE TRANSAÇÃO
        sapGuiLib.run_transaction('/nme21n')
        if sapGuiLib.session.findById("wnd[0]/shellcont/shell/shellcont[1]/shell[1]", False) is not None:
            sapGuiLib.session.findById("wnd[0]/tbar[1]/btn[9]").press()
        sapGuiLib.send_vkey(0)

        # REORGANIZA ELEMENTOS PARA GARANTIR QUE CABEÇALHO ESTEJA ABERTO
        sapGuiLib.send_vkey(29) # Fechar Cabeçalho
        sapGuiLib.send_vkey(30) # Fechar Síntese de itens
        sapGuiLib.send_vkey(31) # Fechar Detahe de item
        sapGuiLib.send_vkey(26) # Abrir Cabeçalho

        # PREENCHE DADOS INICIAIS (Antes do cabeçalho)
        sapGuiLib.session.findById("wnd[0]/usr/subSUB0:SAPLMEGUI:0013/subSUB0:SAPLMEGUI:0030/subSUB1:SAPLMEGUI:1105/cmbMEPO_TOPLINE-BSART").Key = nota_pedido['tipo'] # Define o tipo de pedido como Ped.C.Custo/Ordem
        sapGuiLib.session.findById("wnd[0]/usr/subSUB0:SAPLMEGUI:0013/subSUB0:SAPLMEGUI:0030/subSUB1:SAPLMEGUI:1105/ctxtMEPO_TOPLINE-SUPERFIELD").Text = nota_pedido['cod_fornecedor']

        # CABEÇALHO | Aba Dados Organizacionais
        sapGuiLib.session.findById("wnd[0]/usr/subSUB0:SAPLMEGUI:0013/subSUB1:SAPLMEVIEWS:1100/subSUB2:SAPLMEVIEWS:1200/subSUB1:SAPLMEGUI:1102/tabsHEADER_DETAIL/tabpTABHDT9").Select() #Seleciona a aba Dados organizacionais
        sapGuiLib.session.findById("wnd[0]/usr/subSUB0:SAPLMEGUI:0013/subSUB1:SAPLMEVIEWS:1100/subSUB2:SAPLMEVIEWS:1200/subSUB1:SAPLMEGUI:1102/tabsHEADER_DETAIL/tabpTABHDT9/ssubTABSTRIPCONTROL2SUB:SAPLMEGUI:1221/ctxtMEPO1222-EKORG").Text = nota_pedido['org_compras']  # (orgCompras)
        sapGuiLib.session.findById("wnd[0]/usr/subSUB0:SAPLMEGUI:0013/subSUB1:SAPLMEVIEWS:1100/subSUB2:SAPLMEVIEWS:1200/subSUB1:SAPLMEGUI:1102/tabsHEADER_DETAIL/tabpTABHDT9/ssubTABSTRIPCONTROL2SUB:SAPLMEGUI:1221/ctxtMEPO1222-EKGRP").Text = nota_pedido['grp_compradores'] # grpCompradores)
        sapGuiLib.session.findById("wnd[0]/usr/subSUB0:SAPLMEGUI:0013/subSUB1:SAPLMEVIEWS:1100/subSUB2:SAPLMEVIEWS:1200/subSUB1:SAPLMEGUI:1102/tabsHEADER_DETAIL/tabpTABHDT9/ssubTABSTRIPCONTROL2SUB:SAPLMEGUI:1221/ctxtMEPO1222-BUKRS").Text = nota_pedido['empresa']  # (Empresa)

        sapGuiLib.send_vkey(29) #Fechar cabeçalho
        msg = sapGuiLib.session.findById("wnd[0]/sbar").Text
        for patter in [MSG_SAP_FORNECEDOR_NAO_CRIADO, MSG_SAP_FORNECEDOR_BLOQUEADO]: 
            if sbar_extracted_text(patter, msg) is not None:
                raise HntSapException(msg)

        sapGuiLib.send_vkey(27) #Abrir Síntese de itens
        sapGuiLib.send_vkey(31) #Fechar Detahe de item
        sapGuiLib.send_vkey(26) #Abrir Cabeçalho
        sapGuiLib.send_vkey(29) #Fechar cabeçalho


        # SÍNTESE DE ITENS
        for index, sintese_item in enumerate(nota_pedido['sintese_itens']):

            fatura = sintese_item['fatura']

            id_0015  = "wnd[0]/usr/subSUB0:SAPLMEGUI:0015"
            id_0016  = "wnd[0]/usr/subSUB0:SAPLMEGUI:0016"
            id_0019  = "wnd[0]/usr/subSUB0:SAPLMEGUI:0019"

            check_id_sintese  = sapGuiLib.session.findById(id_0016, False) != None
            id_gui_sintese    = id_0016 if check_id_sintese else id_0019

            check_id_detalhes = sapGuiLib.session.findById(id_0015, False) != None
            id_gui_detalhes   = id_0015 if check_id_detalhes else id_0019

            sapGuiLib.session.findById(f"{id_gui_sintese}/subSUB2:SAPLMEVIEWS:1100/subSUB2:SAPLMEVIEWS:1200/subSUB1:SAPLMEGUI:1211/tblSAPLMEGUITC_1211/ctxtMEPO1211-KNTTP[2,{index}]").Text = sintese_item['categoria_cc']  # (Categoria C|C)
            sapGuiLib.session.findById(f"{id_gui_sintese}/subSUB2:SAPLMEVIEWS:1100/subSUB2:SAPLMEVIEWS:1200/subSUB1:SAPLMEGUI:1211/tblSAPLMEGUITC_1211/ctxtMEPO1211-EPSTP[3,{index}]").Text = sintese_item['categoria_item']  # (Categoria do item)
            sapGuiLib.session.findById(f"{id_gui_sintese}/subSUB2:SAPLMEVIEWS:1100/subSUB2:SAPLMEVIEWS:1200/subSUB1:SAPLMEGUI:1211/tblSAPLMEGUITC_1211/txtMEPO1211-TXZ01[5,{index}]").Text = sintese_item['texto_breve']  # (Texto breve)
            sapGuiLib.session.findById(f"{id_gui_sintese}/subSUB2:SAPLMEVIEWS:1100/subSUB2:SAPLMEVIEWS:1200/subSUB1:SAPLMEGUI:1211/tblSAPLMEGUITC_1211/txtMEPO1211-MENGE[6,{index}]").Text = sintese_item['quantidade']  # (Qtd.do pedido)
            sapGuiLib.session.findById(f"{id_gui_sintese}/subSUB2:SAPLMEVIEWS:1100/subSUB2:SAPLMEVIEWS:1200/subSUB1:SAPLMEGUI:1211/tblSAPLMEGUITC_1211/ctxtMEPO1211-NAME1[10,{index}]").Text = sintese_item['centro']  # (Centro)
            sapGuiLib.session.findById(f"{id_gui_sintese}/subSUB2:SAPLMEVIEWS:1100/subSUB2:SAPLMEVIEWS:1200/subSUB1:SAPLMEGUI:1211/tblSAPLMEGUITC_1211/ctxtMEPO1211-WGBEZ[19,{index}]").Text = sintese_item['grp_mercadorias']  # (Grupo de mercadorias)
            sapGuiLib.send_vkey(0)

 

            # DETALHES DE ITEM | Aba Serviços
            check_id_detalhes = sapGuiLib.session.findById(id_0015, False) != None
            id_gui_detalhes   = id_0015 if check_id_detalhes else id_0019

            if sapGuiLib.session.findById(f"{id_gui_detalhes}/subSUB3:SAPLMEVIEWS:1100/subSUB2:SAPLMEVIEWS:1200/subSUB1:SAPLMEGUI:1301/subSUB2:SAPLMEGUI:1303/tabsITEM_DETAIL/tabpTABIDT1", False) != None:  
                # Seleciona aba "Serviços"
                sapGuiLib.session.findById(f"{id_gui_detalhes}/subSUB3:SAPLMEVIEWS:1100/subSUB2:SAPLMEVIEWS:1200/subSUB1:SAPLMEGUI:1301/subSUB2:SAPLMEGUI:1303/tabsITEM_DETAIL/tabpTABIDT1").select()
            
            for j, item in enumerate(sintese_item['item']):
                check_id_detalhes = sapGuiLib.session.findById(id_0015, False) != None
                id_gui_detalhes   = id_0015 if check_id_detalhes else id_0019
                if j > 1:
                    sapGuiLib.session.findById(f"{id_gui_detalhes}/subSUB3:SAPLMEVIEWS:1100/subSUB2:SAPLMEVIEWS:1200/subSUB1:SAPLMEGUI:1301/subSUB2:SAPLMEGUI:1303/tabsITEM_DETAIL/tabpTABIDT1/ssubTABSTRIPCONTROL1SUB:SAPLMEGUI:1328/subSUB0:SAPLMLSP:0400/tblSAPLMLSPTC_VIEW").verticalScrollbar.position = j-1
                pos = 0 if j == 0 else 1
                sapGuiLib.session.findById(f"{id_gui_detalhes}/subSUB3:SAPLMEVIEWS:1100/subSUB2:SAPLMEVIEWS:1200/subSUB1:SAPLMEGUI:1301/subSUB2:SAPLMEGUI:1303/tabsITEM_DETAIL/tabpTABIDT1/ssubTABSTRIPCONTROL1SUB:SAPLMEGUI:1328/subSUB0:SAPLMLSP:0400/tblSAPLMLSPTC_VIEW/ctxtESLL-SRVPOS[2,{pos}]").Text = item['nro_servico'] # (Nº serviço)

                if item['centro_custo'] is not None:
                    sapGuiLib.session.findById(f"{id_gui_detalhes}/subSUB3:SAPLMEVIEWS:1100/subSUB2:SAPLMEVIEWS:1200/subSUB1:SAPLMEGUI:1301/subSUB2:SAPLMEGUI:1303/tabsITEM_DETAIL/tabpTABIDT1/ssubTABSTRIPCONTROL1SUB:SAPLMEGUI:1328/subSUB0:SAPLMLSP:0400/tblSAPLMLSPTC_VIEW/ctxtRM11P-KOSTL[3,{pos}]").Text = item['centro_custo']  # (Centro custo)
                    sapGuiLib.session.findById(f"{id_gui_detalhes}/subSUB3:SAPLMEVIEWS:1100/subSUB2:SAPLMEVIEWS:1200/subSUB1:SAPLMEGUI:1301/subSUB2:SAPLMEGUI:1303/tabsITEM_DETAIL/tabpTABIDT1/ssubTABSTRIPCONTROL1SUB:SAPLMEGUI:1328/subSUB0:SAPLMLSP:0400/tblSAPLMLSPTC_VIEW/txtESLL-MENGE[4,{pos}]").Text = item['quantidade']  # (Quantidade)
                    sapGuiLib.session.findById(f"{id_gui_detalhes}/subSUB3:SAPLMEVIEWS:1100/subSUB2:SAPLMEVIEWS:1200/subSUB1:SAPLMEGUI:1301/subSUB2:SAPLMEGUI:1303/tabsITEM_DETAIL/tabpTABIDT1/ssubTABSTRIPCONTROL1SUB:SAPLMEGUI:1328/subSUB0:SAPLMLSP:0400/tblSAPLMLSPTC_VIEW/txtESLL-TBTWR[5,{pos}]").Text = sapGuiLib.format_float(item['valor_bruto']) # (Preço bruto)
                elif item['ord_interna'] is not None:
                    sapGuiLib.session.findById(f"{id_gui_detalhes}/subSUB3:SAPLMEVIEWS:1100/subSUB2:SAPLMEVIEWS:1200/subSUB1:SAPLMEGUI:1301/subSUB2:SAPLMEGUI:1303/tabsITEM_DETAIL/tabpTABIDT1/ssubTABSTRIPCONTROL1SUB:SAPLMEGUI:1328/subSUB0:SAPLMLSP:0400/tblSAPLMLSPTC_VIEW/txtESLL-MENGE[3,{pos}]").Text = item['quantidade']  # (Quantidade)
                    sapGuiLib.session.findById(f"{id_gui_detalhes}/subSUB3:SAPLMEVIEWS:1100/subSUB2:SAPLMEVIEWS:1200/subSUB1:SAPLMEGUI:1301/subSUB2:SAPLMEGUI:1303/tabsITEM_DETAIL/tabpTABIDT1/ssubTABSTRIPCONTROL1SUB:SAPLMEGUI:1328/subSUB0:SAPLMLSP:0400/tblSAPLMLSPTC_VIEW/txtESLL-TBTWR[4,{pos}]").Text = sapGuiLib.format_float(item['valor_bruto']) # (Preço bruto)
                    sapGuiLib.session.findById("wnd[0]/usr/subSUB0:SAPLMEGUI:0019/subSUB3:SAPLMEVIEWS:1100/subSUB2:SAPLMEVIEWS:1200/subSUB1:SAPLMEGUI:1301/subSUB2:SAPLMEGUI:1303/tabsITEM_DETAIL/tabpTABIDT1/ssubTABSTRIPCONTROL1SUB:SAPLMEGUI:1328/subSUB0:SAPLMLSP:0400/tblSAPLMLSPTC_VIEW/ctxtRM11P-AUFNR[9,0]").Text = item['ord_interna']  # (Ordem Interna)
                else:
                    raise HntSapException('Informe o Centro de custo ou uma ordem interna em Tipo de Alocação de DespesaNo - Formulário Notas Fiscais de Serviço')
                # DETALHES DE ITEM | Aba Fatura
                if j == 0 and sapGuiLib.session.findById(f"{id_gui_detalhes}/subSUB3:SAPLMEVIEWS:1100/subSUB2:SAPLMEVIEWS:1200/subSUB1:SAPLMEGUI:1301/subSUB2:SAPLMEGUI:1303/tabsITEM_DETAIL/tabpTABIDT7", False) != None:
                    sapGuiLib.session.findById(f"{id_gui_detalhes}/subSUB3:SAPLMEVIEWS:1100/subSUB2:SAPLMEVIEWS:1200/subSUB1:SAPLMEGUI:1301/subSUB2:SAPLMEGUI:1303/tabsITEM_DETAIL/tabpTABIDT7").Select() #Seleciona a aba "Fatura"
                    check_id_detalhes = sapGuiLib.session.findById(id_0015, False) != None
                    id_gui_detalhes   = id_0015 if check_id_detalhes else id_0019
                    sapGuiLib.session.findById(f"{id_gui_detalhes}/subSUB3:SAPLMEVIEWS:1100/subSUB2:SAPLMEVIEWS:1200/subSUB1:SAPLMEGUI:1301/subSUB2:SAPLMEGUI:1303/tabsITEM_DETAIL/tabpTABIDT7/ssubTABSTRIPCONTROL1SUB:SAPLMEGUI:1317/ctxtMEPO1317-MWSKZ").Text = fatura['cod_imposto']  # (Cód.imposto)
                    # Seleciona aba "Serviços"
                    sapGuiLib.session.findById(f"{id_gui_detalhes}/subSUB3:SAPLMEVIEWS:1100/subSUB2:SAPLMEVIEWS:1200/subSUB1:SAPLMEGUI:1301/subSUB2:SAPLMEGUI:1303/tabsITEM_DETAIL/tabpTABIDT1").select()

            sapGuiLib.send_vkey(0)

            try:
                msg = sapGuiLib.session.findById('/app/con[0]/ses[0]/wnd[2]/usr/txtMESSTXT1').text
            except:
                msg = None

            if msg is not None and sbar_extracted_text(MSG_ORDEM_BLOQUEADA, msg) is not None:
                raise HntSapException(msg)

            check_id_detalhes = sapGuiLib.session.findById(id_0015, False) != None
            id_gui_detalhes   = id_0015 if check_id_detalhes else id_0019
 



        # PROCESSO PARA ANEXAR O DOCUMENTO NO PEDIDO
        for anexo in nota_pedido['anexo']:
            sapGuiLib.session.findById("wnd[0]/titl/shellcont/shell").pressButton("%GOS_TOOLBOX")
            sapGuiLib.session.findById("wnd[0]/shellcont/shell").pressContextButton("CREATE_ATTA")
            sapGuiLib.session.findById("wnd[0]/shellcont/shell").selectContextMenuItem("PCATTA_CREA")
            sapGuiLib.session.findById("wnd[1]/usr/ctxtDY_PATH").Text = anexo['path'] #Diretório de NFs
            sapGuiLib.session.findById("wnd[1]/usr/ctxtDY_FILENAME").Text = anexo['filename'] #PDF da DANFE
            sapGuiLib.session.findById("wnd[1]/tbar[0]/btn[0]").press()

        sapGuiLib.session.findById("wnd[0]/tbar[0]/btn[11]").press() # Grava o lançamento
        sbar = sapGuiLib.session.findById("wnd[0]/sbar").Text # Captura do nº do documento exibido na barra de status do SAP (últimos 10 caracteres da mensagem)
        cod_nota_pedido = None
        for patter in [MSG_SAP_CODIGO_NOTA_PEDIDO_ZCOR, MSG_SAP_CODIGO_NOTA_PEDIDO_ZAIM]: 
            cod_nota_pedido = sbar_extracted_text(patter, sbar)
            if cod_nota_pedido != None:
                break
        if cod_nota_pedido == None:
            raise HntSapException(f"SAP status bar: '{sbar}'")
        tx_result = TxResult(cod_nota_pedido, sbar)
        logger.info(f"Leave execute code service_note:{str(tx_result)}")

        return tx_result