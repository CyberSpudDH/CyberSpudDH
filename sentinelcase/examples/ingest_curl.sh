#!/usr/bin/env bash
curl -X POST http://localhost:8000/api/v1/signals:ingest \
  -H "Authorization: Bearer <SOURCE_API_KEY>" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: 11111111-2222-3333-4444-555555555555" \
  -d '{"src_ip":"1.2.3.4","user":"ACME\\\\bob","url":"https://evil.example/login","sha256":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}'
