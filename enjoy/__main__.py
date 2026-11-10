"""Atalho:  python -m enjoy   (abre em http://localhost:8000)"""

import uvicorn

if __name__ == "__main__":
    print("\n  Enjoy no ar: abra http://localhost:8000 no navegador (Ctrl+C para desligar)\n")
    uvicorn.run("enjoy.frameworks_drivers.app:app", host="127.0.0.1", port=8000)
