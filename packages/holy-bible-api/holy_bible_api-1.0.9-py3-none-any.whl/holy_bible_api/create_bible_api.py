from openapi_client import Configuration, ApiClient, DefaultApi

def create_bible_api(url: str | None = "https://holy-bible-api.com") -> DefaultApi:
    configuration = Configuration(host=url)
    client = ApiClient(configuration=configuration)
    api = DefaultApi(client)
    return api