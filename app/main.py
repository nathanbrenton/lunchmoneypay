from fastapi import FastAPI

app = FastAPI(
    title="LunchMoneyPay",
    description="Mock third-party payment processor for Homesteady ChoreTracker.",
    version="0.1.0",
)


@app.get("/")
def read_root():
    return {
        "service": "LunchMoneyPay",
        "status": "running",
        "message": "Mock payment processor API is online.",
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
    }
