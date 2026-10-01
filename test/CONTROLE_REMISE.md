# Contrôle de remise R02 — 17 septembre 2026

R02 corrige uniquement les modalités documentaires de l'entretien : vendredi 25 septembre, heure à confirmer, présentation de 30 minutes suivie de questions, sans plafond de préparation ; un avancement de date est possible d'un commun accord si le travail est terminé plus tôt et URANOS informé. Le module demandé, le plan global et les restrictions de données sont conservés. Les 208 fichiers sources de R02 sont identiques à ceux de la copie R01 vérifiée ; les tests techniques ci-dessous n'ont donc pas été rejoués pour cette correction documentaire.

Copie technique issue du commit `eaf4c478a7201c9c8a24472b758a8ca449c5221d`, sans historique Git. 208 fichiers sources sélectionnés, quatre guides neufs et un manifeste. Les seules adaptations de sources sont le README applicatif (guide interne remplacé) et les métadonnées de simulation (chemins relatifs, absence de Git tolérée, pas de lecture d'un dépôt parent). Aucun calcul métier modifié.

## Vérifications effectivement exécutées sur la copie R01, sources inchangées en R02

| Contrôle | Résultat | Limite |
| --- | --- | --- |
| Tests Python après régénération des enveloppes navigateur | 360 tests + 375 sous-tests PASS, zéro échec/skip | Domaine/stubs, pas Frappe réel |
| Démarrage Python sans preuves navigateur | 359 tests + 375 sous-tests PASS | Un test explicitement exclu avec `--ignore` |
| Playwright / Chromium, fixtures locales | 18 contrôles PASS | Pas de session ERP ni de serveur production |
| `node --test tests/unit/test_support_workflows_js.mjs` | PASS | Enregistrement de cinq formulaires et action simulée, pas Desk réel |
| Simulation 1 MW synthétique | 58 assertions PASS | Pas d'achat, réception ou mouvement ERP réellement enregistré |

Versions de contrôle : Python 3.14.5, Node 24.19.0, Playwright 1.62.1. Le lancement initial du navigateur n'a pas trouvé le binaire par défaut de Playwright ; les 18 contrôles ont ensuite réussi avec le Chromium déjà installé, sélectionné via `PLAYWRIGHT_CHROMIUM_EXECUTABLE`. Les dépendances de test existantes ont été réutilisées : une installation vierge des dépendances n'a pas été rejouée. Le guide demande d'installer le Chromium correspondant à Playwright ; tout écart de version ou problème d'environnement doit être rapporté.

Les sorties de test, captures et enveloppes nouvellement générées ne sont pas dans le ZIP. Pour retrouver 360 tests, exécuter le test navigateur avant pytest comme indiqué dans le guide. Le chemin réduit sans Chromium comprend 359 tests, pas 360.

## Contrôle de remise et limites

La sélection est une liste blanche de fichiers suivis, pas une copie récursive du dossier de travail. Les fichiers internes, configurations de production, archives, dépendances et preuves historiques sont exclus. Les noms, identifiants et montants de fixture sont fictifs. Une recherche ciblée de marqueurs sensibles a été effectuée ; ce n'est pas une certification exhaustive d'absence de secrets ni un audit de sécurité production.

`MANIFEST.csv` indique le SHA256 de chaque fichier remis hors manifeste lui-même, et distingue les fichiers source inchangés, les deux adaptations et les nouveaux guides. Le fichier SHA256 livré séparément identifie le ZIP complet. Vérifier cette empreinte avant extraction.

Restent NON EXÉCUTÉS : installation/migration sur vrai Frappe, 27 tests Frappe natifs, grand livre stock réel, permissions SQL réelles, concurrence, recette ERP native complète 1 MW, charge SQL/HTTP, sauvegarde/restauration et mise en production. La V1 reste incomplète et non autorisée pour production.
