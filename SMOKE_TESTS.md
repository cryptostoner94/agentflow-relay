# Smoke Tests

```bash
curl http://localhost:8000/health

curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"source_platform":"web","user_ref":"local","text":"hello"}'

curl http://localhost:8000/logs
```
