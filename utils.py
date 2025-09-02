import contextvars
import logging

###  contextvars 无法传递至 zen-engine 的 customHandler 中, 所以, 连接句柄等信息.
httpsession = contextvars.ContextVar('httpsession')


def get_state(sess_name):
    """
        sess_name: 
        1. http_session
        2. redis_connection
        3. postgresql connection
        4. xdb
    """
    pass
    c = {}
    # app.state[sess_name]

    return c[sess_name]