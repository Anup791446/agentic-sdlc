from fastapi import FastAPI
app = FastAPI()

@app.post('/shorten')
def shorten_url():
    return {'short_url': 'https://short.ly/abc123'}

@app.get('/{code}')
def redirect(code: str):
    return {'redirect': 'https://example.com'}
