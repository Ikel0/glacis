# Glacis

Mini-projet Kafka autour d'un besoin simple : surveiller les relevés de température d'expéditions sensibles et isoler les écarts de consigne avant la réception.

Il est volontairement court. L'objectif n'est pas de simuler une supply chain entière mais de travailler les gestes qu'une équipe data utilise tous les jours : contrat, topic, consumer group, idempotence, sujet de rejet et alerte lisible.

## Démarrage rapide

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
PYTHONPATH=src python3 -m glacis.server
```

Le tableau s'ouvre sur `http://localhost:8090` et le bouton de démonstration injecte cinq lectures synthétiques.

## Version Kafka

```bash
docker compose up --build
docker compose exec api python scripts/publish_demo.py
```

Le producteur envoie les relevés vers `coldchain.reading.v1`. Le worker consomme, valide et transmet les décisions à l'API. Une lecture qui ne respecte pas le contrat est écrite dans `coldchain.invalid.v1` avec son motif.

## Ce qui resterait à faire en équipe

- remplacer SQLite par un stockage partagé ;
- mettre les consignes produit dans une source de référence ;
- publier les métriques de retard et de rejet ;
- gérer les seuils de durée hors plage, pas seulement le point de mesure.
