import contextvars
import logging

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