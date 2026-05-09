# SIBEC ERP (multi-PC, centralisé)

Cette version permet une architecture **serveur central + clients multi-PC**:

- Un seul serveur Flask héberge l'application et la base de données.
- Tous les postes clients se connectent à ce serveur.
- Les modifications faites par l'admin sont visibles immédiatement par les autres utilisateurs.

## 1) Prérequis

- Python 3.10+
- PostgreSQL 13+
- (Optionnel) `pg_dump` et `psql` pour backup/restauration

Installer dépendances:

```bash
cd <project_root>/sibec_erp
pip install -r requirements.txt
```

## 2) Configuration serveur

Créer un fichier `.env` depuis l'exemple:

```bash
cd <project_root>/sibec_erp
cp .env.example .env
```

Configurer au minimum:

- `DATABASE_URL` (PostgreSQL central)
- `SECRET_KEY`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`

Exemple:

```env
DATABASE_URL=postgresql+psycopg2://erp_user:erp_password@192.168.1.10:5432/sibec_erp
HOST=0.0.0.0
PORT=5000
FLASK_DEBUG=false
```

## 3) Migration base de données

```bash
cd <project_root>/sibec_erp
python migrate.py
```

## 4) Démarrage serveur

Linux:

```bash
cd <project_root>/sibec_erp
./scripts/start_server.sh
```

Windows:

```bat
cd /d C:\path\to\erp\sibec_erp
scripts\start_server.bat
```

## 5) Authentification et rôles

- `admin`: accès création/modification (mouvement, production, gestion utilisateurs)
- `user`: accès consultation (dashboard, stock, historique, KPI)

Le premier admin est créé automatiquement au démarrage via:

- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`

## 6) Client Windows multi-PC

Le client (`client.py` / EXE) permet de saisir l'URL du serveur central (IP ou DNS), puis l'enregistre localement dans `client_config.json`.

Exemple d'URL:

- `http://192.168.1.10:5000`

Lancement prêt à cliquer:

- Windows: double-cliquer `sibec_erp\scripts\start_client.bat`
- Windows: double-cliquer `sibec_erp/scripts/start_client.bat`
- Linux/macOS: exécuter `sibec_erp/scripts/start_client.sh` (ou le rendre exécutable puis double-cliquer selon l'environnement)

Pour reconstruire l'EXE:

```bash
cd <project_root>/sibec_erp
pyinstaller client.spec
```

## 7) Sécurité et fiabilité incluses

- Validation stricte des références et quantités
- Blocage des sorties provoquant un stock négatif
- Journal d'audit (logins, mouvements, production, gestion utilisateurs)
- Endpoint de santé: `GET /healthz`
- Debug désactivable en production (`FLASK_DEBUG=false`)

## 8) Exploitation

Backup PostgreSQL:

```bash
cd <project_root>/sibec_erp
export DATABASE_URL='postgresql://...'
./scripts/backup_postgres.sh
```

Restore PostgreSQL:

```bash
cd <project_root>/sibec_erp
export DATABASE_URL='postgresql://...'
./scripts/restore_postgres.sh backup_YYYYMMDD_HHMMSS.sql
```

Healthcheck:

```bash
cd <project_root>/sibec_erp
./scripts/healthcheck.sh http://127.0.0.1:5000/healthz
```

## 9) Validation de mise en service (checklist)

- Connexion admin et création d'un utilisateur `user`
- Ajout d'un mouvement/production par admin
- Vérification immédiate sur un autre PC connecté
- Vérification des restrictions de droits (`user` ne peut pas modifier)
- Redémarrage serveur et re-test des connexions
