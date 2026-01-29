import struct,base58,time,requests,asyncio,time
from typing import Optional,Union
from solders.hash import Hash
from solders.keypair import Keypair
from solders.instruction import Instruction
from solana.rpc.types import TokenAccountOpts,TxOpts
from solana.transaction import Transaction
from abstract_solcatcher import getLatestBlockHash,sendTransaction,getTransaction
from abstract_utilities import get_any_value
from ..abstract_utils.pubkey_utils import Pubkey,get_pubkey
from spl.token.instructions import CloseAccountParams,close_account
from ..abstract_utils.constants import TOKEN_PROGRAM_ID_PUBKEY,LAMPORTS_PER_SOL,UNIT_PRICE,UNIT_BUDGET
from solders.compute_budget import set_compute_unit_limit, set_compute_unit_price
from .token_utils import get_token_balance,check_existing_token_account,get_token_price
from .pump_fun_keys import getKeys
def buildTxn(mint,payer_pubkey, amount, slippage, token_account,sol_in=0,token_price=0,token_balance=0,token_account_instructions=None,close_token_account=False,buy=True):
    # Get keys for the transaction, pass the token account's pubkey instead of the AccountMeta object
    keys = getKeys(mint, token_account=token_account, payer_pubkey=payer_pubkey,buy=buy)
    slippage_adjustment = 1 - (slippage / 100)
    sol_change = sol_in if buy else float(token_balance) * float(token_price)
    sol_change_with_slippage = sol_change * slippage_adjustment
    limit_sol_change = int(sol_change_with_slippage * LAMPORTS_PER_SOL)
    print(f"Max Sol {'Cost' if buy else 'Output'}:", sol_change_with_slippage)
    hex_data = bytes.fromhex("66063d1201daebea" if buy else "33e685a4017f83ad")
    data = bytearray()
    data.extend(hex_data)
    data.extend(struct.pack('<Q', amount))
    data.extend(struct.pack('<Q', limit_sol_change))
    swap_instruction = Instruction(PUMP_FUN_PROGRAM_PUBKEY, bytes(data), keys)
    blockHash = getLatestBlockHash(commitment="processed")
    recent_blockhash = get_any_value(blockHash,'blockhash')
    recent_blockhash = Hash.from_string(recent_blockhash)
    txn = Transaction(recent_blockhash=recent_blockhash, fee_payer=payer_pubkey)
    txn.add(set_compute_unit_price(UNIT_PRICE))
    txn.add(set_compute_unit_limit(UNIT_BUDGET))
    if buy and token_account_instructions:
        txn.add(token_account_instructions)
    txn.add(swap_instruction)
    if buy == False and close_token_account:
        close_account_instructions = close_account(CloseAccountParams(PUMP_FUN_PROGRAM_PUBKEY, token_account_pubkey, payer_pubkey, payer_pubkey))
        txn.add(close_account_instructions)
    return txn

def get_all_buy_sell_info(mint,payer_pubkey,token_balance=None,sol_in=0,buy=True):
    
        print("Owner Public Key:", payer_pubkey)
        mint_str = str(mint)
        if not get_pubkey(mint_str).is_on_curve():
            print('Mint public key is not on curve')
            return False,amount,token_balance,token_price,token_account,token_account_instructions
        mint_pubkey = get_pubkey(mint_str)
        token_account, token_account_instructions = check_existing_token_account(payer_pubkey, mint_pubkey)
        token_account_pubkey = get_pubkey(token_account)
        # Ensure the token_account is a valid Pubkey
        if not isinstance(token_account_pubkey, Pubkey):
            print("Failed to create or retrieve a valid token account Pubkey...")
            return False,amount,token_balance,token_price,token_account,token_account_instructions
        print("Token Account:", token_account)
        if not token_account:
            print("Failed to retrieve or create token account.")
            return False,amount,token_balance,token_price,token_account,token_account_instructions
        # Calculate token price
        token_price = get_token_price(mint_str)
        print(f"Token Price: {token_price:.20f} SOL")
        amount = int(LAMPORTS_PER_SOL * token_price)
        print("Calculated Amount:", amount)
        if buy == False:
            if token_balance == None:
                token_balance = get_token_balance(token_account,mint_str)
            print("Token Balance:", token_balance)
            if token_balance == 0:
                return False,amount,token_balance,token_price,token_account,token_account_instructions        
        return mint,amount,token_balance,token_price,token_account_pubkey,token_account_instructions

