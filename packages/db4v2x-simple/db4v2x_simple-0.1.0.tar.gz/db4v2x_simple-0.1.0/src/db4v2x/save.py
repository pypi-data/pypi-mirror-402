from .redis import data_save_one_mec_multi_dtype


# one mec and multi dtype
async def data_save(kv, mec_id: str, cur_frame):
    await data_save_one_mec_multi_dtype(kv, mec_id, cur_frame)
