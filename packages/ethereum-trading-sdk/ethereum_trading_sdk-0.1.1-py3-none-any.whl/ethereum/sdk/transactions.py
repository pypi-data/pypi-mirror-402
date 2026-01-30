from typing_extensions import AsyncIterable, Sequence, Iterable
from dataclasses import dataclass, replace
from decimal import Decimal
from collections import defaultdict
from datetime import datetime, timezone

from web3 import Web3

from trading_sdk.util import ChunkedStream
from trading_sdk.reporting import (
  Transactions as TransactionsTDK, Transaction,
  EthereumTransaction, ERC20Transfer,
  Operation
)

from ethereum.sdk.core import EtherscanMixin
from ethereum.etherscan import tx_value, tx_fee, token_value
from ethereum.etherscan.transactions import Transaction as NativeTransaction
from ethereum.etherscan.token_transactions import TokenTransaction


def parse_transfer(tx: TokenTransaction, address: str) -> ERC20Transfer.Transfer:
  to_address = Web3.to_checksum_address(tx['to'])
  from_address = Web3.to_checksum_address(tx['from'])
  return ERC20Transfer.Transfer(
    sender_address=from_address, recipient_address=to_address,
    contract_address=tx['contractAddress'], value=token_value(tx),
    direction='IN' if to_address == address else 'OUT',
  )

async def parse_transactions(
  self: EtherscanMixin,
  native_transactions: Iterable[NativeTransaction],
  token_transactions: Iterable[TokenTransaction],
) -> AsyncIterable[Operation]:

  tx_idx = {tx['hash']: tx for tx in native_transactions}
  token_tx_idx = defaultdict[str, list[TokenTransaction]](list)
  for tok_tx in token_transactions:
    token_tx_idx[tok_tx['hash']].append(tok_tx)

  for hash in set(tx_idx).union(token_tx_idx):
    if (token_txs := token_tx_idx.get(hash, [])): # ERC-20 transfer
      time = datetime.fromtimestamp(int(token_txs[0]['timeStamp']))
      if (tx := tx_idx.get(hash)) is not None: # Initiated
        from_address = Web3.to_checksum_address(tx['from'])
        to_address = Web3.to_checksum_address(tx['to'])
        yield ERC20Transfer(
          id=hash, time=time, details=tx,
          tx_hash=hash, chain_id=self.chain_id,
          from_address=from_address, to_address=to_address,
          fee=tx_fee(tx),
          transfers=[parse_transfer(tok_tx, self.address) for tok_tx in token_txs]
        )
      else: # Received
        tx = await self.client.transaction_by_hash(hash, self.chain_id)
        from_address = Web3.to_checksum_address(tx['from'])
        to_address = Web3.to_checksum_address(tx['to'])
        yield ERC20Transfer(
          id=hash, time=time, details=tx,
          tx_hash=hash, chain_id=self.chain_id,
          from_address=from_address, to_address=to_address,
          fee=None,
          transfers=[parse_transfer(tok_tx, self.address) for tok_tx in token_txs]
        )
    else: # Native transaction
      tx = tx_idx[hash]
      time = datetime.fromtimestamp(int(tx['timeStamp']))
      from_address = Web3.to_checksum_address(tx['from'])
      to_address = Web3.to_checksum_address(tx['to'])
      yield EthereumTransaction(
        id=hash, time=time, details=tx,
        tx_hash=hash, chain_id=self.chain_id,
        from_address=from_address, to_address=to_address,
        value=tx_value(tx), fee=tx_fee(tx),
      )

class AutoDetect:
  ...

AUTO_DETECT = AutoDetect()

@dataclass
class Transactions(EtherscanMixin, TransactionsTDK):
  tz: timezone | AutoDetect = AUTO_DETECT
  """Timezone of the API times (defaults to the local timezone)."""

  @property
  def timezone(self) -> timezone:
    if isinstance(self.tz, AutoDetect):
      return datetime.now().astimezone().tzinfo # type: ignore
    else:
      return self.tz

  def add_tz(self, tx: Transaction) -> Transaction:
    op = replace(tx.operation, time=tx.operation.time.replace(tzinfo=self.timezone))
    return replace(tx, operation=op, postings=[replace(p, time=p.time.replace(tzinfo=self.timezone)) for p in tx.postings])

  async def _transactions_impl(
    self, start: datetime, end: datetime
  ) -> AsyncIterable[Sequence[Transaction]]:
    start_block = await self.client.block_by_time(start, self.chain_id, closest='after')
    end_block = await self.client.block_by_time(min(end, datetime.now()), self.chain_id, closest='before')
    native_transactions = await ChunkedStream(self.client.transactions_paged(self.address, self.chain_id, start_block=start_block, end_block=end_block))
    token_transactions = await ChunkedStream(self.client.token_transactions_paged(self.address, self.chain_id, start_block=start_block, end_block=end_block))
    async for op in parse_transactions(self, native_transactions, token_transactions):
      tx = Transaction(operation=op, postings=op.all_postings)
      yield [self.add_tz(tx)]
