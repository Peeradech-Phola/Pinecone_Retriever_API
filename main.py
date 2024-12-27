from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from retriever_api import router as retriever_api_router

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:4200",
    "https://ntl-gpt-staging.ibotnoi.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root route
@app.get("/")
async def root():
    return {"message": "Welcome to FastAPI server!"}

# Register routers
app.include_router(retriever_api_router)

