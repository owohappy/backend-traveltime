import uvicorn
import routes

if __name__ == "__main__":
    uvicorn.run(routes.api, host="0.0.0.0", port=8080)