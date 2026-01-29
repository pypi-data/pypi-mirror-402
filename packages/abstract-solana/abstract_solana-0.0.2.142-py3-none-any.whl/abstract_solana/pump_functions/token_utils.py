from ..abstract_utils.constants import TOKEN_DECIMAL_EXP,SOL_DECIMAL_EXP
from ..abstract_utils.pubkey_utils import Pubkey
from .pump_fun_keys import get_pump_fun_data
from abstract_solcatcher import getTokenAccountBalance,getTokenAccountsByOwner
from spl.token.instructions import create_associated_token_account, get_associated_token_address
from abstract_utilities import get_any_value
import requests
def get_token_balance(payer,mint: str):
    response = getTokenAccountBalance(str(payer),str(mint))
    response=response.get('value',response)
    ui_amount = get_any_value(response, "uiAmount") or 0
    return float(ui_amount)
def get_token_price(mint: str) -> float:
    try:
        # Get coin data
        coin_data = get_pump_fun_data(str(mint))
        if not coin_data:
            print("Failed to retrieve coin data...")
            return None
        virtual_sol_reserves = coin_data['virtual_sol_reserves'] / SOL_DECIMAL_EXP
        virtual_token_reserves = coin_data['virtual_token_reserves'] / TOKEN_DECIMAL_EXP
        token_price = virtual_sol_reserves / virtual_token_reserves
        print(f"Token Price: {token_price:.20f} SOL")
        return token_price
    except Exception as e:
        print(f"Error calculating token price: {e}")
        return None
def get_account_by_owner(payer, mint_str: str) -> dict:
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTokenAccountsByOwner",
        "params": [payer, {"mint": mint_str}, {"encoding": "jsonParsed"}]
    }
    response = requests.post(
        url="https://rpc.ankr.com/solana/c3b7fd92e298d5682b6ef095eaa4e92160989a713f5ee9ac2693b4da8ff5a370",
        json=payload
    )
    response_json = response.json()

    result = response_json.get('result')
    if not result or 'value' not in result:
        return None

    accounts = result.get('value', [])
    if accounts:
        return accounts[0]  # Return the first account found
    return None
def check_existing_token_account(owner: Pubkey, mint: Pubkey):
    try:
        account_data = get_account_by_owner(str(owner), str(mint))
        if account_data:
            token_account = account_data['pubkey']
            print(f"Existing token account found: {token_account}")
            return token_account, None
        else:
            print("No existing token account found. Creating a new one...")
            token_account = get_associated_token_address(owner, mint)
            token_account_instructions = create_associated_token_account(owner, owner, mint)
            return token_account, token_account_instructions
    except Exception as e:
        print(f"Error checking or creating token account: {e}")
        return None, None
