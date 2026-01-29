import requests
import json
import time
import enum


class CalculationType(enum.Enum):
    INTEREST_RATES_SWAP = "interest_rates_swap_calculator"
    FIXED_RATE_BOND = "fixed_rate_bond"
    VANILLA_OPTION = "vanilla_option_calculator"
    YIELD_CURVE = "yield_curve_calculator"
    ZERO_COUPON_BOND = "zero_coupon_bond_calculator"
    FLOATING_RATE_BOND = "floating_rate_bond"
    FORWARD_RATE_AGREEMENT = "forward_rate_agreement_calculator"
    OIS = "overnight_index_swap_calculator"
    BASIS_SWAP = "basis_swap_calculator"
    FX_FORWARD = "fx_forward_calculator"
    FX_SWAP = "fx_swap_calculator"
    NDF = "ndf_calculator"
    CROSS_CURRENCY = "cc_swap_calculator"
    ASIAN_OPTION = "asian_option_calculator"
    SINGLE_BARRIER_OPTION = "single_barrier_option_calculator"
    DOUBLE_BARRIER_OPTION = "double_barrier_option_calculator"
    CAP_FLOOR = "cap_volatility_calculator"
    SWAPTION = "swaption_calculator"
    CPI_BOND = "cpi_bond_calculator"
    ZCI_SWAP = "zero_coupon_inflation_swap_calculator"
    YoY_SWAP = "year_on_year_inflation_swap_calculator"
    CPI_SWAP = "cpi_swap_calculator"
    CDS = "cds_calculator"
    INFLATION_CURVE = "inflation_curve_calculator"
    ASSET_SWAP = "asset_swap_calculator"
    REPO = "repo_calculator"
    DEPOSIT = "deposit_calculator"
    LOAN = "loan_calculator"
    PORTFOLIO = "portfolio"
    CRYPTO = "crypto_calculator"
    TL_REF_INDEX_BOND = "tl_ref_index_bond"
    SPOT_CALCULATOR = "spot_calculator"


class DataType(enum.Enum):
    YIELD_CURVE = 0
    YIELD_DATA = 1
    FIXED_RATE_BOND_DEFINITION = 2
    VANILLA_OPTION_DEFINITION = 3
    PRICES_FOR_VOL_MARKET_DATA = 4
    FLOATING_BOND_DEFINITION = 5
    DEPOSITS = 6
    ZCIIS_DATA = 7
    FUTURE_FIXING_DAYS = 8
    FIX_DATA = 9


class RhoovaError(Exception):
    def __init__(self, message):
        self.message = message

    def printPretty(self):
        try:
            print(json.dumps(json.loads(self.message), indent=4))
        except json.decoder.JSONDecodeError:
            print(self.message)


class ClientConfig:
    def __init__(self, apiKey: str, apiSecret: str):
        self.apiUrl = "https://app.rhoova.com/api"
        self.apiKey = apiKey
        self.apiSecret = apiSecret


class TaskTransaction:
    def __init__(self):
        self.tasks = []
        self.commonData = {}

    def addTask(self, identifier, calculationType: CalculationType, data):
        self.tasks.append({
            'identifier': identifier,
            'calculationType': calculationType.value,
            'data': data
        })

    def setCommonData(self, commonData):
        self.commonData = commonData

    def setParams(self, params):
            self.params = params


class Api:
    def __init__(self, config: ClientConfig):
        self.config = config

    def createTask(self, calculationType: CalculationType, data, holdRequest=False):
        if not isinstance(calculationType, CalculationType):
            raise TypeError('Calculation must be an instance of CalculationType')
        url = self.config.apiUrl + "/tasks/" + calculationType.value + "?apiClient=true"
        response = requests.post(url=url, data=json.dumps(data), headers={
            'Content-type': 'application/json',
            'ekx-api-key': self.config.apiKey,
            'ekx-api-secret': self.config.apiSecret,
            "ekx-wait-result": 'true' if holdRequest else 'false'
        })
        if response.status_code == 200:
            return json.loads(response.text)
        else:
            raise RhoovaError(response.text)

    def getTaskResult(self, taskId):
        url = self.config.apiUrl + "/tasks/" + taskId
        response = requests.get(url=url, headers={
            'Content-type': 'application/json',
            'ekx-api-key': self.config.apiKey,
            'ekx-api-secret': self.config.apiSecret
        })
        if response.status_code == 200:
            data = json.loads(response.text)
            if data['error'] is not None:
                raise RhoovaError(data['error'])
            else:
                return data
        else:
            raise RhoovaError(response.text)

    def createTaskAndWaitForResult(self, calculationType: CalculationType, data, maxTryCount=6, tryInterval=5):
        task = self.createTask(calculationType, data)
        while maxTryCount > 0:
            data = self.getTaskResult(task["taskId"])
            if data["result"] is not None:
                return data
            else:
                maxTryCount = maxTryCount - 1
                time.sleep(tryInterval)
        raise RhoovaError("Task created but result timed out. taskId : " + task["taskId"])

    def createTaskTransaction(self, taskTransaction: TaskTransaction):
        url = self.config.apiUrl + "/transactions"
        data = {
            'tasks': taskTransaction.tasks,
            'commonData': taskTransaction.commonData,
            'params': taskTransaction.params
        }
        response = requests.post(url=url, data=json.dumps(data), headers={
            'Content-type': 'application/json',
            'ekx-api-key': self.config.apiKey,
            'ekx-api-secret': self.config.apiSecret
        })
        if response.status_code == 200:
            return json.loads(response.text)
        else:
            raise RhoovaError(response.text)

    def getTaskTransaction(self, transactionId):
        url = self.config.apiUrl + "/transactions/" + transactionId
        response = requests.get(url=url, headers={
            'Content-type': 'application/json',
            'ekx-api-key': self.config.apiKey,
            'ekx-api-secret': self.config.apiSecret
        })
        if response.status_code == 200:
            data = json.loads(response.text)
            return data
        else:
            raise RhoovaError(response.text)

    def loadData(self, file, type: DataType, name):
        if not isinstance(type, DataType):
            raise TypeError('Data type must be an instance of DataType')
        url = self.config.apiUrl + "/data-sources"
        response = requests.post(url=url, data=json.dumps({"file": file, "name": name, "type": type.value}), headers={
            'Content-type': 'application/json',
            'ekx-api-key': self.config.apiKey,
            'ekx-api-secret': self.config.apiSecret
        })
        if response.status_code == 200:
            return json.dumps({"ID": json.loads(response.text)['pid'],
                               "DATA": (json.loads(json.loads(json.loads(response.text)['data'])['data'])),
                               "NAME": (json.loads(response.text)['name']),
                               "TYPE": DataType(json.loads(response.text)['type']).name}, indent=4)
        else:
            raise RhoovaError(response.text)

    def getData(self, id):
        url = self.config.apiUrl + "/data-sources/" + id
        response = requests.get(url=url, headers={
            'Content-type': 'application/json',
            'ekx-api-key': self.config.apiKey,
            'ekx-api-secret': self.config.apiSecret
        })
        if response.status_code == 200:
            return json.dumps({"ID": json.loads(response.text)['pid'],
                               "DATA": (json.loads(json.loads(json.loads(response.text)['data'])['data'])),
                               "NAME": (json.loads(response.text)['name']),
                               "TYPE": DataType(json.loads(response.text)['type']).name}, indent=4)
        else:
            raise RhoovaError(response.text)
