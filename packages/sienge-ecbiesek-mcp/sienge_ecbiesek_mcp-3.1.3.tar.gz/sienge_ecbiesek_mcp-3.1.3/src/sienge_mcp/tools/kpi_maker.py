"""
KPI Maker Tools - Ferramentas para criar, calcular e gerenciar KPIs
Cria KPIs baseados em dados do Sienge (PostgreSQL) e armazena resultados no PostgreSQL do Railway
"""

import os
import hashlib
import json
import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
from decimal import Decimal

# Logger
log = logging.getLogger("sienge_mcp.kpi_maker")

# Tentar importar psycopg
try:
    import psycopg
    from psycopg import sql
    PSYCOPG_AVAILABLE = True
except ImportError:
    PSYCOPG_AVAILABLE = False
    log.warning("psycopg não disponível. Instale: pip install psycopg[binary]")


# ============ HELPER FUNCTIONS ============

def _get_sienge_postgres_conn():
    """
    Cria uma conexão com PostgreSQL do Sienge (banco de dados de origem).
    Usa as mesmas variáveis de ambiente que postgres_tools.py.
    
    Prioridade de conexão:
    1. PGHOST como connection string (postgres:// ou postgresql://)
    2. POSTGRES_URL (connection string específica para PostgreSQL)
    3. Variáveis individuais: PGHOST, PGDATABASE, PGUSER, PGPASSWORD
    4. DATABASE_URL (último recurso)
    
    Nota: Este banco é usado para BUSCAR dados do Sienge.
    """
    if not PSYCOPG_AVAILABLE:
        raise ImportError("psycopg não está instalado. Instale: pip install psycopg[binary]")

    # Opção 1: PGHOST como connection string
    pghost = os.environ.get("PGHOST", "")
    if pghost and (pghost.startswith("postgres://") or pghost.startswith("postgresql://")):
        if pghost.startswith("postgres://"):
            pghost = pghost.replace("postgres://", "postgresql://", 1)
        try:
            log.info("Conectando ao PostgreSQL do Sienge via PGHOST (connection string)")
            return psycopg.connect(pghost, connect_timeout=10)
        except Exception as e:
            log.error(f"Erro ao conectar via PGHOST: {e}")
            raise

    # Opção 2: POSTGRES_URL
    postgres_url = os.environ.get("POSTGRES_URL")
    if postgres_url:
        if postgres_url.startswith("postgres://"):
            postgres_url = postgres_url.replace("postgres://", "postgresql://", 1)
        try:
            log.info("Conectando ao PostgreSQL do Sienge via POSTGRES_URL")
            return psycopg.connect(postgres_url, connect_timeout=10)
        except Exception as e:
            log.warning(f"Erro ao conectar via POSTGRES_URL: {e}. Tentando outras opções...")

    # Opção 3: Variáveis individuais
    required_vars = ["PGHOST", "PGDATABASE", "PGUSER", "PGPASSWORD"]
    missing = [var for var in required_vars if not os.environ.get(var)]
    if not missing:
        try:
            dbname = os.environ.get("PGDATABASE", "ecbiesek")
            log.info(f"Conectando ao PostgreSQL do Sienge via variáveis individuais - database: {dbname}")
            return psycopg.connect(
                host=os.environ["PGHOST"],
                port=int(os.environ.get("PGPORT", "5432")),
                dbname=dbname,
                user=os.environ["PGUSER"],
                password=os.environ["PGPASSWORD"],
                connect_timeout=10,
            )
        except Exception as e:
            log.warning(f"Erro ao conectar via variáveis individuais: {e}")

    # Opção 4: DATABASE_URL (último recurso)
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        try:
            log.warning("Usando DATABASE_URL para conectar ao PostgreSQL do Sienge")
            return psycopg.connect(database_url, connect_timeout=10)
        except Exception as e:
            log.error(f"Erro ao conectar via DATABASE_URL: {e}")

    raise ValueError(
        "Nenhuma configuração PostgreSQL do Sienge encontrada. "
        "Configure PGHOST, POSTGRES_URL ou variáveis individuais (PGHOST, PGDATABASE, PGUSER, PGPASSWORD)"
    )


