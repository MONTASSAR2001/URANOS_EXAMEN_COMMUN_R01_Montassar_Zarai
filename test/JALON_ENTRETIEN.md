# Jalon proposé — lecture de l'avancement vérifié sur 7 jours

Objectif : montrer votre capacité à reprendre du code existant, comprendre une règle métier, produire un ajout vérifiable et expliquer honnêtement ses limites. Le module demandé ci-dessous et le plan global de `PERIMETRE_ET_REGLES.md` sont conservés. Le jalon ne doit pas être présenté comme une finalisation garantie de toute la V1.

Entretien au siège le vendredi 25 septembre 2026, heure à confirmer. Présentation de 30 minutes suivie de questions. Aucun plafond d'heures de préparation n'est imposé. Si vous terminez plus tôt, informez URANOS : l'entretien pourra être avancé d'un commun accord. Dans tous les cas, distinguer les résultats vérifiés, les limites et les travaux restant à faire.

## Travail demandé dans la copie

1. Reproduire le démarrage et les tests accessibles, distinguer couverture portable et vraie intégration Frappe. Résumer l'architecture en une page maximum.
2. Ajouter une petite fonction testable de lecture des quantités installées vérifiées sur une fenêtre explicite de 7 jours calendaires, par work package et unité, sur un jeu exclusivement fictif. Afficher la période et la baseline. Ne pas additionner des mètres et des unités, ni convertir les quantités en heures de travail.
3. Présenter le résultat dans une carte ou un tableau simple FR/AR RTL du mode démonstration. Un résultat réellement absent doit apparaître inconnu, et une quantité réellement mesurée nulle peut apparaître zéro. L'intégration dans un endpoint Frappe réel est un bonus uniquement si l'environnement est déjà disponible ; ne pas prétendre qu'un mock est un serveur ERP.
4. Tester au moins : lignes Draft/Reported exclues ; réceptions et sorties stock exclues ; correction sans double comptage ; bornes de période ; deux unités distinctes ; projet non autorisé refusé par la couche testée ; données insuffisantes signalées.

La fenêtre de 7 jours calendaires est une convention de cet exercice, pas une politique de calendrier chantier. Les corrections doivent être résolues sur leur chaîne complète avant de calculer un total. Si l'historique ne permet pas de reconstruire ce qui était connu à une date donnée, le dire au lieu d'inventer un historique. Choisir pour la démonstration des corrections à même date d'origine, et documenter le cas des corrections entre périodes comme décision métier A COMPLETER. Ne pas modifier une règle de production pour faire passer ce cas.

Ne pas remplacer Python/Frappe par Java/Spring ou Angular, ni modifier le cœur ERP. Un blocage d'installation bien diagnostiqué est recevable ; fournir alors les tests portables et la démonstration clairement étiquetée, et poursuivre les autres travaux accessibles du périmètre.

## À remettre

- Modifications source sous forme de patch ou archive propre sur le canal convenu, sans publication d'un dépôt public.
- README : commandes exactes, versions, ordre de démarrage, temps réellement passé.
- `TEST_RESULTS.md` : tests exécutés, succès/échecs, exclusions et NOT RUN ; pas de résultats copiés présentés comme les vôtres.
- `DECISIONS.md` court : hypothèses, limites, prochaine étape, dépendances ajoutées et leurs licences, outils IA utilisés et contrôles personnels.
- Présentation locale de 30 minutes, suivie de questions sur le code et les scénarios. Ne pas préparer de données réelles ni de compte de production.

## Critères d'acceptation de l'exercice

Règles de calcul correctes et testées ; aucune donnée réelle ; stack préservée ; tests existants accessibles sans régression non expliquée ; séparation entre mock/fixture et intégration réelle ; FR/AR lisibles pour le nouvel élément ; erreurs et informations inconnues explicites ; code compréhensible que vous pouvez expliquer et modifier. L'évaluation ne vaut pas validation de sécurité ou autorisation de mise en production de la plateforme entière.
