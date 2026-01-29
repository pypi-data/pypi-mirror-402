from ..abstract_utils.pubkey_utils import Pubkey,get_pubkey,derive_bonding_curve,derive_associated_bonding_curve
from ..abstract_utils.log_message_functions import get_for_program_ids_info
from spl.token.instructions import create_associated_token_account, get_associated_token_address
from abstract_solcatcher import getGenesisSignature,getTransaction,getAccountInfo
from construct import Padding, Struct, Int64ul, Flag
from solana.transaction import AccountMeta, Transaction
import base64
from ..abstract_utils.constants import (PUMP_FUN_GLOBAL_PUBKEY,
                         PUMP_FUN_FEE_RECIPIENT_PUBKEY,
                         SYSTEM_PROGRAM_PUBKEY,
                         PUMP_FUN_EVENT_AUTHORITY_PUBKEY,
                         PUMP_FUN_PROGRAM_PUBKEY,
                         TOKEN_PROGRAM_ID_PUBKEY,
                         RENT_PUBKEY,
                         PUMP_FUN_ASSOC_TOKEN_ACC_PROG_PUBKEY)

# Change dictionary keys to lowercase and replace spaces with underscores
def change_keys_lower(dict_obj):
    new_dict = {}
    for key, value in dict_obj.items():
        new_dict[key.lower().replace(' ', '_')] = value
    return new_dict

