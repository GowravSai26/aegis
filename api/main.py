from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import disputes, health

load_dotenv()

app = FastAPI(title="AEGIS", description="Autonomous Chargeback Defense System", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://aegis-zeta-ten.vercel.app/"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(disputes.router)
