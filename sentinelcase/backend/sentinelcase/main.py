from fastapi import FastAPI

from sentinelcase.api import audit, auth, cases, observables, signals, sources

app = FastAPI(title="SentinelCase", version="0.1.0")

app.include_router(auth.router)
app.include_router(sources.router)
app.include_router(signals.router)
app.include_router(cases.router)
app.include_router(observables.router)
app.include_router(audit.router)


@app.get("/health")
def health():
    return {"ok": True}
