from .redis import data_delete_one_mec_multi_dtype


# multi mec and multi data type
async def data_delete(kv, mec_ids, data_type_list, ts_list):
    for mec_id in mec_ids:
        await data_delete_one_mec_multi_dtype(kv, mec_id, data_type_list, ts_list)