# Predefined map for different transaction types
def get_create_map():
    return [
        {'instruction_number': '1', 'instruction_name': 'Mint', 'token_address': 'AkAUSJg1v9xYT3HUxdALH7NsrC6owmwoZuP9MLw8fxTL', 'token_name': '3CAT'},
        {'instruction_number': '2', 'instruction_name': 'Mint Authority', 'token_address': 'TSLvdd1pWpHVjahSpsvCXUbgwsL3JAcvokwaKt1eokM', 'token_name': 'Pump.fun Token Mint Authority'},
        {'instruction_number': '3', 'instruction_name': 'Bonding Curve', 'token_address': '9nhxvNxfSUaJddVco6oa6NodtsCscqCScp6UU1hZkfGm', 'token_name': 'Pump.fun (3CAT) Bonding Curve'},
        {'instruction_number': '4', 'instruction_name': 'Associated Bonding Curve', 'token_address': '889XLp3qvVAHpTYQmhn6cBpYSppV8Gi8E2Rgp9RH2vRy', 'token_name': 'Pump.fun (3CAT) Vault'},
        {'instruction_number': '5', 'instruction_name': 'Global', 'token_address': '4wTV1YmiEkRvAtNtsSGPtUrqRYQMe5SKy2uB4Jjaxnjf', 'token_name': '4wTV1YmiEkRvAtNtsSGPtUrqRYQMe5SKy2uB4Jjaxnjf'},
        {'instruction_number': '6', 'instruction_name': 'Mpl Token Metadata', 'token_address': 'metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s', 'token_name': 'Metaplex Token Metadata'},
        {'instruction_number': '7', 'instruction_name': 'Metadata', 'token_address': 'CH41RxpjSXHqr1vfLTVYJMsfNs2fBCCWoAE13tPihXh7', 'token_name': 'CH41RxpjSXHqr1vfLTVYJMsfNs2fBCCWoAE13tPihXh7'},
        {'instruction_number': '8', 'instruction_name': 'User', 'token_address': 'Fuy5MvbgzjSok1U8hH6mUY6WnLynzUextDxfEWMiTkn4', 'token_name': 'Fuy5MvbgzjSok1U8hH6mUY6WnLynzUextDxfEWMiTkn4'},
        {'instruction_number': '9', 'instruction_name': 'System Program', 'token_address': '11111111111111111111111111111111', 'token_name': 'System Program'},
        {'instruction_number': '10', 'instruction_name': 'Token Program', 'token_address': 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA', 'token_name': 'Token Program'},
        {'instruction_number': '11', 'instruction_name': 'Associated Token Program', 'token_address': 'ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL', 'token_name': 'Associated Token Account Program'},
        {'instruction_number': '12', 'instruction_name': 'Rent', 'token_address': 'SysvarRent111111111111111111111111111111111', 'token_name': 'Rent Program'},
        {'instruction_number': '13', 'instruction_name': 'Event Authority', 'token_address': 'Ce6TQqeHC9p8KetsN6JsjHK7UTZk7nasjjnr7XxXp9F1', 'token_name': 'Ce6TQqeHC9p8KetsN6JsjHK7UTZk7nasjjnr7XxXp9F1'},
        {'instruction_number': '14', 'instruction_name': 'Program', 'token_address': '6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P', 'token_name': 'Pump.fun'}
    ]

def get_txnTypesFromGenesisSignature(genesisSignature,commitment="finalized"):
    txn_data = getTransaction(genesisSignature,commitment=commitment)
    txn_data = get_for_program_ids_info(txn_data)
    for new_map in get_create_map():
        instructions = txn_data['transaction']['message']['instructions']
        inner_instructions = txn_data['meta']['innerInstructions'][0]['instructions']
        all_instructions = instructions + inner_instructions
        instruction = [inst for inst in all_instructions if len(inst.get('associatedAccounts', [])) > 13]
        txn_types = {create_index['instruction_name']: instruction[0]['associatedAccounts'][int(create_index['instruction_number']) - 1] for create_index in get_create_map()}
        if txn_types:
            txn_types['signature'] = genesisSignature
            break
    return txn_types

# Fetches and organizes transaction types based on provided mint
def getTxnTypes(mint):
    bonding_curve = str(derive_bonding_curve(mint)[0])
    bonding_curve_signature = getGenesisSignature(address=bonding_curve)
    return get_txnTypesFromGenesisSignature(bonding_curve_signature)
# Retrieve virtual reserves for a bonding curve using a structured layout
def get_virtual_reserves(bonding_curve: Pubkey):
    bonding_curve_struct = Struct(
        Padding(8),
        "virtualTokenReserves" / Int64ul,
        "virtualSolReserves" / Int64ul,
        "realTokenReserves" / Int64ul,
        "realSolReserves" / Int64ul,
        "tokenTotalSupply" / Int64ul,
        "complete" / Flag
    )
    account_info = getAccountInfo(account=str(bonding_curve[0]))
    
    if not account_info or 'value' not in account_info or 'data' not in account_info['value']:
        print("Failed to retrieve account info.")
        return None

    data_base64 = account_info['value']['data'][0]
    data = base64.b64decode(data_base64)
    parsed_data = bonding_curve_struct.parse(data)
    return parsed_data

# Retrieves comprehensive transaction and reserve data for the mint
def get_pump_fun_data(mint_str: str=None,signature=None,commitment="finalized"):
    if mint_str:
        txn_types = change_keys_lower(getTxnTypes(mint_str))
    if signature:
        txn_types = change_keys_lower(get_txnTypesFromGenesisSignature(signature,commitment=commitment))
    mint_str = mint_str or txn_types.get('mint')
    bonding_curve = derive_bonding_curve(mint_str)
    virtual_reserves = get_virtual_reserves(bonding_curve)
    if virtual_reserves is None:
        return None

    txn_types.update({
        "mint": mint_str,
        "bonding_curve": str(bonding_curve[0]),
        "associated_bonding_curve": str(derive_associated_bonding_curve(mint_str)),
        "virtual_token_reserves": int(virtual_reserves.virtualTokenReserves),
        "virtual_sol_reserves": int(virtual_reserves.virtualSolReserves),
        "token_total_supply": int(virtual_reserves.tokenTotalSupply),
        "complete": bool(virtual_reserves.complete)
    })
    
    return txn_types

def getKeys(mint_str,token_account,payer_pubkey,buy=True):
    MINT = get_pubkey(str(mint_str))
    bonding_curve = derive_bonding_curve(str(mint_str))
    associated_bonding_curve = derive_associated_bonding_curve(str(mint_str))
    BONDING_CURVE = get_pubkey(str(bonding_curve[0]))
    ASSOCIATED_BONDING_CURVE = get_pubkey(str(associated_bonding_curve))
    ASSOCIATED_USER = Pubkey.from_string(str(token_account))
    USER = Pubkey.from_string(str(payer_pubkey))
    PUMP_FUN_TOKEN_PROGRAM_SWITCH = TOKEN_PROGRAM_ID_PUBKEY if buy else PUMP_FUN_ASSOC_TOKEN_ACC_PROG_PUBKEY
    PUMP_FUN_RENT_PROGRAM_SWITCH = RENT_PUBKEY if buy else TOKEN_PROGRAM_ID_PUBKEY
    # Build account key list 
    keys = [
        AccountMeta(pubkey=PUMP_FUN_GLOBAL_PUBKEY, is_signer=False, is_writable=False),
        AccountMeta(pubkey=PUMP_FUN_FEE_RECIPIENT_PUBKEY, is_signer=False, is_writable=True),
        AccountMeta(pubkey=MINT, is_signer=False, is_writable=False),
        AccountMeta(pubkey=BONDING_CURVE, is_signer=False, is_writable=True),
        AccountMeta(pubkey=ASSOCIATED_BONDING_CURVE, is_signer=False, is_writable=True),
        AccountMeta(pubkey=ASSOCIATED_USER, is_signer=False, is_writable=True),
        AccountMeta(pubkey=USER, is_signer=True, is_writable=True),
        AccountMeta(pubkey=SYSTEM_PROGRAM_PUBKEY, is_signer=False, is_writable=False), 
        AccountMeta(pubkey=PUMP_FUN_TOKEN_PROGRAM_SWITCH, is_signer=False, is_writable=False),
        AccountMeta(pubkey=PUMP_FUN_RENT_PROGRAM_SWITCH, is_signer=False, is_writable=False),
        AccountMeta(pubkey=PUMP_FUN_EVENT_AUTHORITY_PUBKEY, is_signer=False, is_writable=False),
        AccountMeta(pubkey=PUMP_FUN_PROGRAM_PUBKEY, is_signer=False, is_writable=False)
    ]
    return keys
