from web3 import Web3
import requests
import random
import string
import traceback
import time
from datetime import datetime
import websockets
import json
import asyncio
from win10toast import ToastNotifier

from pynostr.event import Event
from pynostr.key import PrivateKey
from pow import PowEvent
import binascii

# RPC
rpc_url = "wss://arbitrum-one.publicnode.com"

url = 'https://api-worker.noscription.org/inscribe/postEvent'

# 读取文件余额
def read():
    with open("count.txt", "w+") as file:
        val = file.read().strip()
        if val is None or val == "":
            val = 0
        file.write(str(val))
    return val

# 写文件余额|也就说修改文件余额
def write(val):
    with open("count.txt", "w+") as file:
        file.write(str(val))
    return val

# 跑的脚本
async def run_script():

    class color:
        PURPLE = '\033[95m'
        CYAN = '\033[96m'
        DARKCYAN = '\033[36m'
        BLUE = '\033[94m'
        GREEN = '\033[92m'
        YELLOW = '\033[93m'
        RED = '\033[91m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'
        END = '\033[0m'

    w3 = Web3(Web3.WebsocketProvider(rpc_url))   # RPC是wss协议时使用
    try:
        is_connected = w3.provider.is_connected()
        if is_connected:
            print(f"Connected to ARB node at {rpc_url}")
        else:
            print("Connection to ARB node failed. Please check the RPC URL.")
    except AttributeError:
        print("Unable to check connection status. Please ensure you are using an updated version of web3.py.")
        run_script()

    # 配置循环次数
    maxNumber = 10000

    # 设置挖矿难度
    pe = PowEvent(difficulty=21)
    for i in range(maxNumber):
        # 获取最新的区块号
        latest_block = w3.eth.block_number
        # 获取最新区块号的所以data信息
        newBlock = w3.eth.get_block(latest_block)

        # 获取最新的区块号信息
        blockNumber =  str(w3.eth.get_block(latest_block).get('number'))

        # 获取最新的交易hash值
        prefix = "0x" * 1  # 生成以 1 个0 开头的字符串
        hex_string = binascii.hexlify(newBlock['hash']).decode('utf-8')
        # 最新的交易hash值拼接
        blockHash= prefix+hex_string

        # 获取最新的id
        async with websockets.connect('wss://report-worker-2.noscription.org/') as websocket:
            # 接收消息并打印
            response = await websocket.recv()
            # 解析JSON
            data = json.loads(response)

            # 获取值
            event_id = data["eventId"]


            # 获取当前的时间戳
            created_at = int(time.time())
            nonce=''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
            print(color.RED + "postEvent接口的id:",event_id,"当前提交的created_at：",created_at,"当前提交的nonce：",nonce+color.RED)

            e_copy = Event(
                content="{\"p\":\"nrc-20\",\"op\":\"mint\",\"tick\":\"noss\",\"amt\":\"10\"}",
                kind=1,
                pubkey="64c8c82195bd811307b79d7b995302238f5097d84daf05e4242ddfab8e3f03ee",  # 进入https://nostrcheck.me/converter/转换，也就说把你nostr地址转换成16进制  我地址转换出来的是88709d7bbcbaa1a82b4a5c01a692cabdac450fbab67a386e37601fbe7daf7382
                tags=[
                    ["p", "9be107b0d7218c67b4954ee3e6bd9e4dba06ef937a93f684e42f730a0c3d053c"],
                    ["e", "51ed7939a984edee863bfbb2e66fdc80436b000a8ddca442d83e6a2bf1636a95",
                     "wss://relay.noscription.org/", "root"],
                ]
            )

            print(color.YELLOW + "最新区块：",blockNumber,"最新的交易hash值：",blockHash + color.YELLOW)
            e_copy.created_at = created_at
            e_copy.tags.append(["e", event_id, "wss://relay.noscription.org/", "reply"])
            e_copy.tags.append(["seq_witness", blockNumber, blockHash])
            e_copy.tags.append(["nonce", nonce, "21"])
            while True:
                e_copy = pe.mine(e_copy)
                if pe.calc_difficulty(e_copy) >= 21:
                    break
            # 还原被覆盖的参数 block_height
            e_copy.created_at = created_at
            sk = PrivateKey(bytes.fromhex(identity_pk.hex()))
            sig = sk.sign(bytes.fromhex(e_copy.id))
            e_copy.sig = sig.hex()
            event_json={
                "event":e_copy.to_dict()
            }
            #提交的data数据
            comintData= json.dumps(event_json)
            print("")
            print("event_json",comintData)

            url = "https://api-worker.noscription.org/inscribe/postEvent"
            headers = {
                "accept": "application/json, text/plain, */*",
                "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
                "content-type": "application/json",
                "sec-ch-ua": "\"Not A(Brand\";v=\"99\", \"Microsoft Edge\";v=\"121\", \"Chromium\";v=\"121\"",
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": "\"Windows\"",
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-site"
            }

            response = requests.post(url, headers=headers, data=comintData)
            if response.status_code==200 :
                print("挖掘成功, 提交结果",response.status_code)
                print("")

            #查询余额
            responses = requests.get("https://api-worker.noscription.org/indexer/balance?npub="+"npub1vnyvsgv4hkq3xpahn4aej5czyw84p97cfkhstepy9h06hr3lq0hquuz7d5")  # npub13pcf67auh2s6s262tsq6dyk2hkky2ra6kearsm3hvq0muld0wwpqzstrgk 为你的nostr地址
            data = responses.json()
            old = read()
            if data !=[]:
                if data[0]['balance'] > old:
                    toaster = ToastNotifier()
                    toaster.show_toast("挖到了！！！", f"新增{data[0]['balance'] - old}个, 总量{data[0]['balance']}", duration=5)
                    write(data[0]['balance'])
            else:
                print(color.DARKCYAN +"余额", 0)

# 运行脚本
if __name__ == "__main__":
    while True:
        try:
            # 初始化钱包
            identity_pk = PrivateKey.from_nsec("") # 你的nostr钱包私钥  具体找钱包的私钥教程看 https://m8k7lhxlwu.feishu.cn/wiki/BMSOwWujMie0fFk6bBtcj5MHn8X
            print("钱包地址",identity_pk.public_key.bech32())
            asyncio.get_event_loop().run_until_complete(run_script())
        except Exception as e:
            print(f"{datetime.now()} - 发生错误：{e}")
            print(traceback.format_exc())
            print("重新启动脚本...")
