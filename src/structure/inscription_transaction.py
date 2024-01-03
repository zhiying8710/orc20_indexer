

class Inscription_Transaction:

    """
    CREATE TABLE "inscriptions_transaction" (
      "id" int NOT NULL AUTO_INCREMENT,
      "inscription_id" varchar(256) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT '' COMMENT '铭文id',
      "inscription_number" int DEFAULT NULL,
      "genesis_tx" tinyint(1) DEFAULT '0' COMMENT '是否是铭文铸造交易',
      "txid" varchar(256) NOT NULL COMMENT '交易id',
      "prev_txid" varchar(256) DEFAULT '' COMMENT '输入的铭文交易id',
      "prev_owner" varchar(256) DEFAULT '' COMMENT '发生交易前的拥有者',
      "current_owner" varchar(256) DEFAULT NULL COMMENT '发生交易后的拥有者',
      "location" varchar(256) DEFAULT NULL COMMENT '交易发生后铭文的location',
      "hash" varchar(256) DEFAULT NULL COMMENT '交易的hash',
      "version" int DEFAULT NULL COMMENT '发生交易时的铭文版本',
      "size" int DEFAULT NULL,
      "vsize" int DEFAULT NULL,
      "weight" int DEFAULT NULL,
      "lock_time" bigint DEFAULT NULL,
      "block_height" int DEFAULT NULL COMMENT '所在区块高度',
      "block_hash" varchar(256) DEFAULT NULL COMMENT '所在区块hash值',
      "block_index" bigint unsigned DEFAULT NULL COMMENT '交易在当前区块交易列表的下标位置',
      "market" varchar(32) DEFAULT '',
      "amount" int DEFAULT NULL COMMENT '交易金额',
      "fee" int DEFAULT NULL,
      "market_fee" int DEFAULT NULL,
      "input_value" int DEFAULT NULL,
      "output_value" int DEFAULT NULL,
      "confirmations" int DEFAULT NULL COMMENT '确认数',
      "time" int DEFAULT NULL,
      "block_time" int DEFAULT NULL,
      "confirmed" tinyint(1) DEFAULT '1',
      "handled" tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否已和铭文做关联处理',
      "create_time" timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY ("id"),
      UNIQUE KEY "inscriptions_transaction_inscription_id_IDX" ("inscription_id","txid"),
      UNIQUE KEY "inscriptions_transaction_inscription_id2_IDX" ("inscription_id","block_index"),
      KEY "idx_txid" ("txid"),
      KEY "idx_block_index" ("block_index"),
      KEY "idx_current_owner" ("current_owner"),
      KEY "idx_prev_owner" ("prev_owner"),
      KEY "inscriptions_transaction_handled_IDX" ("handled","block_index"),
      KEY "idx_inscription_market" ("market","inscription_id")
    );
    """

    def __init__(
            self,
            id: int,
            inscription_id: str,
            inscription_number: int,
            genesis_tx: bool,
            txid: str,
            prev_txid: str,
            prev_owner: str,
            current_owner: str,
            location: str,
            block_height: int,
            block_index: int,
            handled: bool
    ):
        self.id = id
        self.inscription_id = inscription_id
        self.inscription_number = inscription_number
        self.genesis_tx = genesis_tx
        self.txid = txid
        self.prev_txid = prev_txid
        self.prev_owner = prev_owner
        self.current_owner = current_owner
        self.location = location
        self.block_height = block_height
        self.block_index = block_index
        self.handled = handled

