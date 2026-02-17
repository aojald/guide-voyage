# Guide voyage – Consignes par destination

Page statique (HTML + JS, sans serveur) pour afficher les consignes de voyage selon **pays** et **type de voyage** (Professionnel / Personnel). Les données pays viennent d’un fichier Excel ; les textes des consignes sont dans le template HTML. Une fois généré, le fichier `index.html` fonctionne entièrement en local (offline).

---

## Utilisation rapide

1. **Mettre à jour l’Excel** : éditer `referentiel_données.xlsx` (voir colonnes ci‑dessous).
2. **Éditer les consignes** (optionnel) : modifier `index_template.html` (objets `TEXTS` et `TEXTS_EN`) et/ou `country_tips.py` pour les phrases « En bref ».
3. **Générer la page** : lancer `python3 build_from_excel.py` depuis le dossier `guide-voyage`.
4. **Ouvrir** `index.html` dans un navigateur : choisir pays (recherche ou liste) et type de voyage.

---

## Logique d’affichage

### Données par pays (Excel)

Chaque ligne de l’Excel décrit un pays et ses **flags** (risques / contraintes). Le script produit un JSON embarqué dans la page avec notamment :

- `code`, `nom`, `nomEN` : identification et libellés FR/EN
- `riskColor` : niveau risque **personnes** (ex. `Red`, `Orange`, vide = standard)
- `blocked` : accès Microsoft bloqués par défaut → dérogation, consignes « device clean » renforcées
- `cleanDevice` : risque à la **douane** → consignes douane ; si **Pro** : iPhone de prêt DSI (avant) + restitution (après)
- `cleanOnReturn` : risque **vol / compromission de données** (hôtel, compromat, etc.) → consignes « considérer appareils compromis » après le voyage
- `olaflySim` : pays **hors forfait 4G** → affichage « SIM Olafly nécessaire » + éventuels **Comments** (régions, forfait)

Les risques **données** peuvent se **cumuler** : un pays peut être à la fois `blocked` et `cleanDevice` ; dans ce cas les consignes « Microsoft » et « douane » sont toutes les deux affichées (avant / pendant / après).

### Section « Risque sur les personnes »

- **Toujours** : consignes *standard* (réservations AD, ID Sécurité, incidents, etc.) en trois blocs : **Avant**, **Pendant**, **Après**.
- Si `riskColor` est **Orange** ou **Rouge** : en plus des standard, ajout des consignes *orange_rouge* (assurance rapatriement, briefing sécurité, etc.) et d’une **validation** spécifique :
  - **Orange** : « Validation d’un associé de la stratégie »
  - **Rouge** : « Validation du Management »

### Section « Risque sur les données (appareils et accès cloud) »

- **Toujours** : consignes *standard* (mise à jour appareils, codes PIN, déclaration d’incident, débrief).
- Si **Microsoft bloqué** (`blocked`) :
  - Avant : message « accès tenant Microsoft demande préalable » + suppression données sensibles + phrase « effacer conversations » (voir Pro/Perso ci‑dessous).
  - Pendant : consignes « device sous contrôle », pas de chargeurs tiers, posture, **douane** (une seule phrase douane pour éviter doublon avec risque douane).
  - Après : « considérer appareils compromis », réinitialisation.
- Si **risque douane** (`cleanDevice`) uniquement :
  - Avant : phrase « effacer conversations » (Pro ou Perso selon type de voyage).
  - Pendant : phrase douane détaillée.
- Si **bloqué + douane** : les deux blocs sont fusionnés ; la phrase douane n’apparaît qu’une fois.
- **Voyage Pro + risque douane** : en plus, avant = « DSI peut mettre à disposition un iPhone vierge… » ; après = « Restituer l’iPhone de prêt au service IT… ». Pour éviter doublon, la mention « DSI peut proposer un iPhone de prêt » dans la phrase « effacer » n’est affichée qu’en **Pro sans** risque douane (ou pays bloqué sans douane).
- **Voyage Perso** : la phrase « effacer conversations » est affichée **sans** la mention DSI (iPhone de prêt).
- Si **risque données au retour** (`cleanOnReturn`) et/ou bloqué : après = consignes « compromis / réinitialisation ».

### Section « Risques hors forfait »

- Si le pays est **hors forfait 4G** (`4G_included` = Non) : une consigne « SIM Olafly nécessaire » (+ emoji 📱 dans le bandeau).
- Sinon : « Aucun risque hors forfait identifié ».
- Les **Comments** de l’Excel (régions, forfait 4G) sont affichés dans ce bloc s’ils sont renseignés.

### Bandeau récapitulatif et « En bref »

