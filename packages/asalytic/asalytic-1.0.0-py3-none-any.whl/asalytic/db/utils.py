from pymongo import MongoClient
from asalytic.utils.env import load_mongo_credentials, load_db_name, load_contabo_mongo_credentials, load_asalytic_db_credentials


def get_db_client(db_type: str):
    if db_type == "mongo_cloud":
        username, password, uri = load_mongo_credentials()

        admin_cluster = f"mongodb+srv://{username}:{password}@{uri}"
        admin_client = MongoClient(admin_cluster)
        print('Cloud MongoDB initialized')
        return admin_client

    # if db_type == "contabo":
    #     host, port = load_contabo_mongo_credentials()
    #     print('Contabo MongoDB initialized')
    #     return MongoClient(host=host, port=port)

    if db_type == "asalytic_db":
        host, port = load_asalytic_db_credentials()
        print('Asalytic MongoDB initialized')
        return MongoClient(host=host, port=port)

    raise NotImplementedError(f'Invalid db_type: {db_type}')


def get_db():
    client = get_db_client()
    db_name = load_db_name()

    return client[db_name]
