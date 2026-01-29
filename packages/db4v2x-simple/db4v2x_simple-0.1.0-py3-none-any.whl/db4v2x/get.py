from .utils import merge_mec_data
from .redis import data_get_one_mec_multi_dtype


# multi mec and multi dtype
async def data_get(kv, mec_id_list: list, data_type_list: list, ts_list: list):
    all_mec_data = {data_type: {} for data_type in data_type_list}
    for mec_id in mec_id_list:
        cur_mec_data = await data_get_one_mec_multi_dtype(
            kv, mec_id, data_type_list, ts_list
        )
        merge_mec_data(all_mec_data, cur_mec_data)

    return all_mec_data
