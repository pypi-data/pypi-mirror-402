from typing_extensions import TypedDict
from dataclasses import dataclass

from ethereum.core import validator, ApiError
from .core import ApiMixin, ErrResponse

From = TypedDict('From', {'from': str})

class Transaction(From):
  blockHash: str
  blockNumber: str
  gas: str
  gasPrice: str
  maxFeePerGas: str
  maxPriorityFeePerGas: str
  hash: str
  input: str
  nonce: str
  to: str
  transactionIndex: str
  value: str
  type: str
  accessList: list
  chainId: str
  v: str
  r: str
  s: str
  yParity: str

class RpcResponse(TypedDict):
  result: Transaction
  id: int
  jsonrpc: str

ResponseType: type[RpcResponse|ErrResponse] = RpcResponse | ErrResponse # type: ignore
validate_response = validator(ResponseType)

@dataclass
class TransactionByHash(ApiMixin):
  async def transaction_by_hash(
    self, hash: str, chain_id: int = 1, *,
    validate: bool | None = None,
  ) -> Transaction:
    """Get transaction details by hash.
    
    Args:
    - `hash`: The hash of the transaction to get.
    - `chain_id`: The chain ID to get the block for. You can see supported chains [here](https://docs.etherscan.io/supported-chains).
    - `closest`: Whether to get the closest block before or after the given time.
    - `validate`: Whether to validate the response.

    > [Etherscan API Docs](https://docs.etherscan.io/api-reference/endpoint/ethgettransactionbyhash)
    """
    r = await self.authed_request(
      'GET', params={
      'module': 'proxy',
      'action': 'eth_getTransactionByHash',
      'txhash': hash,
      'chainid': chain_id,
    })
    data = validate_response(r.text)
    if 'jsonrpc' in data:
      return data['result']
    else:
      raise ApiError(data)