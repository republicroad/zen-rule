
from contextlib import contextmanager
from contextvars import ContextVar
import argparse
import pymongo


SESSION = ContextVar("session", default=None)


@contextmanager
def transaction(client):
    with client.start_session() as session:
        with session.start_transaction():
            t = SESSION.set(session)
            try:
                yield
            finally:
                SESSION.reset(t)


def insert1(client):
    client.test.txtest1.insert_one({"data": "insert1"}, session=SESSION.get())


def insert2(client):
    client.test.txtest2.insert_one({"data": "insert2"}, session=SESSION.get())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="mongodb://localhost:27017")
    args = parser.parse_args()

    client = pymongo.MongoClient(args.url)

    # Create and lear collections, collections must be created outside the transaction
    insert1(client)
    client.test.txtest1.delete_many({})
    insert2(client)
    client.test.txtest2.delete_many({})

    with transaction(client):
        insert1(client)
        insert2(client)

    for doc in client.test.txtest1.find({}):
        print(doc)
    for doc in client.test.txtest2.find({}):
        print(doc)


if __name__ == "__main__":
    main()