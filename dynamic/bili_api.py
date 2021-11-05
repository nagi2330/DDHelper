import requests
import time

# 默认每次请求后的等待时间（秒）
# 每台机器最多两个worker
DEFAULT_WAIT = 1.5

BLOCKED = False
BLOCKED_START_TIME = None

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4146.4 Safari/537.36'
}


class BlockedException(Exception):
    def __init__(self, msg):
        super(BlockedException, self).__init__(msg)


def default_wait():
    """
    每次请求后的等待时间，防止请求被拦截
    """
    time.sleep(DEFAULT_WAIT)


def check_response(rsp):
    """
    检查一个请求是否被拦截，拦截后将系统设置为BLOCKED模式，停止发送请求
    :param rsp:
    :return:
    """
    if rsp.status_code == 412:
        global BLOCKED, BLOCKED_START_TIME
        if not BLOCKED:
            set_blocked()


def set_blocked():
    """
    将当前状态设置为BLOCKED
    :return:
    """
    global BLOCKED, BLOCKED_START_TIME
    BLOCKED = True
    from django.utils import timezone
    import pytz
    BLOCKED_START_TIME = timezone.now().astimezone(pytz.timezone("Asia/Shanghai"))
    print(f"[{BLOCKED_START_TIME}] 当前机器或ip可能被b站拦截，已停止所有请求，请管理员手动处理")
    import celery.worker.control as control
    control.disable_events()
    print(f"已停止任务队列")


def check_security():
    """
    在尝试发出请求前做安全检测，默认延迟一段时间，并在被拦截时停止发送新的请求
    :return:
    """
    default_wait()
    if BLOCKED:
        raise BlockedException(f"[{BLOCKED_START_TIME}] 当前机器或ip可能被b站拦截，已停止所有请求，请管理员手动处理")


def get_data_if_valid(rsp, fallback_msg="unknown"):
    """
    如果rsp合理，则提取出data部分，否则返回None
    :param rsp: 需要做提取的json
    :param fallback_msg: rsp为None时的错误信息
    :return: json里的data部分, 发生错误时的错误信息
    """
    if rsp is None:
        return None, fallback_msg
    if rsp['code'] == 0:
        return rsp['data'], None
    else:
        return None, rsp['msg']


# noinspection PyTypeChecker
def space_history(host_uid: int, offset_dynamic_id: int):
    """
    获取动态列表
    :param host_uid: 用户id
    :param offset_dynamic_id: 起始动态id，默认为0（获取最新的动态），不包括这个id的动态
    :return:
    """
    check_security()
    rsp = requests.get(
        "https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/space_history",
        params={
            "visitor_uid": 0,
            "host_uid": host_uid,
            "offset_dynamic_id": offset_dynamic_id
        },
        headers=headers,
        timeout=2)
    check_response(rsp)
    if rsp.status_code != 200:
        return None
    else:
        return rsp.json()


# noinspection PyTypeChecker
def user_profile(mid: int):
    """
    获取b站用户数据
    :param mid: b站用户id
    :return:
    """
    check_security()
    rsp = requests.get(
        "https://api.bilibili.com/x/space/acc/info",
        params={
            "mid": mid,
            "jsonp": "jsonp"
        },
        headers=headers,
        timeout=2)
    check_response(rsp)
    if rsp.status_code != 200:
        print(rsp.status_code)
        print(rsp.json())
        return None
    else:
        return rsp.json()


if __name__ == '__main__':
    # print(space_history(557839, 5190712790698414))
    print(user_profile(489391680))