def _get_postgres_conn():
    """
    Cria uma conexão com PostgreSQL do Railway.
    
    Prioridade de conexão (variáveis com "railway" no nome):
    1. RAILWAY_POSTGRES_URL - Connection string do Railway PostgreSQL
    2. RAILWAY_DATABASE_URL - Alternativa do Railway
    3. RAILWAY_PGHOST - Connection string alternativa
    4. Variáveis individuais com prefixo RAILWAY_: RAILWAY_PGHOST, RAILWAY_PGDATABASE, RAILWAY_PGUSER, RAILWAY_PGPASSWORD
    5. Fallback para variáveis sem prefixo (POSTGRES_URL, DATABASE_URL, etc.)
    
    Nota: Os KPIs são armazenados em um banco PostgreSQL separado no Railway.
    Usamos variáveis com "railway" no nome para evitar conflito com outros bancos.
    """
    if not PSYCOPG_AVAILABLE:
        raise ImportError("psycopg não está instalado. Instale: pip install psycopg[binary]")

    # Opção 1: RAILWAY_POSTGRES_URL (prioridade - específico para Railway)
    railway_postgres_url = os.environ.get("RAILWAY_POSTGRES_URL")
    if railway_postgres_url:
        if railway_postgres_url.startswith("postgres://"):
            railway_postgres_url = railway_postgres_url.replace("postgres://", "postgresql://", 1)
        try:
            log.info("Conectando ao PostgreSQL do Railway via RAILWAY_POSTGRES_URL")
            return psycopg.connect(railway_postgres_url, connect_timeout=10)
        except Exception as e:
            log.warning(f"Erro ao conectar via RAILWAY_POSTGRES_URL: {e}. Tentando outras opções...")

    # Opção 2: RAILWAY_DATABASE_URL
    railway_database_url = os.environ.get("RAILWAY_DATABASE_URL")
    if railway_database_url:
        if railway_database_url.startswith("postgres://"):
            railway_database_url = railway_database_url.replace("postgres://", "postgresql://", 1)
        try:
            log.info("Conectando ao PostgreSQL do Railway via RAILWAY_DATABASE_URL")
            return psycopg.connect(railway_database_url, connect_timeout=10)
        except Exception as e:
            log.warning(f"Erro ao conectar via RAILWAY_DATABASE_URL: {e}. Tentando outras opções...")

    # Opção 3: RAILWAY_PGHOST como connection string
    railway_pghost = os.environ.get("RAILWAY_PGHOST", "")
    if railway_pghost and (railway_pghost.startswith("postgres://") or railway_pghost.startswith("postgresql://")):
        if railway_pghost.startswith("postgres://"):
            railway_pghost = railway_pghost.replace("postgres://", "postgresql://", 1)
        try:
            log.info("Conectando ao PostgreSQL do Railway via RAILWAY_PGHOST (connection string)")
            return psycopg.connect(railway_pghost, connect_timeout=10)
        except Exception as e:
            log.warning(f"Erro ao conectar via RAILWAY_PGHOST: {e}. Tentando outras opções...")

    # Opção 4: Variáveis individuais com prefixo RAILWAY_
    railway_vars = {
        "host": os.environ.get("RAILWAY_PGHOST"),
        "database": os.environ.get("RAILWAY_PGDATABASE"),
        "user": os.environ.get("RAILWAY_PGUSER"),
        "password": os.environ.get("RAILWAY_PGPASSWORD"),
    }
    if all(railway_vars.values()):
        try:
            dbname = railway_vars["database"] or "postgres"
            log.info(f"Conectando ao PostgreSQL do Railway via variáveis RAILWAY_* - database: {dbname}")
            return psycopg.connect(
                host=railway_vars["host"],
                port=int(os.environ.get("RAILWAY_PGPORT", "5432")),
                dbname=dbname,
                user=railway_vars["user"],
                password=railway_vars["password"],
                connect_timeout=10,
            )
        except Exception as e:
            log.warning(f"Erro ao conectar via variáveis RAILWAY_*: {e}. Tentando fallback...")

    # Opção 5: Fallback para variáveis sem prefixo (compatibilidade)
    postgres_url = os.environ.get("POSTGRES_URL")
    if postgres_url:
        if postgres_url.startswith("postgres://"):
            postgres_url = postgres_url.replace("postgres://", "postgresql://", 1)
        try:
            log.warning("Usando POSTGRES_URL (fallback). Considere usar RAILWAY_POSTGRES_URL para evitar conflitos.")
            return psycopg.connect(postgres_url, connect_timeout=10)
        except Exception as e:
            log.warning(f"Erro ao conectar via POSTGRES_URL: {e}")

    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        try:
            log.warning("Usando DATABASE_URL (fallback). Considere usar RAILWAY_DATABASE_URL para evitar conflitos.")
            return psycopg.connect(database_url, connect_timeout=10)
        except Exception as e:
            log.warning(f"Erro ao conectar via DATABASE_URL: {e}")

    raise ValueError(
        "Nenhuma configuração PostgreSQL do Railway encontrada. "
        "Configure uma das opções (recomendado usar prefixo RAILWAY_):\n"
        "1. RAILWAY_POSTGRES_URL (connection string do Railway)\n"
        "2. RAILWAY_DATABASE_URL (alternativa)\n"
        "3. RAILWAY_PGHOST (connection string alternativa)\n"
        "4. Variáveis individuais: RAILWAY_PGHOST, RAILWAY_PGDATABASE, RAILWAY_PGUSER, RAILWAY_PGPASSWORD\n"
        "5. Fallback: POSTGRES_URL ou DATABASE_URL (não recomendado se houver outros bancos)"
    )


