import asyncio
import json
import os
import sys
from queue import Queue, Empty
from typing import Union, List

import sqlalchemy as sa

from aiomysql.sa import create_engine
from environs import Env
from loguru import logger
from sqlalchemy import func, select, bindparam

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from util import random_string
from src import bitcoin_cli, electrs_cli, ord_cli
from src.data.processer.interface import Interface


from src.structure import Inscription, Inscription_Transaction, Event


class EventIndexer:

    def __init__(self, data_processer: Interface):
        metadata = sa.MetaData()

        self.inscription = sa.Table(
            "inscription",
            metadata,
            sa.Column("id", sa.BIGINT, primary_key=True, unique=True),
            sa.Column("inscription_id", sa.String(255)),
            sa.Column("inscription_number", sa.BIGINT),
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

    @staticmethod
    def get_block_index_range(block_height: int):
        return int(str(block_height) + "0000"), int(str(block_height) + "9999")

    @staticmethod
    def get_block_index(block: dict, txid: str):
        txids = block['tx']
        idx = txids.find(txid)
        height = block['height']
        sidx = str(idx)
        return int(str(height) + '0' * (4 - len(sidx)) + sidx)

    async def close(self):
        try:
            self.engine.close()
            await self.engine.wait_closed()
        except Exception as e:
            error = f"Mysql::close: Failed close database connection {e}"
            logger.exception(error)
            raise Exception(error)

    async def is_block_all_inscription_transactions_handled(self, block_height: int) -> bool:
        try:
            async with self.engine.acquire() as conn:
                min_block_index, max_block_index = self.get_block_index_range(block_height)
                unhandled = await conn.scalar(select([func.count(self.inscription_transaction.c.id)])
                .where(
                    self.inscription_transaction.c.block_index >= min_block_index
                ).where(
                    self.inscription_transaction.c.block_index <= max_block_index
                ).where(
                    self.inscription_transaction.c.handled == False
                ))
                handled = await conn.scalar(select([func.count(self.inscription_transaction.c.id)])
                .where(
                    self.inscription_transaction.c.block_index >= min_block_index
                ).where(
                    self.inscription_transaction.c.block_index <= max_block_index
                ).where(
                    self.inscription_transaction.c.handled == True
                ))
                return unhandled == 0 and handled > 0
        except Exception as e:
            error = f"Mysql::is_block_all_inscription_transactions_handled: Failed to detect block txs are all handled or not {e}"
            logger.exception(error)
            raise Exception(error)

    async def get_block_inscription_transactions(self, block_height: int) -> Union[list[Inscription_Transaction], None]:
        try:
            async with self.engine.acquire() as conn:
                min_block_index, max_block_index = self.get_block_index_range(block_height)
                query = self.inscription_transaction.select().where(
                    self.inscription_transaction.c.block_index >= min_block_index
                ).where(
                    self.inscription_transaction.c.block_index <= max_block_index
                )
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
            logger.exception(error)
            raise Exception(error)

    async def get_inscription_content_by_id(self, inscription_id: str):
        return (await ord_cli.get_inscription_content(inscription_id)).decode('utf-8')

    async def get_inscription_by_ids(self, inscription_ids: List[str]) -> Union[list[Inscription], None]:
        if not inscription_ids:
            return []
        try:
            async with self.engine.acquire() as conn:
                query = self.inscription.select().where(self.inscription.c.inscription_id.in_(bindparam('inscription_ids', expanding=True)))
                result = await conn.execute(query, params={'inscription_ids': inscription_ids})
                records = await result.fetchall()
                if records is None:
                    return None
                return [Inscription(**record) for record in records]
        except Exception as e:
            error = f"Mysql::get_inscription_by_ids: Failed to get inscriptions {e}"
            logger.exception(error)
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
            logger.exception(error)
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
            logger.exception(error)
            raise Exception(error)

    async def get_inscription_transactions_by_txid(self, txid: str) -> Union[list[Inscription_Transaction], None]:
        try:
            async with self.engine.acquire() as conn:
                query = self.inscription_transaction.select().where(
                    self.inscription_transaction.c.txid == txid
                )
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
            logger.exception(error)
            raise Exception(error)

    async def get_block(self, block_height):
        block_hash = await bitcoin_cli.get_block_hash(block_height)
        return await bitcoin_cli.get_block(block_hash, 1)

    async def detect_reorg(self, block_height):
        if not self.blocks:  # FIXME
            return False
        cached_prev_block = self.blocks[block_height - 1]
        block = await self.get_block(block_height)
        return not cached_prev_block['hash'] == block['previousblockhash']

    async def stop(self):
        logger.warning("Waiting event indexer stop...")
        self.stopped = True
        while self.running:
            await asyncio.sleep(1)

    async def process_tx(self, block):
        block_height = block['height']
        block_time = block['time']

        while not self.stopped and not await self.is_block_all_inscription_transactions_handled(block_height):
            logger.info(f"Waiting for {block_height} all txs to be handled")
            await asyncio.sleep(1)
            continue

        inscription_transactions = None
        while not self.stopped:
            inscription_transactions = await self.get_block_inscription_transactions(block_height)
            if [1 for inscription_transaction in inscription_transactions if not inscription_transaction.handled]:
                logger.info(f"Waiting for {block_height} all txs to be handled")
                await asyncio.sleep(1)
                continue
            break

        logger.info(f"Got {block_height} {len(inscription_transactions)} txs")
        inscriptions = {inscription.inscription_id: inscription for inscription in await self.get_inscription_by_ids([inscription_tx.inscription_id for inscription_tx in inscription_transactions])}
        tx_queue = Queue()
        for tx in inscription_transactions:
            tx_queue.put_nowait(tx)

        async def _process():
            while not self.stopped:
                try:
                    inscription_transaction = tx_queue.get_nowait()
                except Empty:
                    break
                else:
                    if inscription_transaction.inscription_number < 0:
                        continue
                    inscription_id = inscription_transaction.inscription_id
                    # logger.info(f"Will process {block_height} {inscription_id} {inscription_transaction.txid}")
                    inscription = inscriptions.get(inscription_id)
                    if not inscription:
                        inscription = await self.get_inscription_by_id(inscription_id)
                    content_type = (inscription.content_type or '').lower()
                    if not ('text' in content_type or 'json' in content_type):
                        continue
                    content = inscription.content
                    if not content:
                        content = await self.get_inscription_content_by_id(inscription_id)
                    if not content:
                        continue
                    try:
                        content_json = json.loads(content)
                    except:
                        continue
                    else:
                        if not type(content_json) == dict or not content_json.get("p", "").lower() == "orc-20":
                            continue
                        op = content_json.get("op", "").lower()
                        if not op:
                            continue
                        logger.info(f"Produce new event on {block_height} {inscription_id} {inscription_transaction.txid}")
                        await self.data_processer.save_event(Event(
                            id=random_string(16),
                            event_type="INSCRIBE" if inscription_transaction.genesis_tx else "TRANSFER",
                            block_height=block_height,
                            block_index=inscription_transaction.block_index,
                            timestamp=block_time,
                            inscription_id=inscription_id,
                            inscription_number=inscription.inscription_number,
                            sender=inscription_transaction.current_owner if inscription_transaction.genesis_tx else inscription_transaction.prev_owner,
                            receiver=inscription_transaction.current_owner,
                            content=content_json,
                            operation=op,
                            handled=True
                        ))

        done, _ = await asyncio.wait([
            asyncio.create_task(_process()) for _ in range(20)
        ])
        for fut in done:
            ex = fut.exception()
            if ex:
                raise ex
        await self.data_processer.mark_block_events_as_unhandled(block_height)
        logger.info(f'Mark {block_height} events to unhandled')

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
                    if block_height > current_block_height or block_height < current_block_height - 12:
                        self.blocks.pop(block_height)

                if not self.stopped and not await bitcoin_cli.get_block_hash(current_block_height):
                    logger.info('Waiting for new block')
                    await asyncio.sleep(5)
                    continue

                if not self.stopped:
                    logger.info(f"Process block {current_block_height}")
                    current_block = await self.get_block(current_block_height)
                    logger.info(f"Got block {current_block_height}")
                    self.blocks[current_block_height] = current_block

                    while not self.stopped:
                        await self.data_processer.delete_event_by_block(current_block_height)
                        logger.info(f"Clear {current_block_height} events")
                        try:
                            await self.process_tx(current_block)
                            break
                        except Exception as e:
                            logger.exception("Process txs error, retry")
                            await asyncio.sleep(5)

                    current_block_height += 1

            self.running = False
        except Exception as e:
            logger.exception("Event indexer running into error")
            raise e
        finally:
            await self.close()
