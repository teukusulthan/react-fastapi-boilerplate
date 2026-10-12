# Skills library (archived, not auto-loaded)

Claude Code auto-discovers every skill in [`.claude/skills/`](../skills/) and lists it in each agent's
context. The skills in this folder encode **domain recipes from other company projects**. They are not
part of this boilerplate's foundation, so they live here: out of the default context, but still
available on demand.

| Skill | Useful when a project needs… |
|---|---|
| [`fastapi-api-gateway`](fastapi-api-gateway/SKILL.md) | An API-gateway/proxy service: REST/SSE forwarding with SSRF protection, S3 offload of file responses, Kafka audit logging, gateway config CRUD. |
| [`fastapi-build-filter-elasticsearch`](fastapi-build-filter-elasticsearch/SKILL.md) | Turning dashboard filter DTOs into Elasticsearch bool queries (nested fields, index patterns, date ranges, sort, pagination). |
| [`fastapi-create-map`](fastapi-create-map/SKILL.md) | Creating maps, map layers and map-plugin widgets (ID generation, upsert lifecycle, Geoserver integration, widget references). |
| [`fastapi-render-map`](fastapi-render-map/SKILL.md) | A backend tile engine: MVT rendering, map analytics, GeoJSON and coordinate queries (the `/map/*` router that `reactjs-map` Pattern A expects). |
| [`fastapi-topic`](fastapi-topic/SKILL.md) | Topic/keyword monitoring: per-platform Elasticsearch queries, topic codes, cloning across dashboards, Excel import, cross-DB sync. |
| [`fastapi-data-management`](fastapi-data-management/SKILL.md) | A multi-database CRUD dispatcher (MongoDB, Elasticsearch, PostgreSQL, MySQL) with validation, audit logging and MDM-aware cascade delete. |
| [`reactjs-tactical-map`](reactjs-tactical-map/SKILL.md) | A tactical / command-center map on top of [`reactjs-map`](../skills/reactjs-map/SKILL.md): layer groups, incident types, sensor stores, the `TacticalMap` bridge. |

## Enabling a skill for a project

Copy it (or symlink it) into the active skills folder:

```bash
cp -r .claude/skills-library/fastapi-topic .claude/skills/
# or keep a single source of truth:
ln -s ../skills-library/fastapi-topic .claude/skills/fastapi-topic
```

Then add a row for it to the skill index in `AGENTS.md` §10 so other agents know it is active.
Links between library skills (for example `fastapi-topic` → `fastapi-build-filter-elasticsearch`) only
resolve when you enable the linked skill too.

**These skills need adapting.** Their snippets were written against an older backend/web foundation.
Each one starts with an "Adapting to the current foundation" section (or a domain-override note) that
maps the old helpers to this boilerplate's repository layer, envelope, RBAC and file placement. Read it
first, keep the domain logic, and build the module with the active foundation skills
(`fastapi-crud-collection`, `fastapi-api-design`, `fastapi-data`, `reactjs-map`, `reactjs-ui-design`).

This folder is excluded from `npm run docs:check` (apart from this README's links), because the archived
skills describe code from other projects.
