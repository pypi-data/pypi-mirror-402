from datetime import datetime
import json

class TxResult:
    def __init__(self, codigo, sbar=None) -> None:
        self.codigo = codigo
        self.sbar = sbar
        self.created_at = datetime.now().strftime("%Y%m%d%H%M%S")

    def __str__(self):
        return f"TxResult instance with codigo: '{self.codigo}', sbar: '{self.sbar}', created_at:'{self.created_at}'"
    