import requests

email_text = """OBJET : Manque de congés pour les prochains jours

Cher Sara Amrani,

Je vous écris par ce biais pour vous informer qu'il est de plus en plus difficile de gérer les congés de ces derniers jours, compte tenu de la demande constante de vacances des employés. En effet, la réduction de notre personnel et la mise à disposition de nos salariés pour les congés démontrent que nous ne sommes pas en mesure de répondre à leurs besoins de manière efficace.

Le nombre de congés demandés pour les prochains jours dépasse considérablement les besoins actuels, ce qui pose un problème de gestion pour notre équipe de gestion des congés. Il est donc important de prendre des mesures pour atténuer ce problème.

Cliquez ici pour vérifier/confirmer."""

response = requests.post("http://localhost:8000/predict", json={"email_text": email_text})
print("Status code:", response.status_code)
print()
import json
print(json.dumps(response.json(), indent=2, ensure_ascii=False))