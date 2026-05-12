import requests

API_KEY = "AIzaSyBVPfEGtY1hwhHzjPaPuF3dxNpUU46CNgo"

endereco_teste = "Brasília, DF"

url = "https://maps.googleapis.com/maps/api/geocode/json"

params = {
    "address": endereco_teste,
    "key": API_KEY,
    "region": "br",
    "language": "pt-BR"
}

response = requests.get(url, params=params)
dados = response.json()

print(dados)