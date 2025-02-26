import os

from py_clob_client.client import ClobClient
from py_clob_client.clob_types import ApiCreds
from dotenv import load_dotenv
from py_clob_client.constants import AMOY

load_dotenv()


def main():
    host = os.getenv("POLYMARKET_HOST")
    key = os.getenv("PK")
    creds = ApiCreds(
        api_key=os.getenv("CLOB_API_KEY"),
        api_secret=os.getenv("CLOB_SECRET"),
        api_passphrase=os.getenv("CLOB_PASS_PHRASE"),
    )
    chain_id = AMOY
    client = ClobClient(host, key=key, chain_id=chain_id, creds=creds)


    # print(client.get_market("0x68dac65c24b962829f3a3219f4444b2c88da7325acf100b91378023488dea20b"))
    # print(client.get_markets()) <- Totally useless
    print(client.get_sampling_markets())
    print("Done!")


main()