from elasticsearch import AsyncElasticsearch
from backend.app.config import get_settings

settings = get_settings()


class ElasticsearchService:
    def __init__(self):
        self.client: AsyncElasticsearch | None = None
        self.index = settings.elasticsearch_index

    async def connect(self):
        self.client = AsyncElasticsearch(settings.elasticsearch_url)

    async def close(self):
        if self.client:
            await self.client.close()

    async def index_violation(self, violation_data: dict):
        if not self.client:
            return
        try:
            await self.client.index(index=self.index, document=violation_data)
        except Exception:
            pass

    async def search_violations(self, query: str, filters: dict | None = None, size: int = 50):
        if not self.client:
            return {"hits": []}
        body = {
            "query": {
                "bool": {
                    "must": [{"multi_match": {"query": query, "fields": ["plate_number", "violation_type", "location"]}}],
                }
            },
            "size": size,
        }
        if filters:
            for key, value in filters.items():
                body["query"]["bool"]["filter"] = body["query"]["bool"].get("filter", [])
                body["query"]["bool"]["filter"].append({"term": {key: value}})
        try:
            return await self.client.search(index=self.index, body=body)
        except Exception:
            return {"hits": {"hits": []}}


es_service = ElasticsearchService()
