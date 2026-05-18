import os,sys,uvicorn
sys.path.insert(0,os.path.dirname(__file__))

uvicorn.run(
    "app.main:app",
    host="0.0.0.0",
    port=int(os.environ.get("PORT","10000")),
    log_level="info"
)
