import asyncio
import uuid
import orjson

from faststruct import deserialize

from .utils import merge_mec_data


# multi mec and multi dtype, remote
async def data_get_remote(
    mqtt,
    mec_id_list: list,
    data_type_list: list,
    ts_list: list,
    req_topic: str,
    resp_topic: str,
):
    all_mec_data = {data_type: {} for data_type in data_type_list}

    for mec_id in mec_id_list:
        tasks = [
            data_get_remote_one_mec_one_dtype(
                mqtt, mec_id, dt, ts_list, req_topic, resp_topic
            )
            for dt in data_type_list
        ]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        cur_mec_data = {
            dt: deserialize(payload) for dt, payload in zip(data_type_list, results)
        }
        merge_mec_data(all_mec_data, cur_mec_data)

    return all_mec_data


async def data_get_remote_one_mec_one_dtype(
    mqtt,
    server_mec_id: str,
    data_type: str,
    ts_list: list,
    req_topic: str,
    resp_topic: str,
) -> bytes:
    request_id = uuid.uuid4().hex
    req_t = req_topic.format(server_mec_id)
    resp_t = resp_topic.format(server_mec_id, request_id)

    cmd = {"request_id": request_id, "data_type": data_type, "ts_list": ts_list}

    loop = asyncio.get_running_loop()
    fut: asyncio.Future[bytes] = loop.create_future()

    # 一次性回调：收到 resp_t 就 set_result，然后立刻清理
    def _cb(client, userdata, msg):
        if msg.topic != resp_t:
            return
        if not fut.done():
            # 更稳：即使未来回调不在 loop 线程，也不会炸
            loop.call_soon_threadsafe(fut.set_result, msg.payload)

        # 卸载，避免堆积
        try:
            client.message_callback_remove(resp_t)
        except Exception:
            pass
        try:
            client.unsubscribe(resp_t)
        except Exception:
            pass

    # 先订阅 + 挂回调，再 publish（避免“先响应后订阅”）
    mqtt.subscribe(resp_t, qos=1)
    mqtt.message_callback_add(resp_t, _cb)
    mqtt.publish(req_t, payload=orjson.dumps(cmd), qos=1)

    try:
        return await asyncio.wait_for(fut, timeout=10)
    except asyncio.TimeoutError:
        try:
            mqtt.message_callback_remove(resp_t)
        except Exception:
            pass
        try:
            mqtt.unsubscribe(resp_t)
        except Exception:
            pass
        return None
