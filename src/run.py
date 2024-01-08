import os
import sys
import json
import signal
import asyncio
from environs import Env
from loguru import logger


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src import bitcoin_cli
from src.log import setup_logging

setup_logging()

from src.main import handle_event
from src.data.processer.pgsql import Pgsql as DataProcesser
from src.data.redis_helper import RedisHelper
from src.alert import send_alert
from src.data.event.event import EventIndexer


class Run:
    """
    Class representing the main execution of the indexer.
    """

    def __init__(self):
        """
        Initialize the Run object.
        """
        self.set_signal()

        self.redis_helper = RedisHelper()
        self.data_processer = DataProcesser()
        self.stop_flag = False
        self.close_flag = False

        env = Env()
        env.read_env()
        self.start_block_height = env.int("CORE_START_BLOCK_HEIGHT")

        self.mempool_block_height = -1
        self.event_default_error = "not processed by indexer"

        self.default_block_confirmations = 6
        self.default_sleep_seconds = 10

        self.event_indexer = None

    def set_signal(self):
        """
        Set the signal handlers for the Run object.
        """
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGHUP, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

    def stop(self, signal_num, frame):
        """
        Stop the execution of the Run object.
        """
        if self.stop_flag == True and self.close_flag == True:
            sys.exit(0)
        self.stop_flag = True
        self.close_flag = True

    async def init(self):
        """
        Initialize the data processer.
        """
        await self.data_processer.init()

    async def close(self):
        """
        Close the Redis connection and data processer.
        """
        await self.redis_helper.close()
        await self.data_processer.close()
        await asyncio.sleep(3)

    async def load_snapshot(self):
        """
        Load the snapshot data into the database.
        """
        await self.data_processer.clear_all_tables()
        await self.data_processer.create_all_table()

        data_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "data/snapshot/")
        )

        # Load tokens from tokens.json
        with open(f"{data_path}/tokens.json", "r") as tokens_file:
            tokens_json = json.load(tokens_file)

        # Load holders from holders.json
        with open(f"{data_path}/holders.json", "r") as holders_file:
            holders_json = json.load(holders_file)

        tokens = []
        for token in tokens_json.values():
            token["circulating"] = token["minted"]
            tokens.append(token)

        logger.info("saving tokens ...")
        await self.data_processer.batch_save_tokens_in_dict(tokens)

        holders = [
            holder
            for token_holders in holders_json.values()
            for holder in token_holders
        ]
        for holder in holders:
            holder["original_balance"] = holder["balance"]

        logger.info("saving balances ...")
        await self.data_processer.batch_save_balances_in_dict(holders)

        return

    async def get_chain_current_block_height(self):
        """
        get the current max block height on chain
        """
        return await bitcoin_cli.get_block_count()

    async def get_latest_block_height(self):
        """
        Get the latest block height from Redis.
        """
        result = await self.redis_helper.get_current_block()
        if result is None:
            latest_block_height = self.start_block_height - 1
            return latest_block_height

        latest_block_height = int(result)
        return latest_block_height

    async def handle_block(self, block_height, is_pending=False):
        """
        Handle the events in a block.
        """
        try:
            events = await self.data_processer.get_events_by_block_height(block_height)
            if events is None:
                logger.error(f"Failed to get events by block height: {block_height}")
                self.stop_flag = True
                return

            logger.info(f"handling block: {block_height}, got {len(events)} events")

            for event in events:
                if is_pending is True and event.error != self.event_default_error:
                    continue
                await handle_event(event, self.data_processer, is_pending)
            return True
        except Exception as e:
            error = f"Failed to handle block: {block_height}, {e}"
            logger.exception(error)
            return False

    async def reprocess_block(self, block_height):
        """
        Reprocess a block and its previous blocks.
        """
        try:
            reprocess_block_height = 0
            for index in range(
                block_height - self.default_block_confirmations, block_height
            ):
                events = await self.data_processer.get_events_by_block_height(index)
                if events is None:
                    logger.error(
                        f"Failed to get events by block height: {block_height}"
                    )
                    self.stop_flag = True
                    return

                new_events = [
                    event for event in events if event.error == self.event_default_error
                ]

                if len(new_events) > 0:
                    reprocess_block_height = index
                    break

            if reprocess_block_height == 0:
                return

            self.stop_flag = True
            return True

        except Exception as e:
            error = f"Failed to reprocess block: {block_height}, {e}"
            logger.exception(error)
            await send_alert(error)
            self.stop_flag = True

        return

    async def restart_event_indexer(self, init_block_height):
        if self.event_indexer:
            await self.event_indexer.stop()
        self.event_indexer = EventIndexer(self.data_processer)
        await self.event_indexer.init()
        asyncio.create_task(self.event_indexer.run(init_block_height))

    async def run(self):
        """
        Run the main execution loop.
        """
        await self.data_processer.init_backup_height_table()
        start_block_height = self.start_block_height
        backup_block_height = await self.data_processer.get_backup_block_height()
        if backup_block_height:
            start_block_height = backup_block_height + 1
            await self.data_processer.restore_all_table()
        else:
            backup_block_height = start_block_height - 1
            logger.info("loading snapshot ...")
            await self.load_snapshot()
            logger.info("snapshot loaded")

        await self.restart_event_indexer(start_block_height)

        while not self.stop_flag:
            latest_block_height = await self.data_processer.get_min_unhandled_block_height()
            if latest_block_height is None:
                await self.handle_block(self.mempool_block_height, True)
                logger.debug(f"Waiting for new block ...")
                await asyncio.sleep(self.default_sleep_seconds)
                continue

            if await self.event_indexer.detect_reorg(latest_block_height):
                logger.warning("Reorg detected, restore tables")
                if await self.data_processer.get_backup_block_height():
                    await self.data_processer.restore_all_table()
                await self.restart_event_indexer(backup_block_height + 1)
                continue

            logger.info(f"Handle block {latest_block_height}")
            if not await self.handle_block(latest_block_height):
                self.stop_flag = True
                break
            backup_block_height = (await self.data_processer.get_backup_block_height()) or -1
            if latest_block_height - backup_block_height >= 12:
                await self.data_processer.backup_all_table()
                await self.data_processer.mark_backup_block_height(latest_block_height)
                logger.info(f"Backup on block {latest_block_height}")

        await self.event_indexer.stop()
        logger.info("Stopped")

    async def main(self):
        """
        Main entry point of the indexer.
        """
        await self.init()

        while not self.close_flag:
            await self.run()
            self.stop_flag = False

        await self.close()


if __name__ == "__main__":
    asyncio.run(Run().main())