def _ensure_kpi_schema():
    """
    Garante que as tabelas de KPI existem no banco.
    Executa o schema se necessário.
    """
    try:
        schema_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "Database",
            "kpi_schema.sql"
        )
        
        # Tentar caminho alternativo
        if not os.path.exists(schema_path):
            schema_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "Database",
                "kpi_schema.sql"
            )
        
        if os.path.exists(schema_path):
            with open(schema_path, "r", encoding="utf-8") as f:
                schema_sql = f.read()
            
            with _get_postgres_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(schema_sql)
                    conn.commit()
            log.info("Schema de KPI verificado/criado com sucesso")
        else:
            log.warning(f"Schema SQL não encontrado em {schema_path}. Criando tabelas manualmente...")
            # Criar tabelas manualmente se o arquivo não existir
            with _get_postgres_conn() as conn:
                with conn.cursor() as cur:
                    # Tabela de definições
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS kpi_definitions (
                          id            bigserial PRIMARY KEY,
                          kpi_name      text        NOT NULL UNIQUE,
                          owner         text        NOT NULL,
                          description   text        NOT NULL DEFAULT '',
                          cadence       text        NOT NULL CHECK (cadence IN ('daily','biweekly','monthly')),
                          lookback_days int         NOT NULL DEFAULT 7 CHECK (lookback_days >= 0 AND lookback_days <= 365),
                          timezone      text        NOT NULL DEFAULT 'America/Sao_Paulo',
                          version       text        NOT NULL DEFAULT 'v1',
                          active        boolean     NOT NULL DEFAULT true,
                          definition    jsonb       NOT NULL,
                          source_tables jsonb       NOT NULL DEFAULT '[]'::jsonb,
                          created_at    timestamptz NOT NULL DEFAULT now(),
                          updated_at    timestamptz NOT NULL DEFAULT now()
                        )
                    """)
                    
                    # Tabela de valores
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS kpi_values (
                          id              bigserial PRIMARY KEY,
                          kpi_name        text        NOT NULL,
                          version         text        NOT NULL DEFAULT 'v1',
                          period_start    date        NOT NULL,
                          period_end      date        NOT NULL,
                          cadence         text        NOT NULL CHECK (cadence IN ('daily','biweekly','monthly')),
                          params          jsonb       NOT NULL DEFAULT '{}'::jsonb,
                          params_hash     text        NOT NULL,
                          value           numeric     NOT NULL,
                          unit            text,
                          computed_at     timestamptz NOT NULL DEFAULT now(),
                          meta            jsonb       NOT NULL DEFAULT '{}'::jsonb,
                          CONSTRAINT kpi_values_period_check CHECK (period_end > period_start)
                        )
                    """)
                    
                    # Índices
                    cur.execute("""
                        CREATE UNIQUE INDEX IF NOT EXISTS kpi_values_uniq
                          ON kpi_values (kpi_name, version, cadence, period_start, period_end, params_hash)
                    """)
                    
                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS kpi_values_lookup
                          ON kpi_values (kpi_name, period_start, period_end)
                    """)
                    
                    conn.commit()
            log.info("Tabelas de KPI criadas manualmente")
    except Exception as e:
        log.error(f"Erro ao criar schema de KPI: {e}", exc_info=True)
        # Não falhar se as tabelas já existirem
        pass


def _hash_params(params: Dict[str, Any]) -> str:
    """Gera hash dos parâmetros para garantir unicidade"""
    params_str = json.dumps(params, sort_keys=True)
    return hashlib.md5(params_str.encode()).hexdigest()


def _calculate_period(cadence: str, lookback_days: int, reference_date: Optional[date] = None) -> tuple[date, date]:
    """
    Calcula o período baseado na cadência e lookback_days.
    
    Args:
        cadence: 'daily', 'biweekly', 'monthly'
        lookback_days: Quantos dias olhar para trás
        reference_date: Data de referência (padrão: hoje)
    
    Returns:
        (period_start, period_end) onde period_end é exclusivo
    """
    if reference_date is None:
        reference_date = date.today()
    
    period_end = reference_date
    
    if cadence == "daily":
        period_start = period_end - timedelta(days=lookback_days)
    elif cadence == "biweekly":
        # Últimas 2 semanas
        period_start = period_end - timedelta(days=14)
    elif cadence == "monthly":
        # Último mês
        period_start = period_end - timedelta(days=30)
    else:
        # Fallback para lookback_days
        period_start = period_end - timedelta(days=lookback_days)
    
    return period_start, period_end


def _extract_table_names_from_sql(sql_query: str) -> List[str]:
    """
    Extrai nomes de tabelas de uma query SQL.
    
    Detecta tabelas em:
    - FROM clauses
    - JOIN clauses (INNER JOIN, LEFT JOIN, RIGHT JOIN, CROSS JOIN)
    - Tabelas dentro de CTEs (WITH ... AS)
    
    NÃO inclui nomes de CTEs (apenas tabelas reais).
    
    Args:
        sql_query: Query SQL a analisar
        
    Returns:
        Lista de nomes de tabelas únicos encontrados (apenas tabelas reais, não CTEs)
    """
    if not sql_query:
        return []
    
    tables = set()
    cte_names = set()  # Nomes de CTEs para filtrar depois
    
    # Normalizar espaços e quebras de linha, mas manter estrutura
    sql_normalized = re.sub(r'\s+', ' ', sql_query.strip())
    
    # Palavras-chave SQL que não são tabelas
    sql_keywords = {
        'select', 'from', 'where', 'group', 'order', 'having', 'union', 'intersect', 
        'except', 'inner', 'left', 'right', 'full', 'cross', 'join', 'on', 'using',
        'as', 'case', 'when', 'then', 'else', 'end', 'with', 'and', 'or', 'not',
        'null', 'coalesce', 'sum', 'count', 'avg', 'max', 'min', 'distinct',
        'by', 'in', 'exists', 'like', 'ilike', 'between', 'is', 'if', 'cast'
    }
    
    # Padrão para nomes de tabelas (permite underscores e letras/números)
    # Exemplo: contas_a_receber, tabela123, schema.tabela_nome
    table_name_pattern = r'[a-zA-Z_][a-zA-Z0-9_]*'
    
    # 0. Primeiro, extrair TODOS os nomes de CTEs para filtrá-los depois
    # Padrão: WITH nome_cte AS (...) ou WITH cte1 AS (...), cte2 AS (...)
    # Estratégia simples: buscar todos os padrões "nome AS (" que aparecem após "WITH"
    # e antes do primeiro SELECT principal (que não está dentro de parênteses)
    
    # Encontrar a posição do "WITH"
    with_match = re.search(r'\bWITH\s+', sql_normalized, re.IGNORECASE)
    if with_match:
        with_start = with_match.end()
        
        # Encontrar o primeiro SELECT que não está dentro de um CTE
        # (o SELECT principal vem após todos os CTEs)
        select_matches = list(re.finditer(r'\bSELECT\s+', sql_normalized, re.IGNORECASE))
        main_select_pos = None
        
        for sel_match in select_matches:
            sel_pos = sel_match.start()
            if sel_pos <= with_start:
                continue
            
            # Contar parênteses abertos entre WITH e este SELECT
            paren_count = 0
            for i in range(with_start, sel_pos):
                if sql_normalized[i] == '(':
                    paren_count += 1
                elif sql_normalized[i] == ')':
                    paren_count -= 1
            
            # Se não há parênteses abertos, este é o SELECT principal
            if paren_count == 0:
                main_select_pos = sel_pos
                break
        
        # Extrair o bloco WITH (entre WITH e o SELECT principal)
        if main_select_pos:
            with_block = sql_normalized[with_start:main_select_pos]
        else:
            # Fallback: usar até o final se não encontrarmos o SELECT principal
            with_block = sql_normalized[with_start:]
        
        # Buscar todos os nomes de CTEs neste bloco
        # Padrão: nome AS ( (pode ter vírgula antes ou ser o primeiro após WITH)
        # Usar dois padrões: um para o primeiro CTE após WITH, outro para CTEs após vírgulas
        cte_pattern_first = rf'^({table_name_pattern})\s+AS\s*\('
        cte_pattern_comma = rf',\s*({table_name_pattern})\s+AS\s*\('
        
        # Buscar primeiro CTE (logo após WITH)
        first_match = re.search(cte_pattern_first, with_block.strip(), re.IGNORECASE)
        if first_match:
            cte_name = first_match.group(1)
            if cte_name and cte_name.lower() not in sql_keywords:
                cte_names.add(cte_name.lower())
        
        # Buscar CTEs após vírgulas
        comma_matches = re.finditer(cte_pattern_comma, with_block, re.IGNORECASE)
        for match in comma_matches:
            cte_name = match.group(1)
            if cte_name and cte_name.lower() not in sql_keywords:
                cte_names.add(cte_name.lower())
        
        # Debug: verificar se CTEs foram capturados (remover depois)
        # print(f"DEBUG: CTEs encontrados: {cte_names}")
    
    # 1. Extrair tabelas dentro de CTEs (WITH ... AS) - estas são as tabelas reais
    # Padrão: WITH nome_cte AS (SELECT ... FROM tabela_real ...)
    # Buscar FROM dentro de cada CTE - estas são tabelas reais do banco
    # Usar uma abordagem mais robusta: encontrar cada CTE e buscar FROM dentro dele
    cte_blocks = re.finditer(rf'\bWITH\s+{table_name_pattern}\s+AS\s*\(', sql_normalized, re.IGNORECASE)
    for cte_block in cte_blocks:
        # Encontrar o final do CTE (parêntese de fechamento correspondente)
        start_pos = cte_block.end()
        paren_count = 1
        end_pos = start_pos
        while end_pos < len(sql_normalized) and paren_count > 0:
            if sql_normalized[end_pos] == '(':
                paren_count += 1
            elif sql_normalized[end_pos] == ')':
                paren_count -= 1
            end_pos += 1
        
        if paren_count == 0:
            # Extrair conteúdo do CTE
            cte_content = sql_normalized[start_pos:end_pos-1]
            # Buscar FROM dentro deste CTE
            cte_from_pattern = rf'\bFROM\s+(?:({table_name_pattern})\.)?({table_name_pattern})(?:\s+(?:AS\s+)?\w+)?'
            cte_from_matches = re.finditer(cte_from_pattern, cte_content, re.IGNORECASE)
            for match in cte_from_matches:
                table = match.group(2)
                if table and table.lower() not in sql_keywords and len(table) > 2:
                    # Verificar se não é um CTE (pode haver CTEs aninhados)
                    if table.lower() not in cte_names:
                        tables.add(table.lower())
            
            # Também buscar JOIN dentro do CTE
            cte_join_pattern = rf'\b(?:INNER|LEFT|RIGHT|FULL|CROSS)?\s*JOIN\s+(?:({table_name_pattern})\.)?({table_name_pattern})(?:\s+(?:AS\s+)?\w+)?'
            cte_join_matches = re.finditer(cte_join_pattern, cte_content, re.IGNORECASE)
            for match in cte_join_matches:
                table = match.group(2)
                if table and table.lower() not in sql_keywords and len(table) > 2:
                    if table.lower() not in cte_names:
                        tables.add(table.lower())
    
    # 2. Extrair tabelas de FROM clauses no SELECT principal (após os CTEs)
    # IMPORTANTE: Ignorar completamente o FROM/JOIN que referencia CTEs
    # Padrão: FROM tabela [AS alias] ou FROM schema.tabela
    # Mas ignorar se for um CTE
    from_pattern = rf'\bFROM\s+(?:({table_name_pattern})\.)?({table_name_pattern})(?:\s+(?:AS\s+)?\w+)?'
    from_matches = re.finditer(from_pattern, sql_normalized, re.IGNORECASE)
    for match in from_matches:
        table = match.group(2)  # group(1) é schema, group(2) é tabela
        if table and table.lower() not in sql_keywords and len(table) > 2:
            # Verificar se não é um CTE - se for CTE, NÃO adicionar
            table_lower = table.lower()
            if table_lower not in cte_names:
                tables.add(table_lower)
    
    # 3. Extrair tabelas de JOIN clauses
    # IMPORTANTE: Ignorar completamente o JOIN que referencia CTEs
    # Padrão: [INNER|LEFT|RIGHT|FULL|CROSS] JOIN tabela [AS alias]
    # Mas ignorar se for um CTE
    join_pattern = rf'\b(?:INNER|LEFT|RIGHT|FULL|CROSS)?\s*JOIN\s+(?:({table_name_pattern})\.)?({table_name_pattern})(?:\s+(?:AS\s+)?\w+)?'
    join_matches = re.finditer(join_pattern, sql_normalized, re.IGNORECASE)
    for match in join_matches:
        table = match.group(2)
        if table and table.lower() not in sql_keywords and len(table) > 2:
            # Verificar se não é um CTE - se for CTE, NÃO adicionar
            table_lower = table.lower()
            if table_lower not in cte_names:
                tables.add(table_lower)
    
    # 4. Filtrar palavras-chave SQL, CTEs e valores muito curtos
    # Esta é uma verificação final para garantir que nenhum CTE passou
    # Usar set comprehension com verificação explícita
    filtered_tables = set()
    for t in tables:
        t_lower = t.lower()
        if (t_lower not in sql_keywords and 
            t_lower not in cte_names and 
            len(t) > 2):
            filtered_tables.add(t_lower)
    
    tables = filtered_tables
    
    # Ordenar e retornar
    return sorted(list(tables))


# ============ MAIN FUNCTIONS ============


async def create_kpi_definition(
    kpi_name: str,
    owner: str,
    definition: Dict[str, Any],
    description: str = "",
    cadence: str = "daily",
    lookback_days: int = 7,
    timezone: str = "America/Sao_Paulo",
    version: str = "v1",
    source_tables: Optional[List[str]] = None,
    active: bool = True,
) -> Dict:
    """
    Cria ou atualiza uma definição de KPI.
    
    Args:
        kpi_name: Nome único do KPI
        owner: Proprietário/responsável pelo KPI
        definition: JSONB com a definição do cálculo
                   Exemplo: {"type": "sql_scalar", "sql": "SELECT SUM(valor) FROM tabela", "unit": "BRL"}
        description: Descrição do KPI
        cadence: Frequência de cálculo ('daily', 'biweekly', 'monthly')
        lookback_days: Quantos dias olhar para trás (0-365)
        timezone: Timezone (padrão: 'America/Sao_Paulo')
        version: Versão do KPI (padrão: 'v1')
        source_tables: Lista de tabelas usadas (para auditoria)
        active: Se o KPI está ativo
    
    Returns:
        Dict com success, message e dados do KPI criado
    """
    if not PSYCOPG_AVAILABLE:
        return {
            "success": False,
            "message": "❌ psycopg não disponível. Instale: pip install psycopg[binary]",
            "error": "PSYCOPG_NOT_AVAILABLE",
        }
    
    # Validações
    if cadence not in ["daily", "biweekly", "monthly"]:
        return {
            "success": False,
            "message": "❌ cadence deve ser 'daily', 'biweekly' ou 'monthly'",
            "error": "INVALID_CADENCE",
        }
    
    if lookback_days < 0 or lookback_days > 365:
        return {
            "success": False,
            "message": "❌ lookback_days deve estar entre 0 e 365",
            "error": "INVALID_LOOKBACK_DAYS",
        }
    
    if not definition or not isinstance(definition, dict):
        return {
            "success": False,
            "message": "❌ definition deve ser um dict JSON válido",
            "error": "INVALID_DEFINITION",
        }
    
    try:
        _ensure_kpi_schema()
        
        # Extrair tabelas automaticamente do SQL se não foram fornecidas
        sql_query = definition.get("sql", "")
        if sql_query:
            # Se source_tables não foi fornecido ou está vazio, extrair automaticamente
            if source_tables is None or (isinstance(source_tables, list) and len(source_tables) == 0):
                extracted_tables = _extract_table_names_from_sql(sql_query)
                if extracted_tables:
                    source_tables = extracted_tables
                    log.info(f"✅ Tabelas extraídas automaticamente do SQL: {source_tables}")
                else:
                    source_tables = []
                    log.info("⚠️ Nenhuma tabela encontrada no SQL")
            else:
                log.info(f"Usando tabelas fornecidas manualmente: {source_tables}")
        else:
            source_tables = source_tables or []
        
        source_tables_json = json.dumps(source_tables or [])
        definition_json = json.dumps(definition)
        
        with _get_postgres_conn() as conn:
            with conn.cursor() as cur:
                # UPSERT: atualizar se existir, criar se não existir
                cur.execute("""
                    INSERT INTO kpi_definitions (
                        kpi_name, owner, description, cadence, lookback_days,
                        timezone, version, active, definition, source_tables
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb)
                    ON CONFLICT (kpi_name) DO UPDATE SET
                        owner = EXCLUDED.owner,
                        description = EXCLUDED.description,
                        cadence = EXCLUDED.cadence,
                        lookback_days = EXCLUDED.lookback_days,
                        timezone = EXCLUDED.timezone,
                        version = EXCLUDED.version,
                        active = EXCLUDED.active,
                        definition = EXCLUDED.definition,
                        source_tables = EXCLUDED.source_tables,
                        updated_at = now()
                    RETURNING id, kpi_name, created_at, updated_at
                """, (
                    kpi_name, owner, description, cadence, lookback_days,
                    timezone, version, active, definition_json, source_tables_json
                ))
                
                result = cur.fetchone()
                conn.commit()
                
                return {
                    "success": True,
                    "message": f"✅ KPI '{kpi_name}' criado/atualizado com sucesso",
                    "kpi": {
                        "id": result[0],
                        "kpi_name": result[1],
                        "created_at": result[2].isoformat() if result[2] else None,
                        "updated_at": result[3].isoformat() if result[3] else None,
                    },
                    "source_tables": source_tables,  # Retornar tabelas detectadas
                }
    
    except Exception as e:
        log.error(f"Erro ao criar definição de KPI: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao criar definição de KPI: {str(e)}",
            "error": "CREATE_KPI_ERROR",
            "details": str(e),
        }


async def calculate_kpi(
    kpi_name: str,
    period_start: Optional[str] = None,
    period_end: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
    force_recalculate: bool = False,
) -> Dict:
    """
    Calcula um KPI e salva o resultado.
    
    Args:
        kpi_name: Nome do KPI a calcular
        period_start: Data de início do período (YYYY-MM-DD). Se None, usa lookback_days da definição
        period_end: Data de fim do período (YYYY-MM-DD, exclusivo). Se None, usa hoje
        params: Parâmetros adicionais para o cálculo (opcional)
        force_recalculate: Se True, recalcula mesmo se já existir valor para o período
    
    Returns:
        Dict com success, message, value e metadados
    """
    if not PSYCOPG_AVAILABLE:
        return {
            "success": False,
            "message": "❌ psycopg não disponível. Instale: pip install psycopg[binary]",
            "error": "PSYCOPG_NOT_AVAILABLE",
        }
    
    try:
        _ensure_kpi_schema()
        
        # Buscar definição do KPI
        with _get_postgres_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT kpi_name, owner, description, cadence, lookback_days,
                           timezone, version, active, definition, source_tables
                    FROM kpi_definitions
                    WHERE kpi_name = %s
                """, (kpi_name,))
                
                row = cur.fetchone()
                if not row:
                    return {
                        "success": False,
                        "message": f"❌ KPI '{kpi_name}' não encontrado",
                        "error": "KPI_NOT_FOUND",
                    }
                
                kpi_def = {
                    "kpi_name": row[0],
                    "owner": row[1],
                    "description": row[2],
                    "cadence": row[3],
                    "lookback_days": row[4],
                    "timezone": row[5],
                    "version": row[6],
                    "active": row[7],
                    "definition": row[8],
                    "source_tables": row[9],
                }
                
                if not kpi_def["active"]:
                    return {
                        "success": False,
                        "message": f"❌ KPI '{kpi_name}' está inativo",
                        "error": "KPI_INACTIVE",
                    }
        
        # Calcular período se não fornecido
        if period_start is None or period_end is None:
            p_start, p_end = _calculate_period(
                kpi_def["cadence"],
                kpi_def["lookback_days"]
            )
            period_start = period_start or p_start.isoformat()
            period_end = period_end or p_end.isoformat()
        
        period_start_date = datetime.strptime(period_start, "%Y-%m-%d").date()
        period_end_date = datetime.strptime(period_end, "%Y-%m-%d").date()
        
        if period_end_date <= period_start_date:
            return {
                "success": False,
                "message": "❌ period_end deve ser maior que period_start",
                "error": "INVALID_PERIOD",
            }
        
        # Verificar se já existe (a menos que force_recalculate)
        params = params or {}
        params_hash = _hash_params(params)
        
        if not force_recalculate:
            with _get_postgres_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, value, unit, computed_at
                        FROM kpi_values
                        WHERE kpi_name = %s
                          AND version = %s
                          AND cadence = %s
                          AND period_start = %s
                          AND period_end = %s
                          AND params_hash = %s
                    """, (
                        kpi_name, kpi_def["version"], kpi_def["cadence"],
                        period_start_date, period_end_date, params_hash
                    ))
                    
                    existing = cur.fetchone()
                    if existing:
                        return {
                            "success": True,
                            "message": f"✅ KPI '{kpi_name}' já calculado para este período",
                            "value": float(existing[1]),
                            "unit": existing[2],
                            "computed_at": existing[3].isoformat() if existing[3] else None,
                            "cached": True,
                        }
        
        # Executar cálculo baseado no tipo de definição
        definition = kpi_def["definition"]
        calc_type = definition.get("type", "sql_scalar")
        
        # Determinar qual banco usar para executar a query
        # "sienge" = banco do Sienge (PGHOST, etc.), "railway" = banco do Railway (RAILWAY_*)
        # Padrão: "railway" para manter compatibilidade
        database_source = definition.get("database", "railway")
        
        value = None
        unit = definition.get("unit")
        meta = {}
        
        if calc_type == "sql_scalar":
            # Executar SQL que retorna um único valor
            sql_query = definition.get("sql")
            if not sql_query:
                return {
                    "success": False,
                    "message": "❌ definition.type='sql_scalar' requer definition.sql",
                    "error": "MISSING_SQL",
                }
            
            # Substituir placeholders de período se existirem
            sql_query = sql_query.replace("{{period_start}}", period_start)
            sql_query = sql_query.replace("{{period_end}}", period_end)
            
            # Substituir parâmetros se existirem
            for key, val in params.items():
                sql_query = sql_query.replace(f"{{{{{key}}}}}", str(val))
            
            # Escolher conexão baseado no database_source
            if database_source == "sienge":
                conn_func = _get_sienge_postgres_conn
                meta["database_source"] = "sienge"
            else:
                conn_func = _get_postgres_conn
                meta["database_source"] = "railway"
            
            try:
                with conn_func() as conn:
                    with conn.cursor() as cur:
                        cur.execute(sql_query)
                        result = cur.fetchone()
                        if result:
                            value = float(result[0]) if result[0] is not None else 0.0
                        else:
                            value = 0.0
                        
                        meta["sql_executed"] = sql_query
                        meta["execution_time"] = datetime.now().isoformat()
            except Exception as e:
                return {
                    "success": False,
                    "message": f"❌ Erro ao executar SQL no banco {database_source}: {str(e)}",
                    "error": "SQL_EXECUTION_ERROR",
                    "database_source": database_source,
                    "details": str(e),
                }
        
        elif calc_type == "sql_aggregate":
            # Similar ao sql_scalar, mas pode retornar múltiplas colunas
            sql_query = definition.get("sql")
            if not sql_query:
                return {
                    "success": False,
                    "message": "❌ definition.type='sql_aggregate' requer definition.sql",
                    "error": "MISSING_SQL",
                }
            
            sql_query = sql_query.replace("{{period_start}}", period_start)
            sql_query = sql_query.replace("{{period_end}}", period_end)
            
            for key, val in params.items():
                sql_query = sql_query.replace(f"{{{{{key}}}}}", str(val))
            
            # Escolher conexão baseado no database_source
            if database_source == "sienge":
                conn_func = _get_sienge_postgres_conn
                meta["database_source"] = "sienge"
            else:
                conn_func = _get_postgres_conn
                meta["database_source"] = "railway"
            
            try:
                with conn_func() as conn:
                    with conn.cursor() as cur:
                        cur.execute(sql_query)
                        result = cur.fetchone()
                        if result:
                            # Se houver múltiplas colunas, usar a primeira como valor
                            value = float(result[0]) if result[0] is not None else 0.0
                            # Guardar outras colunas em meta
                            if len(result) > 1:
                                meta["additional_values"] = [float(r) if r is not None else 0.0 for r in result[1:]]
                        else:
                            value = 0.0
                        
                        meta["sql_executed"] = sql_query
                        meta["execution_time"] = datetime.now().isoformat()
            except Exception as e:
                return {
                    "success": False,
                    "message": f"❌ Erro ao executar SQL no banco {database_source}: {str(e)}",
                    "error": "SQL_EXECUTION_ERROR",
                    "database_source": database_source,
                    "details": str(e),
                }
        
        else:
            return {
                "success": False,
                "message": f"❌ Tipo de cálculo não suportado: {calc_type}",
                "error": "UNSUPPORTED_CALC_TYPE",
                "supported_types": ["sql_scalar", "sql_aggregate"],
            }
        
        # Salvar resultado
        meta_json = json.dumps(meta)
        params_json = json.dumps(params)
        
        with _get_postgres_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO kpi_values (
                        kpi_name, version, period_start, period_end, cadence,
                        params, params_hash, value, unit, meta
                    ) VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s::jsonb)
                    ON CONFLICT (kpi_name, version, cadence, period_start, period_end, params_hash)
                    DO UPDATE SET
                        value = EXCLUDED.value,
                        unit = EXCLUDED.unit,
                        meta = EXCLUDED.meta,
                        computed_at = now()
                    RETURNING id, computed_at
                """, (
                    kpi_name, kpi_def["version"], period_start_date, period_end_date,
                    kpi_def["cadence"], params_json, params_hash, value, unit, meta_json
                ))
                
                result = cur.fetchone()
                conn.commit()
                
                return {
                    "success": True,
                    "message": f"✅ KPI '{kpi_name}' calculado e salvo com sucesso",
                    "value": value,
                    "unit": unit,
                    "period": {
                        "start": period_start,
                        "end": period_end,
                    },
                    "computed_at": result[1].isoformat() if result[1] else None,
                    "meta": meta,
                }
    
    except Exception as e:
        log.error(f"Erro ao calcular KPI: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao calcular KPI: {str(e)}",
            "error": "CALCULATE_KPI_ERROR",
            "details": str(e),
        }


