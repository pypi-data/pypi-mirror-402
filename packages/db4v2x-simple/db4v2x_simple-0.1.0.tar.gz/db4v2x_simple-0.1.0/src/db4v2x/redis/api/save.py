from typing import Dict
from collections import defaultdict

from db4v2x.utils import mec_id_data_type2key


async def data_save_one_mec_multi_dtype(kv, mec_id: str, last_frame: Dict[str, Dict]):
    key2ts_id2value = defaultdict(dict)
    for data_type, ts_id2value in last_frame.items():
        key = mec_id_data_type2key(mec_id, data_type)
        key2ts_id2value[key] = ts_id2value

    await kv.batch_hset(key2ts_id2value)
