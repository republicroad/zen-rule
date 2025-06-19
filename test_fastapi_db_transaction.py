#
# https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/#dependencies-with-yield
# 启动此模块测试
# 在项目根目录执行:
# uvicorn tests.fastapi.test_fastapi_db_transaction:app --log-config log_conf.json
# curl http://127.0.0.1:8000/db_transaction1
# curl http://127.0.0.1:8000/db_transaction2
# curl http://127.0.0.1:8000/db_transaction3
# curl http://127.0.0.1:8000/db_transaction4


import uvicorn
import asyncio
import contextlib
from typing import Any, AsyncIterator, Union
import logging
import dataclasses
import sys
import logging
from httpx import ASGITransport, AsyncClient

# #  %(pathname)s:%(lineno)d
# fmt_debug = '[%(asctime)s %(process)d] %(pathname)s:%(lineno)d %(levelname)s %(name)s %(funcName)s %(message)s'
# # '[%(asctime)s %(process)d] %(levelname)s %(name)s %(funcName)s %(message)s'
# fmt = '[%(asctime)s %(process)d]  %(levelname)s %(name)s %(funcName)s %(message)s'
# logging.basicConfig(stream=sys.stdout,
#                     level=logging.DEBUG,
#                     format=fmt_debug
#                     )
logger = logging.getLogger(__name__)
from pprint import pprint

import pytest
import psutil
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi import applications
from fastapi.staticfiles import StaticFiles
from fastapi import APIRouter, Depends
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.gallery.fastapi.dbpg import (get_db, get_session, get_session2, get_conn,
                              BrdeUser, select,
                              sessionmanager,
                              PG_HOST,
                            )

# 移除 sqlalchemy.engine.Engine 默认的 handler, 方便对日志进行统一管理
# 我们需要对日志查看事务的具体执行过程.
logging.getLogger("sqlalchemy.engine.Engine").handlers.clear()
# from tests.utils.tools import show_all_logging_handlers
# show_all_logging_handlers()


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # 初始化 关系型数据库连接池或连接
    # 初始化 redis 连接池或连接
    # 初始化 http client 连接池或连接
    pass
    yield
    # 关闭 关系型数据库连接池或连接
    # 关闭 redis 连接池或连接
    # 关闭 http client 连接池或连接
    pass
    # await app.state.redis_client.aclose()
    # await app.state.http_session.close()


# 是否将 lifespan 和 app 相关的构建放在 pytest fixture 汇总
app = FastAPI(lifespan=lifespan)


def netconn_tools(rip="", rport=0):
    p = psutil.Process()
    net_conns = p.net_connections(kind='inet')
    if rip and rport:
        net_conns = [i for i in net_conns if i.raddr and i.raddr[0]==rip and i.raddr[1]==rport]
    elif rip:
        net_conns = [i for i in net_conns if i.raddr and i.raddr[0]==rip]
    elif rport:
        net_conns = [i for i in net_conns if i.raddr and i.raddr[1]==rport]
    else:
        net_conns = [i for i in net_conns]
    net_conns = [i._asdict() for i in net_conns]
    return net_conns


@app.get("/db_transaction1")
async def db_transaction1(session: AsyncSession = Depends(get_db)):
    logger.info(f"db session:{session}", )
    logger.info(f"db session type:{type(session)}")
    result = await session.execute(select(BrdeUser))
    r1 = result.scalars().first()
    session.expunge(r1)
    res = dataclasses.asdict(r1)
    logger.info(res)
    netconns = netconn_tools(rip=PG_HOST)
    return {
            "in_transaction": session.in_transaction(),
            "res": r1,
            "net_connections": netconns,
            "desp": "传入开启事务的数据库连接, 用于比较简单的增删改业务. Depends(get_db)"}


@app.get("/db_transaction2")
async def db_transaction2(context: contextlib._AsyncGeneratorContextManager = Depends(get_session)):
    """
        ####### best practice ##########
        # Depends(sessionmanager.session)   
        # Depends(get_session)
    """
    logger.info(f"context:{context}", )
    logger.info(f"context type:{type(context)}")
    async with context as session:  # 事务块
        result = await session.execute(select(BrdeUser))
        r1 = result.scalars().first()
        res = dataclasses.asdict(r1)
        logger.info(res)
        # session.expunge(r1)  # 让 r1 在事务结束后也可以用.
        # 离开 with 上下文块后事务关闭
    netconns = netconn_tools(rip=PG_HOST)
    return {
            "in_transaction": session.in_transaction(),
            "res": res,
            "net_connections": netconns,
            "desp": "传入数据库连接池上下文管理器, 用于手动控制事务范围复杂事务, 主要用来避免在数据库事务中嵌套其他耗时比如 http 等第三方请求.Depends(get_session)"}


