# ORC-20 Nirvana Upgrade Indexer

This project serves as an indexing program for the ORC-20 protocol, developed in alignment with the latest official [documentation](https://orc20protocol.gitbook.io/orc-20-protocol/) following the ORC-20 Nirvana Upgrade.

## Project Directory Structure

The primary directory structure of the project is as follows:

- `src/data`: Contains snapshot data files and data processing scripts. The data source is from [ORC-20 Snapshot](https://github.com/ORC-20/snapshot).
- `src/handler`: Manages user operations by loading necessary data, conveying it to the indexer for execution, and then storing the processed data.
- `src/indexer`: Interprets and processes inscribed content according to protocol rules, performing logical operations.
- `src/structure`: Defines the data structures required by the indexer program.
- `src/register.py`: Registers handlers for all operations.
- `src/main.py`: Entry point of the indexing program. It processes each inscribe and transfer event individually.

## Indexing Program Functionality

The indexing program acts solely as a rule parser. You are free to choose any method for data storage, provided it conforms to the requirements defined in `src/data/processor/Interface.py`. In this codebase, we provide an example using PostgreSQL database for data processing.

It is important to note that the indexing program does not include the capture of inscribed data. It is necessary for you to have an independent data parsing solution to capture the inscribing and transferring of ORC-20 inscriptions. These transfer events should then be converted into the `Event` data structure and fed into main.py.

## Data Processing Workflow

This program assumes the existence of a data processing system that inputs ORC-20 inscription and transfer events into a PostgreSQL database, adhering to the data structure defined by `Event`. Additionally, it writes the latest block height data into Redis.

To facilitate this, we have included `redis_helper.py` to read the current latest block height. In PostgreSQL, we have implemented a method `get_events_by_block_height` to retrieve all events for a specified block height, in the order they occurred within each block.

The `run.py` script is responsible for continuously monitoring the latest events in the database. It extracts these events and passes them to the `handle_event` method in `main.py` for processing.

## Running the Program

If you have already stored event data in PostgreSQL following the above assumptions, you can execute the program using the following steps:

```bash
# Navigate to the project root directory
cd orc20_indexer

# Install Python packages
pip install -r requirements.txt

# Execute the run script
python src/run.py
```

## Ongoing Development

The indexer is still under active development. Currently, it supports the `Core` and `OTC` features of the ORC-20 protocol. Future updates will gradually include support for the `Order` feature.
