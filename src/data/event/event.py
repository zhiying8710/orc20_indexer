import asyncio
import json
import os
import sys
from queue import Queue, Empty
from typing import Union

import sqlalchemy as sa

from aiomysql.sa import create_engine
from environs import Env
from loguru import logger


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from src.data.event import InscriptionTransactionParser, InscriptionTransactionParseResult
from util import random_string
from src import bitcoin_cli, electrs_cli
from src.data.processer.interface import Interface


from src.structure import Inscription, Inscription_Transaction, Event


class EventIndexer:

    def __init__(self, data_processer: Interface):
        metadata = sa.MetaData()

        self.inscription = sa.Table(
            "inscription",
            metadata,
            sa.Column("id", sa.BIGINT, primary_key=True, unique=True),
            sa.Column("inscription_index", sa.BIGINT),
            sa.Column("inscription_number", sa.String(255)),
            sa.Column("owner", sa.String(255)),
            sa.Column("content_type", sa.String(255)),
            sa.Column("content", sa.Text),
            sa.Column("timestamp", sa.BIGINT),
            sa.Column("genesis_height", sa.BIGINT),
            sa.Column("location", sa.String(255)),
        )

        self.inscription_transaction = sa.Table(
            "inscription_transaction",
            metadata,
            sa.Column("id", sa.BIGINT, primary_key=True, unique=True),
            sa.Column("inscription_id", sa.String(255)),
            sa.Column("inscription_number", sa.BIGINT),
            sa.Column("genesis_tx", sa.BOOLEAN),
            sa.Column("txid", sa.String(255)),
            sa.Column("prev_txid", sa.String(255)),
            sa.Column("prev_owner", sa.String(255)),
            sa.Column("current_owner", sa.String(255)),
            sa.Column("location", sa.String(255)),
            sa.Column("block_height", sa.BIGINT),
            sa.Column("block_index", sa.BIGINT),
            sa.Column("handled", sa.BOOLEAN),
        )

        self.engine = None
        self.stopped = False
        self.running = True
        self.data_processer = data_processer
        self.blocks = {}

    async def init(self):
        env = Env()
        env.read_env()
        self.engine = await create_engine(
            user=env.str("MYSQL_USER"),
            password=env.str("MYSQL_PASSWD"),
            db=env.str("MYSQL_DB"),
            host=env.str("MYSQL_HOST"),
            port=env.int("MYSQL_PORT")
        )

    async def close(self):
        try:
            self.engine.close()
            await self.engine.wait_closed()
        except Exception as e:
            error = f"Mysql::close: Failed close database connection {e}"
            logger.error(error)
            raise Exception(error)

    async def get_inscription_by_id(self, inscription_id: str) -> Union[Inscription, None]:
        try:
            async with self.engine.acquire() as conn:
                query = self.inscription.select().where(self.inscription.c.inscription_id == inscription_id)
                result = await conn.execute(query)
                record = await result.fetchone()
                if record is None:
                    return None
                return Inscription(**record)
        except Exception as e:
            error = f"Mysql::get_inscription_by_id: Failed to get inscription {e}"
            logger.error(error)
            raise Exception(error)

    async def get_inscription_transaction_by_id(self, inscription_id: str, txid: str) -> Union[Inscription_Transaction, None]:
        try:
            async with self.engine.acquire() as conn:
                query = self.inscription_transaction.select().where(
                    self.inscription_transaction.c.inscription_id == inscription_id
                ).where(
                    self.inscription_transaction.c.txid == txid
                ).where(
                    self.inscription_transaction.c.handled == 1
                )
                result = await conn.execute(query)
                tx_record = await result.fetchone()
                if tx_record is None:
                    return None

                return Inscription_Transaction(**tx_record)
        except Exception as e:
            error = f"Mysql::get_inscription_transaction_by_id: Failed to get inscription transaction {e}"
            logger.error(error)
            raise Exception(error)

    async def get_inscription_transactions_by_txid(self, txid: str) -> Union[list[Inscription_Transaction], None]:
        try:
            async with self.engine.acquire() as conn:
                query = self.inscription_transaction.select().where(
                    self.inscription_transaction.c.txid == txid
                ).where(self.inscription_transaction.c.handled == 1)
                result = await conn.execute(query)
                tx_records = await result.fetchall()
                if tx_records is None:
                    return None

                ret_tx_records = [
                    Inscription_Transaction(**tx_record) for tx_record in tx_records
                ]

                return ret_tx_records
        except Exception as e:
            error = f"Mysql::get_block_inscription_transactions: Failed to get block inscription transactions {e}"
            logger.error(error)
            raise Exception(error)

    async def get_block(self, block_height):
        block_hash = await bitcoin_cli.get_block_hash(block_height)
        return await bitcoin_cli.get_block(block_hash, 1)

    async def detect_reorg(self, block_height):
        cached_prev_block = self.blocks[block_height - 1]
        block = await self.get_block(block_height)
        if block_height in self.blocks:
            self.blocks.pop(block_height)
        return not cached_prev_block['hash'] == block['previousblockhash']

    async def get_latest_block_height(self):
        return await self.data_processer.get_min_unhandled_block_height()

    async def stop(self):
        logger.warning("Waiting event indexer stop...")
        self.stopped = True
        while self.running:
            await asyncio.sleep(1)

    async def process_tx(self, block, txid_queue):
        block_height = block['height']
        block_time = block['time']

        async def _process():
            while not self.stopped:
                try:
                    idx, txid = txid_queue.get_nowait()
                except Empty:
                    break
                else:
                    tx_detail = await electrs_cli.get_tx(txid)
                    tx_status = tx_detail['status']
                    if not tx_status['confirmed']:
                        break
                    tx_witness = tx_detail['vin'][0]['witness']
                    if InscriptionTransactionParser.has_inscription(tx_witness):
                        inscription_txs = None
                        while not self.stopped:
                            inscription_txs = await self.get_inscription_transactions_by_txid(txid)
                            if inscription_txs:
                                break
                            await asyncio.sleep(1)
                        if not inscription_txs:
                            continue
                        for inscription_tx in inscription_txs:
                            if inscription_tx.genesis_tx:
                                result = InscriptionTransactionParser().parse_inscription(tx_witness)
                                if not result:
                                    inscription = await self.get_inscription_by_id(inscription_tx.inscription_id)
                                    if not inscription:
                                        continue
                                    result = InscriptionTransactionParseResult(None, inscription.content)
                                content = result.content
                                if not content:
                                    continue
                                try:
                                    content_json = json.loads(content)
                                except:
                                    continue
                                else:
                                    if not content_json.get("p", "").lower() == "orc-20":
                                        continue
                                    op = content_json.get("op", "").lower()
                                    if not op:
                                        continue
                                    await self.data_processer.save_event(Event(
                                        id=random_string(16),
                                        event_type="INSCRIBE",
                                        block_height=block_height,
                                        block_index=int(str(block_height) + ("0" * (4 - len(str(idx)))) + str(idx) + str(10000 + int(inscription_tx.location.split(':')[1]))),
                                        timestamp=block_time,
                                        inscription_id=inscription_tx.inscription_id,
                                        inscription_number=inscription_tx.inscription_number,
                                        sender=inscription_tx.current_owner,
                                        receiver=inscription_tx.current_owner,
                                        content=content_json,
                                        operation=op,
                                    ))
                        continue


                    vins = tx_detail['vin']
                    vouts = tx_detail['vout']
                    for vin_idx, vin in enumerate(vins):
                        if self.stopped:
                            break
                        prev_txid = vin['txid']
                        prev_inscription_txs = await self.get_inscription_transactions_by_txid(prev_txid)
                        if not prev_inscription_txs:
                            continue
                        for prev_inscription_tx in prev_inscription_txs:
                            if self.stopped:
                                break
                            if prev_inscription_tx.inscription_number < 0:
                                continue
                            inscription_id = prev_inscription_tx.inscription_id
                            inscription_tx = None
                            while not self.stopped:
                                inscription_tx = await self.get_inscription_transaction_by_id(inscription_id, txid)
                                if inscription_tx:
                                    break
                                await asyncio.sleep(1)
                            if not inscription_tx:
                                continue
                            if inscription_tx.inscription_number < 0:
                                continue
                            inscription = await self.get_inscription_by_id(inscription_id)
                            content = inscription.content
                            if not content:
                                continue
                            try:
                                content_json = json.loads(content)
                            except:
                                continue
                            else:
                                if not content_json.get("p", "").lower() == "orc-20":
                                    continue
                                op = content_json.get("op", "").lower()
                                if not op:
                                    continue
                                await self.data_processer.save_event(Event(
                                    id=random_string(16),
                                    event_type="TRANSFER",
                                    block_height=block_height,
                                    block_index=int(str(block_height) + ("0" * (4 - len(str(idx)))) + str(idx) + str(10000 + int(inscription_tx.location.split(':')[1]))),
                                    timestamp=block_time,
                                    inscription_id=inscription_id,
                                    inscription_number=prev_inscription_tx.inscription_number,
                                    sender=prev_inscription_tx.current_owner,
                                    receiver=vouts[vin_idx].get('scriptpubkey_address'),
                                    content=content_json,
                                    operation=op,
                                ))

        done, _ = await asyncio.wait([
            asyncio.create_task(_process()) for _ in range(10)
        ])
        for fut in done:
            ex = fut.exception()
            if ex:
                raise ex

    async def run(self, init_block_height):
        try:
            #  删除init_block_height(包含)之后的所有event
            logger.info(f"Start at block {init_block_height}")
            await self.data_processer.delete_event_by_block(init_block_height)
            logger.info("Event table cleaned")
            self.blocks[init_block_height - 1] = await self.get_block(init_block_height - 1)
            current_block_height = init_block_height
            while not self.stopped:
                for block_height in list(self.blocks.keys()):
                    if block_height >= current_block_height:
                        self.blocks.pop(block_height)

                if not self.stopped and not await bitcoin_cli.get_block_hash(current_block_height):
                    logger.info('Waiting for new block')
                    await asyncio.sleep(5)
                    continue

                if not self.stopped:
                    logger.info(f"Process block {current_block_height}")
                    current_block = await self.get_block(current_block_height)
                    self.blocks[current_block_height] = current_block
                    await self.data_processer.delete_event_by_block(current_block_height)
                    txid_queue = Queue()
                    for idx, txid in enumerate(current_block['tx']):
                        txid_queue.put_nowait((idx, txid))
                    await self.process_tx(current_block_height, txid_queue)
                    current_block_height += 1

            self.running = False
        except Exception as e:
            logger.error("Event indexer running into error", exc_info=e)
            raise e
        finally:
            await self.close()
