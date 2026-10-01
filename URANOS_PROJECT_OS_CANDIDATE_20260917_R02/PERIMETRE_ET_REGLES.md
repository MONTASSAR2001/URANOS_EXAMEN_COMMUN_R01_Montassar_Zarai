# Périmètre et règles de reprise

Synthèse technique expurgée pour l'exercice. Elle ne remplace pas les spécifications complètes qui seront remises selon le périmètre d'une mission ultérieure autorisée. En cas de manque : écrire A COMPLETER et expliciter l'hypothèse ; ne pas inventer une règle métier.

## Objectif de la plateforme

Suivre des projets photovoltaïques de l'ingénierie et des achats à la réception : logistique internationale, stock, kits et tourets, travaux terrain, avancement vérifié, qualité/HSE, blocages et modifications, coûts, commissioning, documents de réception et pilotage multi-projets. Hors V1 : paie/RH, portail client public, applications natives de stores, achats automatiques, suivi GPS permanent des salariés et IA métier de phase 2.

## Invariants à préserver

1. Une commande, une livraison, une réception ou une sortie stock n'est jamais de l'avancement physique installé.
2. L'avancement officiel repose uniquement sur les quantités installées vérifiées indépendamment, dans une baseline approuvée dont les poids totalisent 100. Ne pas confondre % physique, matériel disponible et planifié.
3. Une correction conserve l'historique et remplace sa contribution antérieure sans double comptage. Ne pas réécrire silencieusement un enregistrement vérifié.
4. Le déclarant ne s'auto-vérifie pas. Les rôles et permissions sont contrôlés côté serveur, par utilisateur nommé et projet ; masquer un bouton n'est pas une autorisation.
5. Stock émis = installé vérifié + retourné + rebut/écart approuvé indépendamment. Les kits suivent la BOM fournisseur approuvée, sans quantités techniques improvisées.
6. Les documents ERP natifs restent les sources de vérité pour commandes, réceptions, mouvements et écritures. Les fixtures des tests ne les remplacent pas en production.
7. La file hors ligne contient des brouillons chiffrés. Synchroniser avec UUID idempotent ne signifie ni soumettre ni vérifier ; les étapes restent explicites et validées serveur.
8. Documents IFC en vigueur, preuves QA/QC, NCR, holds et gates conditionnent les opérations concernées. Aucune recette ou autorité d'ingénieur n'est simulée comme réelle.
9. Ne pas exposer un autre projet ni ses coûts. Les champs financiers sont filtrés côté serveur selon le rôle.
10. Une donnée manquante est inconnue/A COMPLETER, pas un zéro, un feu vert ou une date de fin inventée. Les unités et versions de baseline sont explicites.

## Principaux travaux restant après ce socle

Validation Linux/ERP réelle, migrations, master data, permissions SQL et transactions/concurrence ; workflows réception/quarantaine généralisés ; disponibilité matérielle 7/14 jours ; stock/tourets multi-circuits et inventaires ; finance native ; courbes temporelles, productivité et prévisions ; délégations/gates ; couverture Desk/terrain et QR/caméra/PDF ; supervision, sauvegarde/restauration et exploitation ; recette native complète 1 MW et multi-projets.

Ce backlog n'est pas demandé pour l'entretien. Aucun accès production, déploiement public, dépense, achat ou modification d'infrastructure n'est nécessaire pour l'exercice.
