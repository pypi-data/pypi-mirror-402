from typing import Dict

from db4v2x.utils import decode, mec_id_data_type2key


async def data_get_one_mec_multi_dtype(
    kv, mec_id: str, data_type_list: list, ts_list: list = []
) -> Dict[str, Dict]:
    key2ts_id_list = {}
    for data_type in data_type_list:
        key = mec_id_data_type2key(mec_id, data_type)

        # filter ts_id
        ts_id_list = await kv._redis.hkeys(key)
        ts_id_list = decode(ts_id_list)
        valid_ts_id_list = (
            [f for f in ts_id_list if int(f.split(":")[0]) in ts_list]
            if ts_list
            else ts_id_list
        )
        key2ts_id_list[key] = valid_ts_id_list

    # batch hget
    key2ts_id2value = await kv.batch_hget(key2ts_id_list)

    # key2ts_id2value -> data_type2ts_id2value
    data_type2ts_id2value = {}
    for data_type in data_type_list:
        key = mec_id_data_type2key(mec_id, data_type)
        data_type2ts_id2value[data_type] = key2ts_id2value[key]

    return data_type2ts_id2value
