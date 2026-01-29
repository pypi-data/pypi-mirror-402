### LCDP api

## Présentation
Ce dépôt contient les définitions **open API 3.0** de l'API Rest LCDP

[Open API 3.0 Doc](https://swagger.io/specification/)

##  Docker

Un docker-compose permettant de lancer swagger-ui est en place dans le dossier
`swagger-ui/docker-compose.yml`

## Exécuter les requêtes swagger en local

Si la stack LCDP tourne en local, le swagger-ui ne pourra pas effectuer de requête vers la stack local à cause des CORS.

Pour permettre au swagger-ui d'exécuter les requêtes, if faut l'ouvrir dans **un navigateur non sécurisé**.
 
Voir : [Documentation Utiliser swagger sans CORS](https://lecomptoirdespharmacies.atlassian.net/wiki/spaces/LCDP/pages/87261185/Utiliser+Swagger+UI+sans+CORS)