@app.get("/db_transaction3")
async def db_transaction3():
    """
        ####### best practice ##########
        异步上下文管理器需要使用 async with
    """
    context = get_session()
    async with context as session:
        result = await session.execute(select(BrdeUser))
        r1 = result.scalars().first()
        res = dataclasses.asdict(r1)
        session.expunge(r1)
    netconns = netconn_tools(rip=PG_HOST)
    return {
            "in_transaction": session.in_transaction(),
            "res": res,
            "net_connections": netconns,
            "desp": "不依赖 Depends 方法. 直接使用异步上下文管理器函数. async with"}


@app.get("/db_transaction4")
async def db_transaction4():
    """
        异步上下文管理器需要使用 async for
    """
    session_gen = get_db()
    async for session in session_gen:  # 这种生成器迭代只会返回一个元素.
        result = await session.execute(select(BrdeUser))
        r1 = result.scalars().first()
        session.expunge(r1)
        res = dataclasses.asdict(r1)
    netconns = netconn_tools(rip=PG_HOST)
    return {
            "in_transaction": session.in_transaction(),
            "res": res,
            "net_connections": netconns,
            "desp": "不依赖 Depends 方法. 直接使用异步生成器函数. async for"}


@pytest.mark.asyncio(loop_scope="session")
async def test_fastapi_dbtest():
    """
        在这个测试单独设置 pytest live log 配置.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://localhost"
    ) as aclient:
        await asyncio.sleep(0)
        logger.info("---------- test case 1 ----------")
        t1 = await aclient.get("/db_transaction1")
        logger.info(f"/db_transaction1 resp:{t1}")
        assert t1.status_code == 200
        body1 = t1.json()
        net_connections1 = body1["net_connections"]

        logger.info("---------- test case 2 ----------")
        t2 = await aclient.get("/db_transaction2")
        logger.info(f"/db_transaction2 resp:{t2}")
        assert t2.status_code == 200
        body2 = t2.json()
        net_connections2= body2["net_connections"]

        logger.info("---------- test case 3 ----------")
        t3 = await aclient.get("/db_transaction3")
        logger.info(f"/db_transaction3 resp:{t3}")
        assert t3.status_code == 200
        body3 = t3.json()
        net_connections3= body3["net_connections"]

        logger.info("---------- test case 4 ----------")
        t4 = await aclient.get("/db_transaction4")
        logger.info(f"/db_transaction4 resp:{t4}")
        assert t4.status_code == 200
        body4 = t4.json()
        net_connections4= body4["net_connections"]

        assert net_connections1[0]["laddr"] == net_connections2[0]["laddr"], "db_transaction2 复用了一个数据库连接db_transaction1."
        assert net_connections1[0]["laddr"] == net_connections3[0]["laddr"], "db_transaction3 复用了一个数据库连接db_transaction1."
        assert net_connections1[0]["laddr"] == net_connections4[0]["laddr"], "db_transaction4 复用了一个数据库连接db_transaction1."



# @pytest.mark.asyncio(loop_scope="session")
# async def test_fastapi_dbtest2():
#     client = TestClient(app)
#     # show_all_logging_handlers()
#     with TestClient(app) as client:
#         logger.info("---------- test case 1 ----------")
#         t1 = client.get("/db_transaction1")
#         logger.info(f"/db_transaction1 resp:{t1}")
#         assert t1.status_code == 200
#         body1 = t1.json()
#         net_connections1 = body1["net_connections"]

#         logger.info("---------- test case 2 ----------")
#         t2 = client.get("/db_transaction2")
#         logger.info(f"/db_transaction2 resp:{t2}")
#         assert t2.status_code == 200
#         body2 = t2.json()
#         net_connections2= body2["net_connections"]

#         logger.info("---------- test case 3 ----------")
#         t3 = client.get("/db_transaction3")
#         logger.info(f"/db_transaction3 resp:{t3}")
#         assert t3.status_code == 200
#         body3 = t3.json()
#         net_connections3= body3["net_connections"]

#         logger.info("---------- test case 4 ----------")
#         t4 = client.get("/db_transaction4")
#         logger.info(f"/db_transaction4 resp:{t4}")
#         assert t4.status_code == 200
#         body4 = t4.json()
#         net_connections4= body4["net_connections"]

#         assert net_connections1[0]["laddr"] == net_connections2[0]["laddr"], "db_transaction2 复用了一个数据库连接db_transaction1."
#         assert net_connections1[0]["laddr"] == net_connections3[0]["laddr"], "db_transaction3 复用了一个数据库连接db_transaction1."
#         assert net_connections1[0]["laddr"] == net_connections4[0]["laddr"], "db_transaction4 复用了一个数据库连接db_transaction1."