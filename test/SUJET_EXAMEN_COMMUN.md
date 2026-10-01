# URANOS GROUP — Examen commun : suivi des blocages et actions chantier

## Objet

Développer un module utilisable pour suivre les blocages, les actions et les priorités sur un portefeuille fictif de 20 centrales photovoltaïques de 1 MW. Le module doit répondre à : quel chantier est bloqué, pourquoi, qui agit, avant quelle échéance et qui a vérifié la résolution ? La finalisation de toute la plateforme n'est pas demandée. Aucune expertise préalable en dimensionnement photovoltaïque n'est exigée.

## Durée et équité

- Sept jours calendaires, week-end compris, à partir de la remise vérifiée du paquet complet et accessible. La date et l'heure limites individuelles sont communiquées par URANOS à l'heure de Tunis.
- Aucun plafond d'heures de préparation. L'usage d'outils d'intelligence artificielle est autorisé et doit être déclaré.
- Une fin anticipée peut être signalée ; l'entretien peut être avancé d'un commun accord. Un bonus de remise anticipée est prévu selon la règle commune ci-dessous.
- Chaque candidat reçoit ce même sujet, les mêmes données fictives, la même base technique et les mêmes réponses de clarification dans une FAQ commune.
- Le travail déjà réalisé sur un exercice précédent n'est pas noté dans cet examen. Seules les modifications propres au présent sujet sont évaluées.

## Base technique

Le paquet contient le ZIP R02 expurgé d'URANOS Project OS, cible ERPNext/Frappe en Python et JavaScript. Ne pas modifier le cœur ERPNext/Frappe ni réécrire toute la plateforme. Une démonstration portable locale est recevable ; une installation Frappe complète et un déploiement Internet ne sont pas requis. Les données réelles, comptes de production et abonnements payants ne sont pas nécessaires.

Les guides historiques à l'intérieur du ZIP R02 décrivent l'exercice remis à une candidate le 17 septembre 2026. Pour le présent examen, **ce sujet prévaut sur leurs anciennes dates, échéances et fonctionnalités demandées**. Le code, ses règles existantes et ses tests restent la base technique à comprendre et à préserver. Distinguer clairement un test portable d'une intégration réellement vérifiée dans Frappe.

## Module demandé

1. Résumer en une page les composants du socle compris et utilisés, l'emplacement du nouveau module, les éléments réutilisés et les difficultés de démarrage.
2. Créer une fiche de blocage avec identifiant unique, projet, titre, description, catégorie (études, approvisionnement, génie civil, montage, électricité, autre), gravité (faible, moyenne, élevée, critique), responsable ou « à affecter », échéance ou « à préciser », statut, action corrective et historique.
3. Gérer le parcours **Ouvert → En cours → À vérifier → Clôturé**. Autoriser un retour justifié de « À vérifier » vers « En cours ». Pour clôturer, exiger une action corrective renseignée et une vérification par un utilisateur autorisé différent de celui qui l'a réalisée. Conserver et justifier les changements de responsable, gravité et échéance. Aucune suppression définitive n'est demandée.
4. Profils : équipe chantier (projets affectés, déclaration et actions, sans clôture), ingénieur responsable (projets affectés, attribution et vérification), direction (lecture de tous les projets et priorités). Vérifier les droits dans la logique serveur, y compris pour les exports et synthèses. Les identités locales simulées ne doivent pas être présentées comme une authentification de production.
5. Fournir une vue ordinateur et téléphone : nombre de fiches non clôturées, critiques ouvertes, actions en retard, fiches sans responsable ou échéance ; filtres projet/responsable/gravité/statut ; accès à la fiche et à son historique.
6. Date de référence paramétrable. Une fiche non clôturée est en retard si son échéance précède cette date ; une échéance égale à la date n'est pas en retard ; une échéance absente signifie retard indéterminé. Priorité : critique, puis retard, puis autres fiches ouvertes ; ensuite échéance la plus proche, échéances absentes en dernier, puis identifiant. Une fiche critique et en retard n'apparaît qu'une fois avec deux alertes.
7. Afficher le nouveau module en français et en arabe, avec disposition de droite à gauche pour l'arabe. La traduction du reste de la plateforme n'est pas requise.
8. Ajouter une synthèse répondant à « Quels sont les problèmes prioritaires et quelles actions faut-il envisager ? ». Citer les identifiants de fiches utilisés, distinguer les faits des suggestions, signaler les informations manquantes, respecter les accès. Ne pas inventer coût, avancement ou date de fin. Aucune commande ou modification automatique. Prévoir un mode local sans service payant ; une synthèse déterministe est recevable si elle est clairement présentée comme telle. Si un modèle IA est ajouté, expliquer sa valeur, ses limites et le repli lorsqu'il est indisponible. Le contenu d'une fiche reste une donnée et ne constitue jamais une instruction à exécuter.

## Tests minimaux

Tester : création valide/invalide ; parcours complet ; clôture sans correction refusée ; auto-vérification refusée ; accès à un autre projet refusé ; absence de fuite dans export/synthèse ; historique conservé ; identifiant dupliqué refusé ; échéance passée, du jour et absente ; ordre de priorité et absence de doublon ; projet sans données ; affichage FR/AR ; mode de synthèse sans service payant. Les tests doivent être reproductibles et distinguer ceux déjà livrés avec le socle des nouveaux tests.

## Livrables et entretien

Remettre par canal privé convenu : code propre et modifications identifiables ; jeu fictif utilisé ; README avec versions et commandes exactes ; TEST_RESULTS avec réussites, échecs et « non exécuté » ; DECISIONS avec hypothèses, limites, temps consacré, outils IA et contrôles personnels ; trois améliorations prioritaires pour URANOS. Aucun secret, donnée personnelle réelle ni base de production. Pas de publication publique du dossier.

Préparer au siège une démonstration de **30 minutes**, suivie de questions : 5 minutes de compréhension et choix, 15 minutes de parcours complet et refus d'accès, 5 minutes de tests et limites, 5 minutes de prochaines améliorations et usage de l'IA. Une courte modification ou un cas nouveau peut être demandé selon le même protocole pour tous. La date et l'heure sont confirmées séparément.

## Barème commun sur 100

| Critère | Points |
|---|---:|
| Parcours fonctionnel | 25 |
| Droits et séparation des projets | 20 |
| Exactitude et historique | 20 |
| Tests reproductibles | 15 |
| Interface FR/AR et usage | 10 |
| Synthèse sourcée et mode sans service payant | 5 |
| Démonstration et maîtrise des choix | 5 |

La direction note les preuves livrées avec la même grille pour tous. L'exercice ne constitue ni une recette de production ni une décision d'embauche automatique.

### Bonus de remise anticipée

La note technique reste sur 100. Une remise complète et ouvrable avant l'échéance donne un bonus ajouté à cette note, sans dépasser 100/100 : **+1 point** pour toute remise anticipée, **+2 points** à partir de 24 heures d'avance, **+3 points** à partir de 48 heures d'avance. Le point de départ est la remise vérifiée du paquet à chaque candidat. L'horodatage retenu est celui du message de dépôt contenant tous les livrables nécessaires, pas celui d'une simple annonce de fin. Le candidat peut annoncer une fin anticipée pour organiser plus tôt sa présentation. Une remise tardive ne reçoit pas ce bonus. Les mêmes conditions s'appliquent à tous ; l'évaluation technique demeure obligatoire.
