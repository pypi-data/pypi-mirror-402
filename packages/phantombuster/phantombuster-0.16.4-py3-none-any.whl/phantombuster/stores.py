import json
import hashlib
import os.path
from collections import Counter
from phantombuster.io_ import write_parquet, read_parquet
import uuid
import polars as pl

def save(result, dir, id=None):
    table, stats  = result

    if id is None:
        id = str(uuid.uuid4())

    if table is not None:
        write_parquet(table, os.path.join(dir, id+'.parquet'))
        r = True
    else:
        r = False

    with open(os.path.join(dir, id + f"_stats.json"), mode="w") as f:
        json.dump(stats, f)

    return (id, r)

def load(id_r, dir):
    id, r = id_r

    if r is True:
        table = read_parquet(os.path.join(dir, id+'.parquet'))
    else:
        table = None

    with open(os.path.join(dir, id + f"_stats.json")) as f:
        stats = json.load(f)

    return (table, stats)


def deduplicator_to_table(deduplicator, columns, lengths, types):
    size = len(deduplicator)
    rows = ((*items, readcount) for items, readcount in deduplicator.items())
    arrays = zip(*rows)
    t = pl.DataFrame([pl.Series(column, iterator, dtype=type) for iterator, type, column in zip(arrays, types, columns)])
    return t