async def list_kpi_definitions(active_only: bool = False) -> Dict:
    """
    Lista todas as definições de KPI.
    
    Args:
        active_only: Se True, retorna apenas KPIs ativos
    
    Returns:
        Dict com success, message e lista de KPIs
    """
    if not PSYCOPG_AVAILABLE:
        return {
            "success": False,
            "message": "❌ psycopg não disponível. Instale: pip install psycopg[binary]",
            "error": "PSYCOPG_NOT_AVAILABLE",
        }
    
    try:
        _ensure_kpi_schema()
        
        with _get_postgres_conn() as conn:
            with conn.cursor() as cur:
                query = """
                    SELECT id, kpi_name, owner, description, cadence, lookback_days,
                           timezone, version, active, source_tables, created_at, updated_at
                    FROM kpi_definitions
                """
                
                if active_only:
                    query += " WHERE active = true"
                
                query += " ORDER BY kpi_name"
                
                cur.execute(query)
                rows = cur.fetchall()
                
                kpis = []
                for row in rows:
                    kpis.append({
                        "id": row[0],
                        "kpi_name": row[1],
                        "owner": row[2],
                        "description": row[3],
                        "cadence": row[4],
                        "lookback_days": row[5],
                        "timezone": row[6],
                        "version": row[7],
                        "active": row[8],
                        "source_tables": row[9],
                        "created_at": row[10].isoformat() if row[10] else None,
                        "updated_at": row[11].isoformat() if row[11] else None,
                    })
                
                return {
                    "success": True,
                    "message": f"✅ Encontrados {len(kpis)} KPIs",
                    "kpis": kpis,
                    "count": len(kpis),
                }
    
    except Exception as e:
        log.error(f"Erro ao listar KPIs: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao listar KPIs: {str(e)}",
            "error": "LIST_KPI_ERROR",
            "details": str(e),
        }


