"""
PostgreSQL Tools - Ferramentas de acesso direto ao PostgreSQL
Acesso direto ao banco de dados PostgreSQL para queries e operações administrativas
"""

import os
from typing import Any, List, Dict, Optional
import logging

# Logger
log = logging.getLogger("sienge_mcp.postgres")

# Tentar importar psycopg
try:
    import psycopg
    from psycopg import sql

    PSYCOPG_AVAILABLE = True
except ImportError:
    PSYCOPG_AVAILABLE = False
    log.warning("psycopg não disponível. Instale: pip install psycopg[binary]")


# ============ HELPER FUNCTIONS ============

# Database padrão a ser usada (sempre ecbiesek, nunca ecbiesek-full)
DEFAULT_DATABASE = "ecbiesek"


def _normalize_connection_string(conn_str: str) -> str:
    """
    Normaliza a connection string para garantir uso da database 'ecbiesek'.
    
    Substitui 'ecbiesek-full' por 'ecbiesek' se encontrado na URL.
    """
    if not conn_str:
        return conn_str
    
    # Substituir ecbiesek-full por ecbiesek na connection string
    if "ecbiesek-full" in conn_str:
        log.info("Substituindo 'ecbiesek-full' por 'ecbiesek' na connection string")
        conn_str = conn_str.replace("ecbiesek-full", "ecbiesek")
    
    return conn_str


def _get_postgres_conn():
    """
    Cria uma conexão com Postgres usando variáveis de ambiente.
    
    Prioridade de conexão:
    1. PGHOST como connection string (postgres:// ou postgresql://) - para PostgreSQL direto
    2. Variáveis individuais: PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD
    3. POSTGRES_URL (connection string específica para PostgreSQL, não Supabase)
    4. DATABASE_URL (último recurso, pode apontar para Supabase)
    
    Nota: DATABASE_URL pode apontar para Supabase, então PGHOST tem prioridade.
    """
    if not PSYCOPG_AVAILABLE:
        raise ImportError("psycopg não está instalado. Instale: pip install psycopg[binary]")

    # Opção 1: PGHOST como connection string (PRIORIDADE - PostgreSQL direto)
    pghost = os.environ.get("PGHOST", "")
    if pghost and (pghost.startswith("postgres://") or pghost.startswith("postgresql://")):
        # Converter postgres:// para postgresql:// se necessário
        if pghost.startswith("postgres://"):
            pghost = pghost.replace("postgres://", "postgresql://", 1)
        # Normalizar para usar apenas 'ecbiesek' (não 'ecbiesek-full')
        pghost = _normalize_connection_string(pghost)
        try:
            log.info("Conectando via PGHOST (connection string) - database: ecbiesek")
            return psycopg.connect(pghost, connect_timeout=5)
        except Exception as e:
            log.error(f"Erro ao conectar via PGHOST: {e}")
            raise

    # Opção 2: POSTGRES_URL (connection string específica para PostgreSQL)
    postgres_url = os.environ.get("POSTGRES_URL")
    if postgres_url:
        if postgres_url.startswith("postgres://"):
            postgres_url = postgres_url.replace("postgres://", "postgresql://", 1)
        # Normalizar para usar apenas 'ecbiesek' (não 'ecbiesek-full')
        postgres_url = _normalize_connection_string(postgres_url)
        try:
            log.info("Conectando via POSTGRES_URL - database: ecbiesek")
            return psycopg.connect(postgres_url, connect_timeout=5)
        except Exception as e:
            log.warning(f"Erro ao conectar via POSTGRES_URL: {e}. Tentando variáveis individuais...")

    # Opção 3: Variáveis individuais (PGHOST, PGDATABASE, PGUSER, PGPASSWORD)
    required_vars = ["PGHOST", "PGDATABASE", "PGUSER", "PGPASSWORD"]
    missing = [var for var in required_vars if not os.environ.get(var)]
    if not missing:
        try:
            # Garantir que sempre use 'ecbiesek' (não 'ecbiesek-full')
            dbname = os.environ.get("PGDATABASE", DEFAULT_DATABASE)
            if dbname == "ecbiesek-full":
                log.info(f"Substituindo PGDATABASE 'ecbiesek-full' por 'ecbiesek'")
                dbname = DEFAULT_DATABASE
            elif not dbname:
                log.info(f"PGDATABASE não especificado, usando padrão: {DEFAULT_DATABASE}")
                dbname = DEFAULT_DATABASE
            
            log.info(f"Conectando via variáveis individuais - database: {dbname}")
            return psycopg.connect(
                host=os.environ["PGHOST"],
                port=int(os.environ.get("PGPORT", "5432")),
                dbname=dbname,
                user=os.environ["PGUSER"],
                password=os.environ["PGPASSWORD"],
                connect_timeout=5,
            )
        except Exception as e:
            log.warning(f"Erro ao conectar via variáveis individuais: {e}")

    # Opção 4: DATABASE_URL (último recurso - pode ser Supabase)
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        # Normalizar para usar apenas 'ecbiesek' (não 'ecbiesek-full')
        database_url = _normalize_connection_string(database_url)
        try:
            log.warning("Usando DATABASE_URL (pode apontar para Supabase). Considere usar PGHOST ou POSTGRES_URL para PostgreSQL direto.")
            return psycopg.connect(database_url, connect_timeout=5)
        except Exception as e:
            log.error(f"Erro ao conectar via DATABASE_URL: {e}")

    # Se chegou aqui, nenhuma opção funcionou
    raise ValueError(
        "Nenhuma configuração PostgreSQL encontrada. "
        "Configure uma das opções:\n"
        "1. PGHOST com connection string: postgresql://user:pass@host:port/dbname\n"
        "2. POSTGRES_URL com connection string\n"
        "3. Variáveis individuais: PGHOST, PGDATABASE, PGUSER, PGPASSWORD\n"
        "4. DATABASE_URL (último recurso, pode ser Supabase)"
    )


