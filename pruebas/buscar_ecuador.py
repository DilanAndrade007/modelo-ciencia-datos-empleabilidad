import requests
import json

url = "https://linkedin-job-search-api.p.rapidapi.com/active-jb-7d"

querystring = {
    "limit": "10",
    "offset": "0",
    "title_filter": "\"Computación\"",
}

headers = {
    "x-rapidapi-key": "412298965fmsh3b6e92e951dc623p12e07bjsn9f945a31146b",
    "x-rapidapi-host": "linkedin-job-search-api.p.rapidapi.com"
}

response = requests.get(url, headers=headers, params=querystring)

jobs = response.json()

print(json.dumps(jobs, indent=2))

print("\n=== Resultados simplificados ===\n")
for job in jobs:
    print(job.get("title", "Sin título"), "-", job.get("url", "Sin URL"))
