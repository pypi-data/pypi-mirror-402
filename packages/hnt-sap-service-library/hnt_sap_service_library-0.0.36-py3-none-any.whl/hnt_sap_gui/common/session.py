from functools import wraps
import os
import logging

from hnt_sap_gui.hnt_sap_exception import HntSapException

logger = logging.getLogger(__name__)

def sessionable(original_function):
    @wraps(original_function)
    def wrapped(*args, **kwargs):
        this = args[0]
        try:
            _open(this)
            response = original_function(*args, **kwargs)
            _close(this)
            return response
        except HntSapException as hntEx:
            _close(this)
            raise hntEx
        except Exception as ex:
            logger.error(msg=str(ex))
            if this.session.findById("wnd[0]/sbar", False) != None:
                msg = this.session.findById("wnd[0]/sbar").Text
                logger.error(f"SAP Status bar: '{msg}'")
                raise HntSapException(msg, ex.args)
            
            if isinstance(ex.args[0], str) and ex.args[0].endswith("object has no attribute 'sapapp'"):
                raise ex
            _close(this)
    return wrapped

def _open(sap_gui):
    logger.info("enter _open")
    sap_gui.connect_to_session()
    
    sap_gui.open_connection(os.getenv("SAP_OPEN_CONNECTION"))

    sap_gui.session.findById("wnd[0]/usr/txtRSYST-MANDT").text = os.getenv("SAP_MANDANTE")
    sap_gui.session.findById("wnd[0]/usr/txtRSYST-BNAME").text = os.getenv("SAP_USERNAME")
    sap_gui.session.findById("wnd[0]/usr/pwdRSYST-BCODE").text = os.getenv("SAP_PASSWORD")
    sap_gui.session.findById("wnd[0]/usr/txtRSYST-LANGU").text = os.getenv("SAP_LANGUAGE")
    sap_gui.send_vkey(0)
    if sap_gui.session.findById("wnd[1]/usr/radMULTI_LOGON_OPT2", False) != None:
        sap_gui.session.findById("wnd[1]/usr/radMULTI_LOGON_OPT2").select()
        sap_gui.session.findById("wnd[1]/tbar[0]/btn[0]").press()
        if sap_gui.session.findById("wnd[1]/tbar[0]/btn[0]", False) != None:
            sap_gui.session.findById("wnd[1]/tbar[0]/btn[0]").press()
    elif sap_gui.session.findById("wnd[1]/tbar[0]/btn[0]", False) != None:
        sap_gui.session.findById("wnd[1]/tbar[0]/btn[0]").press()
    logger.info("leave _open")

def _close(sap_gui):
    logger.info("enter _close")
    sap_gui.session.findById("wnd[0]").close()
    if sap_gui.session.findById("wnd[1]/usr/btnSPOP-OPTION1", False) != None:
        sap_gui.session.findById("wnd[1]/usr/btnSPOP-OPTION1").press()
    elif sap_gui.session.findById("wnd[2]/usr/btnSPOP-OPTION1", False) != None:
        sap_gui.session.findById("wnd[2]/usr/btnSPOP-OPTION1").press()
    logger.info("leave _close")