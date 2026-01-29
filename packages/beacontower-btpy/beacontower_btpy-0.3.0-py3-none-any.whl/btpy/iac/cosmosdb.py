import azure.cosmos.cosmos_client as cosmos_client
import azure.cosmos.exceptions as exceptions

from btpy import misc


def seed_default_provider(data):
    logger = misc.setup_logging()

    client = cosmos_client.CosmosClient(
        data["cosmosdb_endpoint"], {"masterKey": data["cosmosdb_primary_key"]}
    )
    try:
        database = client.get_database_client(data["cosmosdb_database_name"])
        container = database.get_container_client("Providers")
        defaultIothub = {
            "providerType": "iothub",
            "config": {
                "transport": "http",
                "httpConfig": {"host": data["iothub_provider_service_url"]},
            },
            "displayName": "Default Iot-Hub provider",
            "id": "defaultIotHubProvider",
            "type": "Provider",
        }
        container.upsert_item(defaultIothub)
    except exceptions.CosmosHttpResponseError as e:
        logger.error("run_sample has caught an error. {0}".format(e.message))