async def get_kpi_history(
    kpi_name: str,
    limit: int = 100,
    offset: int = 0,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict:
    """
    Obtém histórico de valores calculados de um KPI.
    
    Args:
        kpi_name: Nome do KPI
        limit: Limite de resultados (padrão: 100)
        offset: Deslocamento (padrão: 0)
        start_date: Data de início do filtro (YYYY-MM-DD)
        end_date: Data de fim do filtro (YYYY-MM-DD)
    
    Returns:
        Dict com success, message e lista de valores históricos
    """
    if not PSYCOPG_AVAILABLE:
        return {
            "success": False,
            "message": "❌ psycopg não disponível. Instale: pip install psycopg[binary]",
            "error": "PSYCOPG_NOT_AVAILABLE",
        }
    
    try:
        _ensure_kpi_schema()
        
        with _get_postgres_conn() as conn:
            with conn.cursor() as cur:
                query = """
                    SELECT id, kpi_name, version, period_start, period_end, cadence,
                           params, value, unit, computed_at, meta
                    FROM kpi_values
                    WHERE kpi_name = %s
                """
                params_list = [kpi_name]
                
                if start_date:
                    query += " AND period_start >= %s"
                    params_list.append(start_date)
                
                if end_date:
                    query += " AND period_end <= %s"
                    params_list.append(end_date)
                
                query += " ORDER BY period_start DESC, computed_at DESC LIMIT %s OFFSET %s"
                params_list.extend([limit, offset])
                
                cur.execute(query, params_list)
                rows = cur.fetchall()
                
                values = []
                for row in rows:
                    values.append({
                        "id": row[0],
                        "kpi_name": row[1],
                        "version": row[2],
                        "period_start": row[3].isoformat() if row[3] else None,
                        "period_end": row[4].isoformat() if row[4] else None,
                        "cadence": row[5],
                        "params": row[6],
                        "value": float(row[7]) if row[7] is not None else None,
                        "unit": row[8],
                        "computed_at": row[9].isoformat() if row[9] else None,
                        "meta": row[10],
                    })
                
                return {
                    "success": True,
                    "message": f"✅ Encontrados {len(values)} valores históricos para '{kpi_name}'",
                    "kpi_name": kpi_name,
                    "values": values,
                    "count": len(values),
                }
    
    except Exception as e:
        log.error(f"Erro ao buscar histórico de KPI: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao buscar histórico: {str(e)}",
            "error": "GET_KPI_HISTORY_ERROR",
            "details": str(e),
        }


async def recalculate_kpi(kpi_name: str, force: bool = True) -> Dict:
    """
    Recalcula um KPI usando os parâmetros da definição.
    Útil para cron jobs.
    
    Args:
        kpi_name: Nome do KPI a recalcular
        force: Se True, recalcula mesmo se já existir valor
    
    Returns:
        Dict com success e resultado do cálculo
    """
    return await calculate_kpi(kpi_name, force_recalculate=force)
