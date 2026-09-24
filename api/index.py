from main import app

def handler(event, context):
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    import json
    return app