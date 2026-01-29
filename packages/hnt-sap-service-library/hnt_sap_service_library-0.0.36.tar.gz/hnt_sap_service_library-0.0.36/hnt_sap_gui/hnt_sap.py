import logging
import locale
from SapGuiLibrary import SapGuiLibrary
from dotenv import load_dotenv

from hnt_sap_gui.RPA_HNT_Constants import COD_LIBERACAO_BLOQUADO, COD_LIBERACAO_LIBERADO, COD_LIBERACAO_VAZIO
from hnt_sap_gui.common.tx_result import TxResult
from hnt_sap_gui.nota_fiscal.me21n_query_transaction import Me21nQueryTransaction

from .common.session import sessionable
from .nota_fiscal.nota_pedido_transaction import NotaPedidoTransaction
from .nota_fiscal.fatura_transaction import FaturaTransaction
from .nota_fiscal.miro_transaction import MiroTransaction
from .nota_fiscal.liberacao_transaction import LiberacaoTransaction

logger = logging.getLogger(__name__)

class SapGui(SapGuiLibrary):
    def __init__(self) -> None:
        locale.setlocale(locale.LC_ALL, ('pt_BR.UTF-8'))
        load_dotenv()
        pass
    def format_float(self, value):
        return locale.format_string("%.2f", value)
    @sessionable
    def hnt_aguardando_aprovacao_sap_com_estragia_liberacao(self, issues):
        logger.info(f"enter execute hnt_run_aguardando_aprovacao_sap issues:{len(issues)}")
        for i, issue in enumerate(issues):
            logger.info(f"{len(issues)}/{i+1} - process aguardando_aprovacao_sap")
            tx_result_liberacao = LiberacaoTransaction().execute(self, issue['nro_pedido'])
            if COD_LIBERACAO_BLOQUADO == tx_result_liberacao.codigo:
                estragia_liberacao = Me21nQueryTransaction().execute(self, issue['nro_pedido'])
                issue.update(estragia_liberacao)
            elif COD_LIBERACAO_LIBERADO == tx_result_liberacao.codigo:
                issue.update({ 'indicador_liberacao': tx_result_liberacao.codigo })
            elif tx_result_liberacao.codigo == COD_LIBERACAO_VAZIO:
                issue.update({ 'indicador_liberacao': COD_LIBERACAO_VAZIO })
        logger.info(f"leave execute hnt_run_aguardando_aprovacao_sap")
        return issues

    @sessionable
    def hnt_run_transaction(self, data):
        logger.info(f"enter execute run_hnt_transactions data:{data}")
        results = {
            "nota_pedido": None,
            "error": None
        }
        try:
            if 'nota_pedido' in data:
                tx_result_nota_pedido = NotaPedidoTransaction().execute(self, nota_pedido=data['nota_pedido'])
                results['nota_pedido'] = tx_result_nota_pedido

                tx_result_liberacao = LiberacaoTransaction().execute(self, results['nota_pedido'].codigo)
                results["liberacao"] = tx_result_liberacao
            
                if COD_LIBERACAO_BLOQUADO == tx_result_liberacao.codigo:
                    logger.info(f"leave execute hnt_run_transaction_miro result:{', '.join([str(results[obj]) for  obj in results])}")
                    return results
            
                results["miro"] = MiroTransaction().execute(self, data['miro'], results['nota_pedido'].codigo)
        except Exception as ex:
            logger.error(str(ex))
            results["error"] = str(ex)
        logger.info(f"leave execute run_hnt_transactions result:{', '.join([str(results[obj]) for obj in results])}")
        return results
    
    @sessionable
    def hnt_run_transaction_FV60(self, data):
        results = {
            "fatura": None,
            "error": None
        }
        try:
            results["fatura"] = FaturaTransaction().execute(self, data)
        except Exception as ex:
            logger.error(str(ex))
            results["error"] = str(ex)
        logger.info(f"leave execute run_hnt_transactions result:{', '.join([str(results[obj]) for obj in results])}")
        return results

    @sessionable
    def hnt_run_transaction_ME21N(self, data):
        logger.info(f"enter execute run_hnt_transactions data:{data}")
        results = {
            "nota_pedido": None,
            "error": None
        }
        try:
            if 'nota_pedido' in data:
                tx_result_nota_pedido = NotaPedidoTransaction().execute(self, nota_pedido=data['nota_pedido'])
                results['nota_pedido'] = tx_result_nota_pedido
        except Exception as ex:
            logger.error(str(ex))
            results["error"] = str(ex)
        logger.info(f"leave execute run_hnt_transactions result:{', '.join([str(results[obj]) for obj in results])}")
        return results
    
    @sessionable
    def hnt_run_transaction_miro(self, numero_pedido, data):
        logger.info(f"enter execute run_hnt_transactions data:{data}")
        results = {
            "miro": None,
            "liberacao": None,
            "error": None
        }

        try:
            tx_result_liberacao = LiberacaoTransaction().execute(self, numero_pedido)
            results["liberacao"] = tx_result_liberacao
            
            if COD_LIBERACAO_BLOQUADO == tx_result_liberacao.codigo:
                logger.info(f"leave execute hnt_run_transaction_miro result:{', '.join([str(results[obj]) for  obj in results])}")
                return results
            
            results["miro"] = MiroTransaction().execute(self, data, numero_pedido)

        except Exception as e:
            logger.error(str(e))
            results["error"] = str(e)

        logger.info(f"leave execute hnt_run_transaction_miro result:{', '.join([str(results[obj]) for obj in results])}")
        return results

    @sessionable
    def hnt_run_transaction_approved_miros(self, issues):
        logger.info(f"enter execute hnt_run_transaction_approved_miros issues:{len(issues)}")
        miros = []
        for i, issue in enumerate(issues):
            logger.info(f"{len(issues)}/{i+1} - process miro")
            results = {
                "miro": None,
                "error": None
            }
            try:
                numero_pedido = issue["miro"]["referencia_pedido"]["numero_pedido"]
                data = issue['miro']
                tx_result = MiroTransaction().execute(self, data, numero_pedido)
                results['miro'] = tx_result.__dict__
            except Exception as e:
                logger.error(str(e))
                results["error"] = str(e)
            miros.append({
                "issue": issue,
                "results": results
            })

        logger.info(f"leave execute hnt_run_transaction_approved_miros miros len:{len(miros)}")
        return miros
