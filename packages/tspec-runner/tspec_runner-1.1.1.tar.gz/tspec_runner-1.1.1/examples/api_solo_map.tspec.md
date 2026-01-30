# Solo Map API connectivity

```tspec
suite:
  name: "solo-map-api"
  tags: [http, postman]
  artifact_dir: "artifacts"
  default_timeout_ms: 10000
  fail_fast: true

cases:
  - id: SOLO-API-001
    title: "GET https://api.solo-map.app/"
    steps:
      - do: http.request
        with:
          url: "https://api.solo-map.app/"
          expect_status: 200
          timeout: 10
```
