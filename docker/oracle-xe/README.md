# Oracle XE — RastroSeguro (referencia enterprise)

Stack de referencia para cumplir el estándar Oracle del PDF §16. **No es runtime del prototipo** (Python + CSV).

## Requisitos

- Docker Desktop
- ~2 GB RAM libres para Oracle XE

## Inicio rápido

```bash
cd docker/oracle-xe
docker compose up -d
```

Esperar ~2 min hasta que el healthcheck pase.

## Conexión

| Parámetro | Valor |
|-----------|-------|
| Host | localhost |
| Puerto | 1521 |
| Service | XEPDB1 |
| Usuario app | rastro |
| Password app | rastro |

## Aplicar esquema

Copiar [`db/oracle/schema.sql`](../../db/oracle/schema.sql) a `docker/oracle-xe/init/01_schema.sql` antes del primer `docker compose up`, o ejecutar manualmente:

```bash
docker exec -i rastoseguro-oracle-xe sqlplus rastro/rastro@XEPDB1 < ../../db/oracle/schema.sql
```

## Carga de datos demo

Ver [`db/oracle/load_csv.sql`](../../db/oracle/load_csv.sql) y [`scripts/load_synthetic_to_oracle.sh`](../../scripts/load_synthetic_to_oracle.sh).

## Notas

- Postgres/Supabase (`db/supabase/`) es la ruta analítica cloud del equipo.
- Oracle XE demuestra escalabilidad enterprise para el jurado.