def pump_fun_sell(mint: str,payer_pubkey:Pubkey, token_balance: Optional[Union[int, float]] = None,  slippage: int = 25, close_token_account: bool = True) -> bool:
    mint,amount,token_balance,token_price,token_account,token_account_instructions = get_all_buy_sell_info(mint,payer_pubkey,token_balance=token_balance,buy=False)
    if not mint:
        return mint
    return buildTxn(mint=mint,
             payer_pubkey=payer_pubkey,
             amount=amount,
             slippage=slippage,
             sol_in=0,
             token_balance=token_balance,
             token_price=token_price,
             token_account=token_account,
             token_account_instructions=token_account_instructions,
             buy=False)

def pump_fun_buy(mint: str,payer_pubkey:Pubkey, sol_in: float = 0.001, slippage: int = 25) -> bool:
    mint,amount,token_balance,token_price,token_account,token_account_instructions = get_all_buy_sell_info(mint,payer_pubkey,sol_in=sol_in,buy=True)
    if not mint:
        return mint
    return buildTxn(mint=mint,
             payer_pubkey=payer_pubkey,
             amount=amount,
             slippage=slippage,
             sol_in=sol_in,
             token_balance=0,
             token_price=0,
             token_account=token_account,
             token_account_instructions=token_account_instructions,
             buy=True)
    return True
async def confirm_txn(txn_sig, max_retries=20, retry_interval=3):
    retries = 0
    while retries < max_retries:
        txn_res = await getTransaction(signature=str(txn_sig))
        if txn_res:
            print(f"\n\nhttps://solscan.io/tx/{str(txn_sig)}")
            return txn_res
        retries += 1
        print(f"Retrying... ({retries}/{max_retries})")
        await asyncio.sleep(retry_interval)
    print(f"Failed to confirm transaction after {max_retries} attempts.")
    return txn_sig

async def complete_txn(txn, payer_keypair,confirm=False):
    txn_sig = await sendTransaction(txn=txn, payer_keypair=payer_keypair, skip_preflight=True)  # Await this async call
    print("Transaction Signature", txn_sig)
    if confirm == False:
        return txn_sig
    confirm = await confirm_txn(txn_sig)  # Await confirmation

    while not confirm:
        print("Waiting for transaction confirmation...")
        await asyncio.sleep(1)  # Use asyncio.sleep instead of time.sleep to avoid blocking
        confirm = await confirm_txn(txn_sig)  # Await confirmation check again

    print("Transaction confirmed:", confirm)
    return confirm
def buy_pump(mint: str, payer_keypair: Pubkey, sol_in=None, slippage=None,confirm=False):
    sol_in = sol_in or 0.001
    slippage = slippage or 25
    payer_pubkey = get_pubkey(payer_keypair.pubkey())
    txn = pump_fun_buy(mint=mint, payer_pubkey=payer_pubkey, sol_in=sol_in, slippage=slippage)
    completed = asyncio.run(complete_txn(txn, payer_keypair,confirm=confirm))  # Await here since `complete_txn` is async
    if not completed:
        print("Buy transaction failed")
    return completed
        
def sell_pump(mint:str, payer_keypair:Pubkey, token_balance=None, slippage=None,confirm=False):
    slippage = slippage or 25
    payer_pubkey = get_pubkey(payer_keypair.pubkey())
    txn = pump_fun_sell(mint=mint, payer_pubkey=payer_pubkey, token_balance=token_balance, slippage=slippage)
    completed = asyncio.run(complete_txn(txn, payer_keypair,confirm=confirm))
    if not completed:
        print("sell transaction failed")
    return completed
