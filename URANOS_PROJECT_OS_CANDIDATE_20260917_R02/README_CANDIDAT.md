# URANOS Project OS — socle technique d'évaluation

Snapshot du 17 septembre 2026, source `eaf4c478a7201c9c8a24472b758a8ca449c5221d`. Ce paquet est une copie technique expurgée, pas le dépôt complet, ni une version prête pour production. Toutes les données de démonstration, personnes, quantités, prix et preuves sont fictifs ; elles ne servent pas à dimensionner une centrale réelle.

Révision de remise R02. Lire d'abord ce guide, puis `PERIMETRE_ET_REGLES.md` et `JALON_ENTRETIEN.md`. Entretien au siège le vendredi 25 septembre 2026, heure à confirmer : présentation de 30 minutes suivie de questions. Aucun plafond d'heures de préparation n'est imposé. Si vous terminez plus tôt, informez URANOS ; l'entretien pourra être avancé d'un commun accord. Le module demandé et le plan global sont décrits dans les deux guides ; le jalon ne constitue pas une promesse de finalisation de toute la V1 avant l'entretien.

## Stack et arborescence

Application custom Frappe/ERPNext v16 en Python >=3.14 ; Node 24 pour les tests navigateur. UI Frappe Desk et web/PWA responsive FR/AR RTL en JavaScript/HTML/CSS. En intégration : Linux, MariaDB 11.8 et Redis. Ne pas remplacer cette stack ni modifier le cœur ERPNext/Frappe. Aucune installation Frappe n'est nécessaire pour commencer les tests portables et l'exercice.

- `apps/uranos_project_os/` : application installable, domaine, adaptateurs Frappe, schémas, ressources et tests natifs.
- `tests/` : tests Python portables, stubs de framework et fixtures navigateur explicitement synthétiques.
- `scripts/` : génération des DocTypes, contrôle du package et simulation 1 MW.
- `MANIFEST.csv` : fichiers remis, tailles, SHA256 et origine. Le manifeste ne contient pas sa propre empreinte ; le SHA256 externe identifie tout le ZIP.

Les cœurs ERPNext/Frappe, secrets, données réelles, historique Git, configurations de production, dépendances installées et rapports internes ne sont pas inclus. Les contrôles applicatifs et tests d'autorisation sont conservés pour éviter de livrer une application amputée de ses garanties.

## Démarrage portable — PowerShell Windows

Extraire le ZIP dans un nouveau dossier, ouvrir un terminal à sa racine. Installer Python 3.14 et Node 24 si nécessaires via leurs distributions officielles. Ne pas modifier la politique d'exécution PowerShell ni les protections du poste pour cet exercice : l'activation du venv n'est pas nécessaire.

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
npm.cmd install --no-save --package-lock=false playwright@1.62.1
npx.cmd playwright install chromium
node tests/browser/field_qa.mjs
.\.venv\Scripts\python.exe -m pytest -q
node --test tests/unit/test_support_workflows_js.mjs
```

Le test navigateur doit précéder pytest : il régénère `tests/evidence/browser/envelopes.json` à partir de fixtures fictives. Les preuves historiques ne sont pas livrées. Le navigateur tourne en mode headless contre un serveur local, sans compte URANOS. Ce test ne lance pas ERPNext.

Si Chromium n'est pas disponible, commencer par la couverture réduite ci-dessous et signaler explicitement le test exclu ; ne pas annoncer une suite complète réussie :

```powershell
.\.venv\Scripts\python.exe -m pytest -q --ignore=tests/unit/test_browser_envelope_contract.py
```

Pour la simulation portable :

```powershell
$env:PYTHONPATH = 'apps/uranos_project_os'
.\.venv\Scripts\python.exe scripts/simulate_1mw.py
```

Sans option, la simulation n'écrit pas de rapport. `--write-evidence` crée des résultats locaux contenant notamment version système et révision Git ; inspecter tout rapport avant retour. Ne pas joindre caches, environnements, bases ou identifiants.

## Démarrage portable — Linux

```sh
python3.14 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
npm install --no-save --package-lock=false playwright@1.62.1
npx playwright install chromium
node tests/browser/field_qa.mjs
.venv/bin/python -m pytest -q
node --test tests/unit/test_support_workflows_js.mjs
PYTHONPATH=apps/uranos_project_os .venv/bin/python scripts/simulate_1mw.py
```

Les bibliothèques système de Chromium peuvent manquer sur Linux. Documenter le blocage ; toute installation nécessitant une administration du poste suit les règles de votre environnement. Ne pas transformer un problème d'installation en modification de sécurité.

## Intégration Frappe — hors prérequis de l'entretien

Seulement si un bench Linux v16 jetable est déjà disponible, avec ERPNext installé et sans données réelles : depuis ce bench, adapter les deux placeholders suivants puis exécuter :

```sh
bench get-app /ABSOLUTE/PATH/TO/SNAPSHOT/apps/uranos_project_os
bench --site TEST_SITE install-app uranos_project_os
bench --site TEST_SITE migrate
bench --site TEST_SITE run-tests --app uranos_project_os
```

Ne pas utiliser un site existant ou de production. Les migrations et tests natifs ne sont pas encore validés sur un vrai environnement Frappe : l'installation peut révéler des incompatibilités. En cas de blocage, fournir le diagnostic et continuer les travaux indépendants accessibles. Les comptes projet/permissions explicites et les données maîtres doivent être créés dans le seul site jetable ; aucun identifiant de production n'est fourni ou requis.

## Niveau de preuve au snapshot

Le checkpoint source rapportait 360 tests Python portables et 375 sous-tests réussis, 18 cas Chromium sur fixtures, une simulation pure-domain 1 MW avec 58 assertions et 41 DocTypes vérifiés structurellement. Les 60 tests de revue indépendante sont inclus dans 360. Les 27 tests Frappe natifs écrits n'ont pas été exécutés. Ce ne sont PAS des preuves de migrations, transactions ERP, SQL, concurrence, restauration, sécurité de production ou recette terrain. Voir `CONTROLE_REMISE.md` pour les vérifications propres à cette copie.

## Confidentialité et provenance

Usage prévu : évaluation technique et modifications demandées dans le cadre de la remise autorisée. Ne pas publier le code, le transférer à un tiers ou l'envoyer dans un service externe sans accord URANOS. Aucun accès à un système réel n'est accordé. Déclarer les outils d'IA et dépendances utilisés, leurs apports et les vérifications personnelles effectuées.

Le code custom porte actuellement `UNLICENSED`, sans licence libre jointe. Cette note ne crée pas de cession de propriété intellectuelle : conditions des futurs travaux A COMPLETER avec URANOS. Les droits éventuels attachés aux composants tiers demeurent applicables. Les cœurs non inclus sont [Frappe MIT](https://raw.githubusercontent.com/frappe/frappe/version-16/LICENSE) et [ERPNext GPLv3](https://raw.githubusercontent.com/frappe/erpnext/version-16/license.txt). Conserver leurs notices lors de leur installation et celles de toute nouvelle dépendance.
