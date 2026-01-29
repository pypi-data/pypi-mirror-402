import os

from .consts import DATA_KEY_MAP


def get_mec_id2slot_tag() -> dict:
    mec_id2slot_tag_str = os.environ.get("MEC_ID2SLOT_TAG")
    return dict(item.split("=") for item in mec_id2slot_tag_str.split(","))


def mec_tag(mec_id: str, mec_id2slot_tag: dict = get_mec_id2slot_tag()):
    slot_tag = mec_id2slot_tag[mec_id]
    return f"{{{slot_tag}}}"


def _ensure_key_format(data_type: str) -> str:
    if data_type not in DATA_KEY_MAP:
        raise ValueError(f"未知 data_type: {data_type}")
    return DATA_KEY_MAP[data_type]


def mec_id_data_type2key(mec_id: str, data_type: str) -> str:
    key_format = _ensure_key_format(data_type)
    key = key_format.format(mec_tag(mec_id))
    return key


def merge_mec_data(all_mec_data, one_mec_data):
    for data_type in one_mec_data:
        if data_type not in all_mec_data:
            all_mec_data[data_type] = {}
        all_mec_data[data_type].update(one_mec_data[data_type])


def decode(obj):
    if isinstance(obj, (bytes, bytearray)):
        return obj.decode("utf-8")

    elif isinstance(obj, dict):
        return {decode(k): decode(v) for k, v in obj.items()}

    elif isinstance(obj, list):
        return [decode(v) for v in obj]

    elif isinstance(obj, tuple):
        return tuple(decode(v) for v in obj)

    else:
        return obj
