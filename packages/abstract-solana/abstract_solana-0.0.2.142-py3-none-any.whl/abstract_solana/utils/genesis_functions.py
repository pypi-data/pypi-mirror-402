from abstract_apis import get_headers,get_response,get_text_response,load_inner_json
from abstract_solcatcher import call_solcatcher_db,async_call_solcatcher_py,async_make_rate_limited_call
import asyncio
import asyncio,httpx,logging
def get_block_time_from_txn(txnData):
    return int(get_any_value('txnDatablockTime') or 0)
def get_error_message_from_txn(txnData):
    return make_list(get_any_value(txnData,'err'))[0]
def get_errorless_txn_from_signature_array(signatureArray):
    return [sig for sig in signatureArray or [] if get_error_message_from_txn(sig) == None]
def return_oldest_from_signature_array(signatureArray,errorless=False):
    if errorless:
        signatureArray = get_errorless_txn_from_signature_array(signatureArray)
    if signatureArray and isinstance(signatureArray,list):
        if get_block_time_from_txn(signatureArray[0])<get_block_time_from_txn(signatureArray[-1]):
            return signatureArray[0].get('signature')
        return signatureArray[-1].get('signature')
def return_oldest_last_and_original_length_from_signature_array(signatureArray):
    return {"oldest":return_oldest_from_signature_array(signatureArray),
     "oldestValid":return_oldest_from_signature_array(signatureArray,errorless=True),
     "length":len(signatureArray or '')}
async def getGenesisSignature(address, limit=1000, before=None,encoding='jsonParsed',commitment=0,errorProof=True):
    method = "getGenesisSignature"
    validBefore=None
    oldest=None
    validOldest=None
    while True:
        signatureArray = await async_make_rate_limited_call(method ="getSignaturesForAddress",params=[address, {"limit":limit, "until":before}],solcatcherSettings={"getResponse":True,"getResult":'result'})
        original_length = len(signatureArray or '')
        signature_array_data = return_oldest_last_and_original_length_from_signature_array(signatureArray)
        oldest = signature_array_data.get('oldest',oldest) or oldest
        validOldest = signature_array_data.get('oldestValid',validOldest) or validOldest
        if original_length < limit or original_length == 0 or (original_length>0 and (oldest == validOldest or oldest == before) and last_sig != None):
            return validOldest