- En haut des résultats : **drapeau** (emoji Unicode à partir du code pays) + **nom du pays** (FR ou EN selon la langue) + **type de voyage** (Pro/Personnel) + **indicateurs** (risque personnes, Microsoft bloqué, douane, données en voyage, SIM Olafly).
- En bas : une **phrase « En bref »** (conseil léger / spécialité locale) selon le pays, définie dans `country_tips.py` (FR et EN).

---

## Mise à jour des consignes

### 1. Données pays (liste, flags, noms)

**Fichier** : `referentiel_données.xlsx`

| Colonne        | Rôle |
|----------------|------|
| **Code**       | Code ISO du pays (ex. FR, US) — 2 lettres recommandées |
| **Name_EN**    | Nom du pays en anglais (affiché en mode EN) |
| **Name_FR**    | Nom du pays en français (affiché en mode FR) |
| **Personnal_risk** | Niveau risque personnes : `Red`, `Orange` ou vide → déclenche consignes orange/rouge + validation associé/Management |
| **Blocked_Country IT** | Oui = accès Microsoft bloqués → consignes dérogation, device clean, demande préalable tenant |
| **Customs_Risk** | Oui = risque douane → consignes douane ; si Pro, iPhone de prêt DSI (avant + après) |
| **Local_Data_risk** | Oui = risque vol/compromission données → consignes « appareils compromis » au retour |
| **4G_included** | Oui = pays dans le forfait 4G ; **Non** = affichage « SIM Olafly nécessaire » |
| **Comments**   | Texte libre (ex. régions, forfait) affiché dans le bloc « Risques hors forfait » |

Valeurs considérées comme **Oui** : `Yes`, `Oui`, `1`, `true`, `x`, `o` (insensible à la casse).

Après modification : relancer `python3 build_from_excel.py`.

---

### 2. Textes des consignes (FR et EN)

**Fichier** : `index_template.html`

Les textes affichés dans les trois sections (personnes, données, forfait) sont définis dans le **même fichier** que le template, dans deux objets JavaScript :

- **`TEXTS`** : tous les libellés en **français** (consignes personnes et données, phrases « effacer », pro douane, etc.).
- **`TEXTS_EN`** : même structure en **anglais**.

Structure principale :

- **`TEXTS.personnes`** (et `TEXTS_EN.personnes`)  
  - `avant` : `standard`, `orange_rouge`, `validationOrange`, `validationRouge`  
  - `pendant` : `standard`, `orange_rouge`  
  - `apres` : `standard`, `orange_rouge`
- **`TEXTS.donnees`** (et `TEXTS_EN.donnees`)  
  - `avantMicrosoft`, `effacerConversations`, `effacerConversationsPro`  
  - `avant` : `standard`, `blocked`, `douane`  
  - `pendant` : `blocked`, `douane`, `douaneLineOnly`  
  - `apres` : `standard`, `compromis`  
  - `proDouaneAvant`, `proDouaneApres`
- **`UI`** : libellés d’interface (titres, boutons FR/EN, labels formulaire, « En bref », etc.) dans `UI.fr` et `UI.en`.

Pour modifier une consigne : éditer la chaîne correspondante dans `TEXTS` (FR) et/ou `TEXTS_EN` (EN), puis **regénérer** avec `python3 build_from_excel.py`. Ne pas modifier directement `index.html` (il est écrasé à chaque génération).

---

### 3. Phrases « En bref » (conseil / humour par pays)

**Fichier** : `country_tips.py`

- **`SPECIFIC_TIPS`** : dictionnaire `code pays (2 lettres)` → tuple `(phrase_fr, phrase_en)`.
- **`GENERIC_TIPS`** : liste de tuples `(fr, en)` pour les pays sans entrée spécifique (attribution déterministe à partir du code).

Après modification : relancer `python3 build_from_excel.py` (le script injecte le JSON des tips dans le template).

---

## Fichiers du projet

| Fichier | Rôle |
|---------|------|
| **referentiel_données.xlsx** | Source de vérité : liste des pays et flags (risques, forfait 4G, commentaires). |
| **index_template.html** | Modèle de page : structure HTML/CSS/JS, placeholders `__PAYS_JSON__`, `__TIPS_JSON__`, `__GENERATION_DATE__`, et **référentiel des textes** `TEXTS`, `TEXTS_EN`, `UI`. |
| **build_from_excel.py** | Lit l’Excel, charge les tips (`country_tips.py`), remplace les placeholders dans le template et écrit `index.html`. Dépendances : bibliothèque standard Python uniquement (pas de pip). |
| **country_tips.py** | Phrases « En bref » par pays (FR/EN). Optionnel : si absent, les tips sont vides. |
| **index.html** | Page générée (données + tips + date de génération en bas). À ouvrir dans un navigateur ; ne pas éditer à la main. |

La date de génération affichée en bas de page est mise à jour automatiquement à chaque exécution du script.
