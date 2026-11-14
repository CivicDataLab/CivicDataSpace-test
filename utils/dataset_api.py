# utils/dataset_api.py
#
# Public GraphQL lookups for the consumer dataset page tests. Aliased fields,
# so a whole catalogue costs one or two POSTs (the backend allows 1000/hour per IP).

from utils.usecase_api import gql

# The whole catalogue takes 7-9s on a warm dev; right after a deploy, with several
# workers asking at once, it went past 30s (deploy run 43580283334).
HEAVY_TIMEOUT = 90

CATALOGUE_QUERY = """
{
  datasets(includePublic: true, pagination: {limit: 500}) {
    id title description downloadCount accessType isIndividualDataset
    user { fullName }
    organization { name }
    tags { value }
    sectors { name }
    geographies { name }
    resources { id name type url noOfEntries fileDetails { file { name } } }
  }
  publishedUseCases { id urlSlug title datasets { id } }
  publishedCollaboratives { id urlSlug title datasets { id } }
}
"""


def chart_names(api, dataset_ids):
    """{dataset id: [chart name]} for the given datasets, in one request."""
    if not dataset_ids:
        return {}
    fields = " ".join(
        f'c{i}: getChartData(datasetId: "{d}") {{ ... on TypeResourceChart {{ name }} ... on TypeResourceChartImage {{ name }} }}'
        for i, d in enumerate(dataset_ids)
    )
    data = gql(api, "{ " + fields + " }", timeout=HEAVY_TIMEOUT)
    return {d: [c["name"] for c in data[f"c{i}"]] for i, d in enumerate(dataset_ids)}


def load_catalogue(api):
    """Published datasets plus which use cases / collaboratives contain each one."""
    data = gql(api, CATALOGUE_QUERY, timeout=HEAVY_TIMEOUT)
    links = {"usecases": {}, "collaboratives": {}}
    for kind, rows in (("usecases", data["publishedUseCases"]), ("collaboratives", data["publishedCollaboratives"])):
        for row in rows:
            for d in row["datasets"]:
                links[kind].setdefault(d["id"], []).append({"id": row["id"], "urlSlug": row["urlSlug"], "title": row["title"]})
    return data["datasets"], links
