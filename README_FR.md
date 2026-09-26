# Passerelle Bluetooth Mesh Steinel — fork GL-S10 (Ethernet) multi-lampes

🇬🇧 [English version](README.md) · 📜 [README du projet d'origine](README_UPSTREAM.md)

Ce dépôt est un **fork de [supczinskib/steinel-nightmatiq-esp32-c3-gateway](https://github.com/supczinskib/steinel-nightmatiq-esp32-c3-gateway)**,
une excellente passerelle ESPHome qui pilote un Steinel **NightmatIQ Plus** en Bluetooth Mesh depuis un **ESP32-C3**.

Ce fork adapte le projet à un autre usage :

- il tourne sur un **GL.iNet GL-S10** (ESP32 classique, **Ethernet filaire**, sans Wi-Fi) ;
- il pilote **plusieurs luminaires Steinel Connect en même temps** depuis une seule passerelle
  (testé avec une **L42 SC** et deux **L 810 SC**) ;
- il expose dans Home Assistant, pour **chaque** luminaire, le même jeu d'entités
  (mode, état de la lumière, **variation en direct**, mouvement, luminosité, réglages du détecteur, firmware…) ;
- il envoie les changements à Home Assistant **dès qu'ils se produisent**, au lieu de répéter les valeurs en boucle ;
- il fournit une **couche Home Assistant** prête à l'emploi : lumières variables, onglet de tableau de bord
  et automatisation qui conserve l'intensité choisie.

> ⚠️ Projet communautaire, **sans lien avec STEINEL, ni approuvé ni supporté par STEINEL**.
> Il a été développé et testé sur une seule installation (1× L42 SC, 2× L 810 SC). D'autres produits
> Steinel Connect peuvent se comporter différemment. Utilisation à vos risques, et gardez toujours un moyen
> de reflasher la passerelle (voir *Récupération*).

---

## Sommaire

1. [Ce qui change par rapport au projet d'origine](#1-ce-qui-change-par-rapport-au-projet-dorigine)
2. [Matériel](#2-matériel)
3. [Organisation des luminaires Steinel dans le réseau Mesh](#3-organisation-des-luminaires-steinel-dans-le-réseau-mesh)
4. [Architecture de la passerelle multi-lampes](#4-architecture-de-la-passerelle-multi-lampes)
5. [Entités exposées par luminaire](#5-entités-exposées-par-luminaire)
6. [Compilation et première installation](#6-compilation-et-première-installation)
7. [Configurer vos propres luminaires](#7-configurer-vos-propres-luminaires)
8. [Couche Home Assistant](#8-couche-home-assistant)
9. [Retour d'expérience et dépannage](#9-retour-dexpérience-et-dépannage)
10. [Limites connues et pistes](#10-limites-connues-et-pistes)
11. [Sécurité](#11-sécurité)
12. [Licence et remerciements](#12-licence-et-remerciements)

---

## 1. Ce qui change par rapport au projet d'origine

| Domaine | Projet d'origine | Ce fork |
|---|---|---|
| Matériel | ESP32-C3 Super Mini, Wi-Fi | **GL.iNet GL-S10** (ESP32-D0WD, PHY Ethernet IP101), Ethernet uniquement |
| Luminaires | un NightmatIQ Plus (3 éléments) | **une lampe principale + jusqu'à 4 lampes supplémentaires**, 4 éléments chacune (L42 SC, L 810 SC) |
| Table des nœuds | 1 nœud, 3 éléments | jusqu'à 4 nœuds, **4 éléments** par nœud |
| Mouvement | non exposé | **Mouvement** (binaire, instantané via les publications de groupe) + **Mouvement niveau** (%) |
| Luminosité | élément +2, interrogé | élément +3, **poussée par les lampes** (groupe `0xC000`) + interrogation de secours |
| Réglages du détecteur | seuil crépusculaire (lampe principale seulement) | seuil, **puissance**, **lumière de base**, **temporisation** pour chaque lampe |
| Variation en direct | — | **Intensité** (client Light Lightness) pour chaque lampe |
| Identité | NightmatIQ seulement | firmware / révision matérielle de **chaque lampe**, lus dans les annonces BLE |
| Trafic vers HA | valeurs renvoyées toutes les quelques secondes | valeurs envoyées **seulement quand elles changent**, vérifiées chaque seconde |
| Diagnostic | — | **écoute des messages propriétaires Steinel** (groupe `0xFEFF`), optionnelle |
| LEDs | LED de statut seulement (éteinte quand tout va bien) | **3 LEDs parlantes** : alimentation, réseau/Home Assistant, Bluetooth Mesh |
| Home Assistant | entités de l'appareil | + **lumières modèles avec curseur**, **onglet de tableau de bord**, **automatisation de conservation de l'intensité** |

Tout le fonctionnement propre au NightmatIQ d'origine est conservé : interface web, import depuis le cloud
Steinel, modes Auto/On/Off de la lampe principale, OTA, safe mode…

---

## 2. Matériel

### GL.iNet GL-S10

| Élément | Valeur relevée sur l'appareil testé |
|---|---|
| Module | ESP32-WROOM-32U (antenne externe, connecteur IPEX) |
| Puce | ESP32-D0WD **révision 1.1**, quartz 40 MHz |
| Flash | 4 Mo (fabricant `0x46`) |
| PHY Ethernet | **IP101** (révision matérielle 2.x) : MDC GPIO23, MDIO GPIO18, horloge en entrée sur GPIO0, adresse PHY 1, alimentation GPIO5 |
| LEDs | alimentation GPIO14, Bluetooth GPIO12, réseau GPIO32 (toutes inversées) |
| Bouton | GPIO33 (bouton latéral) |

### LEDs en façade

| LED | GPIO | Comportement |
|---|---|---|
| Alimentation | 14 | allumée dès que le firmware tourne |
| Réseau (WAN) | 32 | **fixe** = Ethernet + Home Assistant connectés · **flash toutes les 2 s** = Ethernet sans Home Assistant · **clignote à 1 Hz** = pas d'Ethernet · **clignote vite** = erreur d'un composant |
| Bluetooth | 12 | **fixe** = Mesh prêt · **clignote à 1 Hz** = Mesh en démarrage / pas prêt |

La LED réseau remplace le `status_led` d'ESPHome, qui reste éteint quand tout va bien.

La radio du GL-S10 est entièrement consacrée au Bluetooth Mesh : **il ne peut pas servir de proxy Bluetooth
en même temps**. Utilisez un autre ESP32 pour le proxy Bluetooth ESPHome.

> La révision matérielle 1.0 utilise un PHY LAN8720 au lieu de l'IP101 (horloge sur GPIO17, pas de broche
> d'alimentation). Des pertes de paquets sont signalées sur certaines révisions récentes équipées de l'IP101.

### Adaptateur série (premier flash / récupération)

- **Adaptateur USB-TTL 3,3 V** avec une vraie puce **FTDI FT232RL** ou **Silicon Labs CP2102**.
  Les adaptateurs **PL2303** contrefaits ne fonctionnent pas sous les versions récentes de macOS.
- Ouvrez le boîtier (encoche en dessous), débranchez l'antenne IPEX et sortez la carte.
- Câblez **TXD → RX**, **RXD → TX**, **GND → GND** sur le connecteur de 9 trous sérigraphié. Ne branchez **pas** le VCC.
- Mode flash : maintenez le bouton situé à côté des 9 trous (ou reliez **IO0** au GND) pendant la mise sous tension.
- Alimentez le GL-S10 **depuis le même ordinateur** que l'adaptateur : avec un chargeur séparé, l'adaptateur
  peut se déconnecter au démarrage du GL-S10 (écart de masse), et on ne lit plus rien.
- Si le GL-S10 est alimenté en PoE, ne branchez **jamais** l'USB et le PoE en même temps.

---

## 3. Organisation des luminaires Steinel dans le réseau Mesh

Tout ce qui suit a été lu dans la sauvegarde cloud Steinel (`/project/network/<id>/backup`, au format standard
*Mesh Configuration Database*), puis confirmé sur le trafic réel.

### Composition d'une L42 SC / L 810 SC (4 éléments)

| Élément | Adresse | Principaux modèles | Rôle |
|---|---|---|---|
| 0 | base | Generic OnOff `1000`, Level `1002`, Power OnOff `1006`, **Light Lightness `1300`**, Time `1200`, Scheduler `1206`, **Scene `1203`** | sortie lumière |
| 1 | base + 1 | **Light LC Server `130F`** / Setup `1310`, modèles fabricant `0563:1001/1004/1005/1006` | contrôleur d'éclairage automatique (logique du détecteur) |
| 2 | base + 2 | Sensor `1100`, propriété **`0x0042` Motion Sensed** | mouvement |
| 3 | base + 3 | Sensor `1100`, propriété **`0x004E` Present Ambient Light Level** | luminosité |

### Ce que publient les lampes (sans aucune modification)

| Publication | Destination | Période |
|---|---|---|
| Mouvement (élément 2) | groupe **`0xC001`** (commun à toutes les lampes) | ~4 s + à chaque changement |
| Luminosité (élément 3) | groupe **`0xC000`** | ~10 s |
| Heure (`1200`) | `0xFFFF` | — |
| Modèle fabricant `0563:1005` (élément 1) | groupe **`0xFEFF`** | non observé lors des changements d'état (voir §10) |
| **État allumée/éteinte, intensité, état LC** | **rien** | → doit être interrogé |

### Bon à savoir

- Le mode **Auto** de l'appli Steinel = *mode LC activé* + **rappel de la scène 3** (« Nightmatic »).
  Une scène Bluetooth Mesh mémorise aussi les **propriétés LC** : la rappeler **remet la puissance du détecteur**
  à la valeur enregistrée par l'appli Steinel (93 % ici). Voir §8.3.
- Les réglages du détecteur sont des **propriétés Light LC** standard, sur l'élément 1 :
  `0x002B` seuil de luminosité, `0x002E` intensité à l'allumage (« puissance »),
  `0x0030` intensité au repos (« lumière de base »), `0x003C` durée après le dernier mouvement (« temporisation »).
- Les deux derniers octets des données fabricant Steinel (société `0x0563`) des annonces BLE correspondent
  aux 4 chiffres hexadécimaux à la fin du nom de la lampe (`L 810 SC A52C` → `0xA52C`). L'annonce contient aussi
  l'identifiant produit, le firmware (majeur.mineur.correctif), le bootloader et la révision matérielle.
- Une luminosité de `0xFFFFFF` signifie **« inconnue »** (167 772,15 lx si on la décode naïvement).

---

## 4. Architecture de la passerelle multi-lampes

### Lampe principale et lampes supplémentaires

- La **lampe principale** est celle choisie dans l'interface web lors de l'import Steinel (adresse du nœud).
  Elle conserve toute la logique d'origine (transactions Auto/On/Off confirmées, seuil, identité…).
- Les **lampes supplémentaires** sont déclarées dans le YAML (`on_boot`), avec leur adresse de base et leur
  numéro de scène. Elles bénéficient d'une implémentation plus légère et indépendante :
  - les commandes (mode, seuil, réglages du détecteur, intensité) sont envoyées **deux fois, sans accusé de
    réception**, puis **relues** pour confirmation ;
  - leur état est **interrogé** à tour de rôle (allumée/éteinte, mode LC, luminosité, seuil) ;
  - les **publications** de mouvement et de luminosité sont aiguillées selon l'adresse de l'émetteur.

### Modifications de la pile Mesh (ESP-BLE-MESH, rôle provisioner)

| Problème rencontré | Solution |
|---|---|
| `Failed to find Dst 0x….` : un provisioner n'envoie qu'aux adresses présentes dans sa table de nœuds | toutes les lampes sont **restaurées dans la table des nœuds**, avec **4 éléments** ; `CONFIG_BLE_MESH_MAX_PROV_NODES: "4"` |
| `RPLFull` : liste anti-rejeu dimensionnée pour 3 sources | `CONFIG_BLE_MESH_CRPL: "16"` |
| les lampes publient mouvement et luminosité vers des groupes | abonnement local du client capteur à `0xC001` et `0xC000` (`CONFIG_BLE_MESH_MODEL_GROUP_COUNT: "2"`) |
| variation en direct | nouveau modèle **client Light Lightness** (`CONFIG_BLE_MESH_LIGHT_LIGHTNESS_CLI: y`), lié à l'AppKey |
| écoute des messages propriétaires | modèle fabricant `0563:1FFF` qui accepte les **64 codes de message Steinel possibles**, abonné à `0xFEFF` |

### Modifications du firmware (composant `nightmatiq_mesh`)

- Code Wi-Fi protégé par `#ifdef USE_WIFI` (le build GL-S10 n'a pas de composant Wi-Fi).
- Nœud restauré avec 4 éléments ; luminosité lue sur l'élément +3, mouvement sur l'élément +2.
- Couche « lampes supplémentaires » : `add_lamp()`, `set_lamp_mode()`, fonctions de lecture `lamp_*()`,
  aiguillage des réponses dans les callbacks generic / light / sensor (avant les compteurs de la lampe principale).
- Couche « propriétés LC » : `add_lc_props()`, `set_lamp_lc_prop()`, `lamp_lc_prop()` pour `0x002E`, `0x0030`, `0x003C`
  (le seuil `0x002B` est traité à part), avec un tampon par lampe (ESP-IDF ne copie pas les valeurs de propriété).
- Intensité : `set_lamp_lightness()` / `lamp_lightness()` (Light Lightness Set Unack / Get).
- Identité : `set_primary_tag()` / `set_lamp_tag()` associent les annonces BLE aux lampes ;
  le scan d'identité attend d'avoir vu toutes les lampes (30 s maximum).
- Luminosité `0xFFFFFF` ignorée ; mode et seuil de la lampe principale publiés seulement s'ils changent.
- Mouvement : `poll_motion()` (secours, un appel sur six) et interrogation de l'état allumée/éteinte de la lampe principale.
- Interrogation plus rapide et entrelacée des lampes supplémentaires (une lampe puis l'autre, toutes les 1,5 s).

### Modifications du YAML (`esphome/gl-s10-steinel.yaml`)

- Construit **à partir de la configuration du proxy Bluetooth GL-S10, qui démarre** (carte, Ethernet, LEDs),
  sans `esp32_ble_tracker` ni `bluetooth_proxy`.
- Lambda `on_boot` qui déclare les groupes, les lampes supplémentaires, les identifiants et les propriétés LC.
- Entités modèles pour chaque lampe, publiées **seulement quand elles changent** (principe `static last`, `update_interval: 1s`).
- Filtre `delayed_off` sur le mouvement (10 s par défaut) : les lampes signalent un mouvement *instantané*.
- Signal filtré (`delta: 3` dB).
- Logique des LEDs (toutes les 250 ms) : LED réseau selon l'Ethernet, Home Assistant et les erreurs ; LED Bluetooth selon *Mesh Ready*.

---

## 5. Entités exposées par luminaire

| Entité | Type | Source | Mise à jour |
|---|---|---|---|
| Mode (Auto / Always On / Always Off) | select | mode LC + état allumée/éteinte | au changement |
| Lumière | capteur binaire | Generic OnOff | interrogée (3 à 6 s) / instantanée pour les commandes HA |
| **Intensité** | nombre 0–100 % | Light Lightness | instantanée à la commande, puis relue |
| Mouvement | capteur binaire (mouvement) | `0x0042`, groupe `0xC001` | **instantanée** (+ maintien 10 s) |
| Mouvement niveau | capteur % (diagnostic) | `0x0042` | instantanée |
| Luminosité | capteur lx | `0x004E`, groupe `0xC000` | ~10 s (période de la lampe) |
| Seuil | nombre lx | LC `0x002B` | au changement |
| Puissance | nombre % | LC `0x002E` | au changement |
| Lumière de base | nombre % | LC `0x0030` | au changement |
| Temporisation | nombre s | LC `0x003C` | au changement |
| Signal | capteur dBm (diagnostic) | RSSI des messages de la lampe | au changement ≥ 3 dB |
| Firmware, Révision matérielle | diagnostic | annonces BLE | une fois après le démarrage |
| Fabricant, Company ID, Product ID | diagnostic | sauvegarde / constantes | une fois |

Entités de la passerelle : *Mesh Ready*, *Status*, *Refresh*, *Safe Mode Boot*, *Reset Button*.

---

## 6. Compilation et première installation

### Prérequis

- **ESPHome 2026.7.3** (exigé par le composant). Sous macOS :
  ```bash
  brew install python@3.13
  python3.13 -m venv ~/esphome-steinel && source ~/esphome-steinel/bin/activate
  pip install --upgrade pip wheel && pip install "esphome==2026.7.3"
  ```
  Sur un **Mac Intel**, `cbor2` peut nécessiter Rust : `brew install rust`, puis relancez `pip install`.
- Votre compte Steinel Connect (e-mail / mot de passe) et les lampes déjà configurées dans l'appli Steinel.

### Secrets

Créez `esphome/secrets.yaml` (à ne jamais publier) :
```yaml
ota_password: "le mot de passe admin que vous définirez dans l'interface web"
api_encryption_key: "…"   # optionnel, voir §11
```
> Le composant **aligne le mot de passe OTA sur le mot de passe admin de l'interface web** : après l'avoir
> changé dans l'interface, les mises à jour OTA exigent ce même mot de passe dans `secrets.yaml`.

### Compilation

```bash
cd esphome
esphome compile gl-s10-steinel.yaml
```

### Premier flash (par câble série)

```bash
esptool --port /dev/cu.usbserial-XXXX --baud 115200 --before no-reset --after no-reset \
        --chip esp32 write-flash -z 0x0 .esphome/build/gl-s10-steinel/build/firmware.factory.bin
```
(mode flash : bouton situé à côté des 9 trous, maintenu pendant la mise sous tension.)

Branchez ensuite l'Ethernet : la passerelle obtient une adresse en DHCP. Les mises à jour suivantes passent par le réseau :
```bash
esphome run gl-s10-steinel.yaml --device <ip-de-la-passerelle>
```

### Configuration initiale (interface web)

1. Ouvrez `http://<ip-de-la-passerelle>`, connectez-vous avec `admin` / `12345678` et **changez le mot de passe admin**.
2. Saisissez votre compte Steinel, téléchargez la liste des réseaux, choisissez le vôtre.
3. **Node** : saisissez l'adresse de votre lampe **principale** (par exemple `000F`). En automatique, le firmware
   prend le premier nœud compatible.
4. IV Index à `0` (automatique), puis **Install**.
5. Ajoutez l'appareil dans Home Assistant (intégration ESPHome).

---

## 7. Configurer vos propres luminaires

Toutes les informations viennent de votre sauvegarde Steinel. Téléchargez-la (mêmes adresses que l'interface web) :

```bash
read -rs 'PW?Mot de passe Steinel : '; echo
H=(-u "vous@exemple.fr:$PW" -H 'X-Accept-Version: 2.4' -H 'User-Agent: A4.1-62' -H 'Device: PC-1')
curl -s "${H[@]}" 'https://connectapp.steinel.de/api/changes?since=4102444800&force_full_personal_sync=true&force_full_translation_sync=false' \
  | jq '.networks.changed[] | {id,name,nodes}'
curl -s "${H[@]}" 'https://connectapp.steinel.de/api/project/network/<ID-DU-RESEAU>/backup' > steinel-backup.json
```
> `steinel-backup.json` contient les **clés du réseau et des appareils** : gardez-le privé et ne le publiez jamais.

Requêtes utiles :

```bash
# nœuds, adresses et modèles (sans les clés)
jq '.nodes[] | {name, unicastAddress, pid, models: [.elements[] | [.models[].modelId]]}' steinel-backup.json
# scène par défaut de chaque lampe (mode Auto)
jq '.. | objects | select(has("nodeAddress") and has("defaultSceneNumber"))' steinel-backup.json
# ce que publie chaque modèle
jq '.nodes[] | {name, pubs: [.elements[] | .models[] | select(.publish != null) | {modelId, to: .publish.address}]}' steinel-backup.json
```

Adaptez ensuite la lambda `on_boot` de `gl-s10-steinel.yaml` :

```yaml
esphome:
  on_boot:
    then:
      - lambda: |-
          id(nightmatiq_gateway).add_group(0xC001);          // groupe mouvement
          id(nightmatiq_gateway).add_group(0xC000);          // groupe luminosité
          id(nightmatiq_gateway).add_lamp(0x0013, 3);        // lampe supplémentaire : adresse de base, scène
          id(nightmatiq_gateway).add_lamp(0x0017, 3);
          id(nightmatiq_gateway).set_primary_tag(0x308A);    // suffixe du nom de la lampe principale
          id(nightmatiq_gateway).set_lamp_tag(0x0013, 0xD58E);
          id(nightmatiq_gateway).set_lamp_tag(0x0017, 0xA52C);
          id(nightmatiq_gateway).add_lc_props(0x000F);       // réglages du détecteur (toutes les lampes)
          id(nightmatiq_gateway).add_lc_props(0x0013);
          id(nightmatiq_gateway).add_lc_props(0x0017);
```

… puis dupliquez les entités modèles d'une lampe supplémentaire pour chaque nouvelle lampe (en changeant l'adresse).
La lampe principale utilise les entités liées au composant.

Installation testée, pour référence :

| Lampe | Modèle | Adresse de base | Identifiant | Nom dans HA |
|---|---|---|---|---|
| principale | L42 SC | `0x000F` | `0x308A` | Applique Entrée |
| supplémentaire | L 810 SC | `0x0013` | `0xD58E` | Applique Devant |
| supplémentaire | L 810 SC | `0x0017` | `0xA52C` | Applique Garage |

---

## 8. Couche Home Assistant

Des fichiers d'exemple se trouvent dans [`home-assistant/gl-s10/`](home-assistant/gl-s10/). Les identifiants
d'entités dépendent des noms donnés à l'appareil et aux entités : adaptez-les.

### 8.1 Une lumière variable par luminaire (lumière modèle)

La passerelle expose séparément le *Mode* et l'*Intensité*. Une **lumière modèle** (template light) les réunit en
une vraie lumière HA, avec un curseur de luminosité ([`template-lights.yaml`](home-assistant/gl-s10/template-lights.yaml),
ou création via *Paramètres → Appareils et services → Entrées → Modèle → Lumière*) :

- **allumer** → règle l'intensité sur l'*intensité mémorisée*, puis passe en *Always On* ;
- **curseur** → règle l'intensité immédiatement, passe en *Always On* et mémorise la valeur ;
- **éteindre** (ou 0 %) → retour en **Auto** (le détecteur reprend la main) ;
- état = capteur binaire *Lumière*, luminosité = *Intensité*.

L'intensité est envoyée **avant** le passage en *Always On* : un Generic OnOff Set restaure la dernière intensité,
donc la lampe va directement au niveau demandé, sans flash intermédiaire.

### 8.2 Onglet de tableau de bord

[`dashboard-view.yaml`](home-assistant/gl-s10/dashboard-view.yaml) : une vue *sections* avec, pour chaque
luminaire, la tuile de lumière et son curseur, le mouvement, la luminosité et les boutons de mode.
À ajouter via *Tableau de bord → modifier → + (nouvelle vue) → ⋮ → Modifier en YAML*.

### 8.3 Conserver l'intensité choisie

Comme le **mode Auto rappelle la scène 3**, la puissance du détecteur revient à la valeur Steinel à chaque retour
en Auto. La solution :

- une entrée `input_number` **« intensité mémorisée »** par lampe, mise à jour par le curseur ;
- l'automatisation [`automation-keep-intensity.yaml`](home-assistant/gl-s10/automation-keep-intensity.yaml)
  réécrit la *Puissance* avec la valeur mémorisée **3 s après un retour en Auto**, ainsi qu'à chaque fois que la
  *Puissance* relue s'en écarte de plus de 1 % (par exemple si la lampe rappelle sa scène d'elle-même).

Résultat : l'intensité que vous choisissez est utilisée pour l'allumage manuel **et** par le détecteur.

---

## 9. Retour d'expérience et dépannage

| Symptôme | Cause / solution |
|---|---|
| Un portage direct du firmware C3 bloque le GL-S10 (pas de lien Ethernet, aucun log) | Partir du **YAML du proxy ESPHome GL-S10 qui démarre**, puis ajouter le composant. Valider chaque étape, garder le câble série branché, et reflasher le proxy si besoin. |
| Capture série vide / le port disparaît quand on alimente le GL-S10 | Alimenter le GL-S10 depuis le même ordinateur ; utiliser un lecteur qui se reconnecte (boucle pyserial). |
| `Failed to find Dst 0x0012` | Destination hors de la table des nœuds du provisioner → 4 éléments par nœud, plus de nœuds. |
| `RPLFull` / `Replay, Src …` puis délais dépassés | Liste anti-rejeu trop petite → `CRPL: 16`. |
| Luminosité affichée à 167 772 lx | `0xFFFFFF` = valeur inconnue → désormais ignorée. |
| Le mouvement clignote | Les lampes signalent un mouvement instantané → `delayed_off` (10 s par défaut). |
| `Authentication invalid` pendant l'OTA | Mot de passe OTA = mot de passe admin web → à mettre dans `secrets.yaml`. |
| L'intensité revient à 93 % | Scène 3 rappelée par le mode Auto → §8.3. |
| Allumage manuel très faible | Generic OnOff restaure la *dernière* intensité → la lumière modèle règle d'abord l'intensité. |
| `No outbound bearer found, inbound bearer 0` | Sans gravité : paquets relayés que la passerelle ne retransmet pas. |
| `request timed out` occasionnels sur les L 810 | Signal faible (-85 à -97 dBm) → rapprocher le GL-S10 ou le placer entre les lampes ; les lampes se relaient entre elles. |

---

## 10. Limites connues et pistes

- **Les changements provoqués par le détecteur sont interrogés** (3 à 6 s) : les lampes n'annoncent pas leur état
  allumée/éteinte. Les changements faits depuis Home Assistant s'affichent instantanément.
- **Message propriétaire `0xFEFF`** : l'écoute n'a reçu **aucun** message lors des allumages et variations commandés
  par le réseau Mesh. Restent à tester : les événements du détecteur et les actions depuis l'appli Steinel.
- **Piste B** (non réalisée) : configurer chaque lampe pour qu'elle publie son état Generic OnOff / Light Lightness
  vers un groupe (nécessite les clés d'appareil de la sauvegarde ; modifie la configuration des lampes).
- Les lampes supplémentaires n'utilisent pas toute la logique de transactions confirmées de la lampe principale.
- Juste après un retour en Auto, pendant environ 3 s, le détecteur peut encore utiliser l'intensité Steinel.
- Un seul GL-S10 par réseau Mesh a été testé ; une passerelle gère 1 + 4 lampes au maximum.
- Le sélecteur de mode de la lampe principale reste optimiste (comportement d'origine).

---

## 11. Sécurité

- **Ne publiez jamais** `secrets.yaml` ni `steinel-backup.json` (clés du réseau et des appareils).
- La passerelle stocke les clés du réseau Steinel : placez-la sur un VLAN de confiance / IoT.
- Changez le mot de passe admin web à la première connexion ; c'est aussi le mot de passe OTA.
- Activez le **chiffrement de l'API** (`api: encryption: key: !secret api_encryption_key`), désactivé dans la
  configuration testée par simplicité.

---

## 12. Licence et remerciements

- Licence : **GNU GPL v3.0**, héritée du projet d'origine (voir [`LICENSE`](LICENSE)).
  Conformément à la section 5 de la GPL-3.0, les fichiers modifiés dans ce fork sont indiqués dans ce README (§4)
  et dans l'historique git, avec leurs dates de modification.
- Projet d'origine et travail sur le protocole Steinel : **[supczinskib/steinel-nightmatiq-esp32-c3-gateway](https://github.com/supczinskib/steinel-nightmatiq-esp32-c3-gateway)**, un grand merci.
- Configuration ESPHome du GL-S10 : [blakadder/bluetooth-proxies](https://github.com/blakadder/bluetooth-proxies) et
  [devices.esphome.io](https://devices.esphome.io/devices/gl-inet-gl-s10/).
- Réalisé avec [ESPHome](https://esphome.io) et **ESP-BLE-MESH** d'Espressif (ESP-IDF).
- STEINEL, NightmatIQ, L 810 SC et L42 SC sont des marques de leurs propriétaires respectifs. Ce projet est
  indépendant et n'utilise que des modèles Bluetooth Mesh standard et des données observables publiquement.
