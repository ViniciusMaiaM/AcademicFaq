import uvicorn
from core.app import start_application

if __name__ == "__main__":

    app = start_application()
    uvicorn.run(
        app, 
        host="0.0.0.0",
        port=8000,
    )