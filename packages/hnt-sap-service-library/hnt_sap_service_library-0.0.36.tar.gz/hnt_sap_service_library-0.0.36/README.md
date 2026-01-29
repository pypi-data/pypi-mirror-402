# hnt_sap_library


# Reglas de negócios para os script SAP: 
Identificação de DANFE ou FATURA:
    Utilizar o campo do anexo invoice.json NotaFiscal, se tiver um valor é DANFE do contrario é uma fatura.

## DANFE
    - Nota de Pedido (nme21n)
    - Aprovaçao da Nota de Pedido, caso for necessário.
    - Miro
        Tx MIRO:
            Salva um doc contábil final
## MIRO
    Query
    /nMIRO
    Menu: Exibir documento de faturamento
    Input: 
        Nro doc.faturamento: #####
        Exercício: 2024

## FATURA
### Modelo Atual em PROD
    - Entrar fatura de Fornecedor (FB60)
    - Sem aprovacao 
    - Salva um doc contábil final
### Modelo Novo em PROD
    - Pre-Editar Fatura de Fornecedor (FV60)
    - Com aprovacao 
    - Salva um draft Documento contábil
    - Salva um doc contábil final
### Modelo Novo em PROD - Query
    - /nFBV3
# Requirements
    Pip 24.0
    Python 3.11.5
    VirtualEnv

# Setup the development env unix
```sh
virtualenv venv
. ./venv/bin/activate
```

# Setup the development env win10
```sh
python -m venv venv
. .\venv\Scripts\activate
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python.exe -m pip install --upgrade pip
pip install pytest
pip install python-dotenv
pip install robotframework-sapguilibrary
copy .\.env.template .\sap_nota_pedido\.env
```

# Before publish the packages
```sh
pip install --upgrade pip
pip install --upgrade setuptools wheel
pip install twine
```
# How to cleanup generated files to publish
```powershell
Remove-Item .\build\ -Force -Recurse
Remove-Item .\dist\ -Force -Recurse
Remove-Item .\hnt_sap_service_library.egg-info\ -Force -Recurse
```

# How to publish the package to test.pypi.org
```sh
python setup.py sdist bdist_wheel
python -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*
```

# How to publish the package to pypi.org (username/password see lastpass Pypi)
```sh
python setup.py sdist bdist_wheel
python -m twine upload --repository-url https://upload.pypi.org/legacy/ dist/*
```

#SAP

/nme21n - Consulta
Menu superior esquerdo : 
Documento de compras = 4505629946
F8


/miro leitura, acessar pela nota de pedido:
5109872720