# ============ TOOLS PRINCIPAIS ============


async def list_postgres_tables(schema: str = "public") -> Dict:
    """
    Lista tabelas no schema especificado (default: public).
    Retorna apenas tabelas base (não views).

    Args:
        schema: Nome do schema (padrão: "public")

    Returns:
        Dict com success, tables (lista de nomes de tabelas) e schema
    """
    if not PSYCOPG_AVAILABLE:
        return {
            "success": False,
            "message": "❌ psycopg não disponível. Instale: pip install psycopg[binary]",
            "error": "PSYCOPG_NOT_AVAILABLE",
        }

    try:
        q = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s
              AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """
        with _get_postgres_conn() as conn, conn.cursor() as cur:
            cur.execute(q, (schema,))
            tables = [r[0] for r in cur.fetchall()]

        return {
            "success": True,
            "message": f"✅ Encontradas {len(tables)} tabelas no schema '{schema}'",
            "schema": schema,
            "tables": tables,
            "count": len(tables),
        }
    except Exception as e:
        log.error(f"Erro ao listar tabelas: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao listar tabelas: {str(e)}",
            "error": "LIST_TABLES_ERROR",
            "details": str(e),
        }


async def get_postgres_table_data(
    table: str,
    schema: str = "public",
    limit: int = 100,
    offset: int = 0,
    filters: Optional[Dict[str, Any]] = None,
    order_by: Optional[str] = None,
    search_term: Optional[str] = None,
    search_columns: Optional[List[str]] = None,
) -> Dict:
    """
    Busca dados de uma tabela PostgreSQL (read-only) com paginação e filtros.
    
    Segurança:
      - Valida se a tabela existe no schema via information_schema
      - Usa psycopg.sql para compor identificadores (evita SQL injection)
      - Apenas operações de leitura (SELECT)
      - Filtros são aplicados usando parâmetros seguros

    Args:
        table: Nome da tabela
        schema: Nome do schema (padrão: "public")
        limit: Limite de registros (1-1000, padrão: 100)
        offset: Deslocamento na lista (padrão: 0)
        filters: Filtros WHERE como dict {"campo": "valor"} ou {"campo": ["valor1", "valor2"]} para IN
        order_by: Campo para ordenação (ex: "nome_centrocusto", "id_credor DESC")
        search_term: Termo de busca textual (busca em múltiplas colunas com ILIKE)
        search_columns: Lista de colunas onde fazer busca textual (se não especificado, tenta detectar automaticamente)

    Returns:
        Dict com success, schema, table, columns, rows, limit, offset, count
    """
    if not PSYCOPG_AVAILABLE:
        return {
            "success": False,
            "message": "❌ psycopg não disponível. Instale: pip install psycopg[binary]",
            "error": "PSYCOPG_NOT_AVAILABLE",
        }

    # Validação de parâmetros
    if limit < 1 or limit > 1000:
        return {
            "success": False,
            "message": "❌ limit deve estar entre 1 e 1000",
            "error": "INVALID_LIMIT",
        }

    if offset < 0:
        return {
            "success": False,
            "message": "❌ offset deve ser >= 0",
            "error": "INVALID_OFFSET",
        }

    try:
        # Valida existência da tabela
        exists_q = """
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = %s AND table_name = %s
              AND table_type = 'BASE TABLE'
            LIMIT 1
        """

        with _get_postgres_conn() as conn, conn.cursor() as cur:
            cur.execute(exists_q, (schema, table))
            if cur.fetchone() is None:
                return {
                    "success": False,
                    "message": f"❌ Tabela não encontrada: {schema}.{table}",
                    "error": "TABLE_NOT_FOUND",
                    "schema": schema,
                    "table": table,
                }

            # Obter colunas da tabela para validação
            cols_q = """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position
            """
            cur.execute(cols_q, (schema, table))
            table_columns = {row[0]: row[1] for row in cur.fetchall()}
            all_cols = list(table_columns.keys())

            # Construir query com filtros
            where_conditions = []
            params = []

            # Aplicar filtros
            if filters:
                for field, value in filters.items():
                    if field not in table_columns:
                        return {
                            "success": False,
                            "message": f"❌ Coluna '{field}' não existe na tabela {schema}.{table}",
                            "error": "INVALID_COLUMN",
                            "schema": schema,
                            "table": table,
                            "column": field,
                            "available_columns": all_cols[:10],  # Mostrar primeiras 10
                        }
                    
                    if isinstance(value, list):
                        # Filtro IN - criar placeholders %s para cada valor
                        placeholders = sql.SQL(", ").join([sql.Placeholder() for _ in value])
                        where_conditions.append(
                            sql.SQL("{} IN ({})").format(
                                sql.Identifier(field),
                                placeholders
                            )
                        )
                        params.extend(value)
                    elif isinstance(value, str) and ("%" in value or "_" in value):
                        # Filtro ILIKE com pattern
                        where_conditions.append(
                            sql.SQL("{} ILIKE {}").format(
                                sql.Identifier(field),
                                sql.Placeholder()
                            )
                        )
                        params.append(value)
                    else:
                        # Filtro de igualdade
                        where_conditions.append(
                            sql.SQL("{} = {}").format(
                                sql.Identifier(field),
                                sql.Placeholder()
                            )
                        )
                        params.append(value)

            # Aplicar busca textual
            if search_term:
                if search_columns:
                    # Usar colunas especificadas
                    search_cols = [col for col in search_columns if col in table_columns]
                else:
                    # Detectar colunas de texto automaticamente
                    text_types = ['text', 'varchar', 'character varying', 'char']
                    search_cols = [
                        col for col, dtype in table_columns.items()
                        if any(dtype.lower().startswith(t) for t in text_types)
                    ]
                    # Limitar a 5 colunas para performance
                    search_cols = search_cols[:5]

                if search_cols:
                    search_conditions = []
                    search_pattern = f"%{search_term}%"
                    for col in search_cols:
                        search_conditions.append(
                            sql.SQL("{} ILIKE {}").format(
                                sql.Identifier(col),
                                sql.Placeholder()
                            )
                        )
                        # Adicionar o mesmo padrão para cada coluna
                        params.append(search_pattern)
                    where_conditions.append(
                        sql.SQL("({})").format(
                            sql.SQL(" OR ").join(search_conditions)
                        )
                    )

            # Construir WHERE clause
            where_clause = sql.SQL("")
            if where_conditions:
                where_clause = sql.SQL("WHERE {}").format(
                    sql.SQL(" AND ").join(where_conditions)
                )

            # Construir ORDER BY
            order_clause = sql.SQL("")
            if order_by:
                # Validar campo de ordenação
                order_parts = order_by.strip().split()
                order_field = order_parts[0]
                order_dir = order_parts[1].upper() if len(order_parts) > 1 else "ASC"
                
                if order_field not in table_columns:
                    return {
                        "success": False,
                        "message": f"❌ Coluna '{order_field}' não existe para ordenação",
                        "error": "INVALID_ORDER_BY_COLUMN",
                        "column": order_field,
                        "available_columns": all_cols[:10],
                    }
                
                if order_dir not in ["ASC", "DESC"]:
                    order_dir = "ASC"
                
                order_clause = sql.SQL("ORDER BY {} {}").format(
                    sql.Identifier(order_field),
                    sql.SQL(order_dir)
                )

            # Query segura com Identifiers (previne SQL injection)
            query = sql.SQL("SELECT * FROM {}.{} {} {} LIMIT {} OFFSET {}").format(
                sql.Identifier(schema),
                sql.Identifier(table),
                where_clause,
                order_clause,
                sql.Literal(limit),
                sql.Literal(offset),
            )

            # Executar query com parâmetros
            cur.execute(query, params)
            
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]

        return {
            "success": True,
            "message": f"✅ Dados recuperados da tabela {schema}.{table}",
            "schema": schema,
            "table": table,
            "columns": cols,
            "rows": [dict(zip(cols, r)) for r in rows],
            "limit": limit,
            "offset": offset,
            "count": len(rows),
        }
    except Exception as e:
        log.error(f"Erro ao buscar dados da tabela: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao buscar dados da tabela: {str(e)}",
            "error": "GET_TABLE_DATA_ERROR",
            "details": str(e),
            "schema": schema,
            "table": table,
        }


async def get_postgres_table_info(table: str, schema: str = "public") -> Dict:
    """
    Obtém informações sobre uma tabela PostgreSQL (colunas, tipos, constraints).

    Args:
        table: Nome da tabela
        schema: Nome do schema (padrão: "public")

    Returns:
        Dict com success, schema, table, columns (com tipos e constraints)
    """
    if not PSYCOPG_AVAILABLE:
        return {
            "success": False,
            "message": "❌ psycopg não disponível. Instale: pip install psycopg[binary]",
            "error": "PSYCOPG_NOT_AVAILABLE",
        }

    try:
        # Query para obter informações das colunas
        info_q = """
            SELECT 
                column_name,
                data_type,
                character_maximum_length,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
        """

        with _get_postgres_conn() as conn, conn.cursor() as cur:
            cur.execute(info_q, (schema, table))
            columns_info = cur.fetchall()

            if not columns_info:
                return {
                    "success": False,
                    "message": f"❌ Tabela não encontrada: {schema}.{table}",
                    "error": "TABLE_NOT_FOUND",
                    "schema": schema,
                    "table": table,
                }

            columns = []
            for col in columns_info:
                columns.append({
                    "name": col[0],
                    "data_type": col[1],
                    "max_length": col[2],
                    "nullable": col[3] == "YES",
                    "default": col[4],
                })

        return {
            "success": True,
            "message": f"✅ Informações da tabela {schema}.{table}",
            "schema": schema,
            "table": table,
            "columns": columns,
            "column_count": len(columns),
        }
    except Exception as e:
        log.error(f"Erro ao obter informações da tabela: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao obter informações da tabela: {str(e)}",
            "error": "GET_TABLE_INFO_ERROR",
            "details": str(e),
            "schema": schema,
            "table": table,
        }
