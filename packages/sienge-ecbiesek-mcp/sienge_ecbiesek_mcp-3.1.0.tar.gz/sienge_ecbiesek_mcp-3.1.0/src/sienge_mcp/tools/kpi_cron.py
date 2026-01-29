#!/usr/bin/env python3
"""
KPI Cron Job - Recalcula KPIs automaticamente no Railway
Pode rodar como servidor contínuo (modo daemon) ou como script único

Modos de execução:
1. Servidor contínuo (padrão): Fica rodando e executa KPIs periodicamente
   python -m sienge_mcp.tools.kpi_cron
   
2. Execução única: Executa uma vez e encerra
   python -m sienge_mcp.tools.kpi_cron --once

3. Dry run: Apenas lista KPIs sem executar
   python -m sienge_mcp.tools.kpi_cron --dry-run

Configuração no Railway:
    1. Adicione um serviço PostgreSQL no Railway (se ainda não tiver)
    2. Configure variáveis de ambiente (RAILWAY_POSTGRES_URL, etc.)
    3. Configure o serviço para rodar este script como startCommand
    4. O script ficará rodando continuamente e executará KPIs automaticamente

Variáveis de Ambiente:
    - RAILWAY_POSTGRES_URL: Connection string do PostgreSQL do Railway (recomendado)
    - RAILWAY_DATABASE_URL: Alternativa
    - KPI_CRON_INTERVAL_HOURS: Intervalo entre execuções em horas (padrão: 6)
    - KPI_CRON_SCHEDULE: Schedule em formato cron (ex: "0 0 * * *" para diário às 00:00)
"""

import os
import sys
import asyncio
import logging
import signal
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional

# Adicionar o diretório raiz ao path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from sienge_mcp.tools import kpi_maker

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("kpi_cron")


async def recalculate_active_kpis(dry_run: bool = False) -> Dict:
    """
    Recalcula todos os KPIs ativos.
    
    Args:
        dry_run: Se True, apenas lista os KPIs que seriam recalculados sem executar
    
    Returns:
        Dict com estatísticas da execução
    """
    log.info("=" * 60)
    log.info("Iniciando recálculo de KPIs")
    log.info(f"Dry run: {dry_run}")
    log.info("=" * 60)
    
    stats = {
        "total": 0,
        "success": 0,
        "failed": 0,
        "errors": [],
        "results": [],
    }
    
    try:
        # Listar todos os KPIs ativos
        result = await kpi_maker.list_kpi_definitions(active_only=True)
        
        if not result.get("success"):
            log.error(f"Erro ao listar KPIs: {result.get('message')}")
            return {
                "success": False,
                "message": "Erro ao listar KPIs",
                "error": result.get("error"),
                **stats,
            }
        
        kpis = result.get("kpis", [])
        stats["total"] = len(kpis)
        
        log.info(f"Encontrados {len(kpis)} KPIs ativos para recalcular")
        
        if dry_run:
            log.info("\nKPIs que seriam recalculados:")
            for kpi in kpis:
                log.info(f"  - {kpi['kpi_name']} (owner: {kpi['owner']}, cadence: {kpi['cadence']})")
            return {
                "success": True,
                "message": f"Dry run: {len(kpis)} KPIs seriam recalculados",
                "dry_run": True,
                **stats,
            }
        
        # Recalcular cada KPI
        for kpi in kpis:
            kpi_name = kpi["kpi_name"]
            log.info(f"\nRecalculando KPI: {kpi_name}")
            log.info(f"  Owner: {kpi['owner']}")
            log.info(f"  Cadence: {kpi['cadence']}")
            log.info(f"  Lookback days: {kpi['lookback_days']}")
            
            try:
                result = await kpi_maker.recalculate_kpi(kpi_name, force=True)
                
                if result.get("success"):
                    stats["success"] += 1
                    value = result.get("value")
                    unit = result.get("unit", "")
                    period = result.get("period", {})
                    log.info(f"  ✅ Sucesso: {value} {unit}")
                    log.info(f"  Período: {period.get('start')} a {period.get('end')}")
                    
                    stats["results"].append({
                        "kpi_name": kpi_name,
                        "success": True,
                        "value": value,
                        "unit": unit,
                        "period": period,
                    })
                else:
                    stats["failed"] += 1
                    error_msg = result.get("message", "Erro desconhecido")
                    log.error(f"  ❌ Falha: {error_msg}")
                    
                    stats["errors"].append({
                        "kpi_name": kpi_name,
                        "error": error_msg,
                    })
                    
                    stats["results"].append({
                        "kpi_name": kpi_name,
                        "success": False,
                        "error": error_msg,
                    })
            
            except Exception as e:
                stats["failed"] += 1
                error_msg = str(e)
                log.error(f"  ❌ Exceção ao recalcular {kpi_name}: {error_msg}", exc_info=True)
                
                stats["errors"].append({
                    "kpi_name": kpi_name,
                    "error": error_msg,
                })
                
                stats["results"].append({
                    "kpi_name": kpi_name,
                    "success": False,
                    "error": error_msg,
                })
        
        log.info("\n" + "=" * 60)
        log.info("Resumo da execução:")
        log.info(f"  Total: {stats['total']}")
        log.info(f"  Sucesso: {stats['success']}")
        log.info(f"  Falhas: {stats['failed']}")
        log.info("=" * 60)
        
        return {
            "success": stats["failed"] == 0,
            "message": f"Recálculo concluído: {stats['success']}/{stats['total']} sucessos",
            **stats,
        }
    
    except Exception as e:
        log.error(f"Erro fatal no cron job: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"Erro fatal: {str(e)}",
            "error": "CRON_JOB_ERROR",
            **stats,
        }


async def recalculate_specific_kpi(kpi_name: str, force: bool = True) -> Dict:
    """
    Recalcula um KPI específico.
    Útil para testes ou recálculos manuais.
    
    Args:
        kpi_name: Nome do KPI a recalcular
        force: Se True, recalcula mesmo se já existir valor
    """
    log.info(f"Recalculando KPI específico: {kpi_name}")
    
    try:
        result = await kpi_maker.recalculate_kpi(kpi_name, force=force)
        
        if result.get("success"):
            value = result.get("value")
            unit = result.get("unit", "")
            period = result.get("period", {})
            log.info(f"✅ Sucesso: {value} {unit}")
            log.info(f"Período: {period.get('start')} a {period.get('end')}")
        else:
            log.error(f"❌ Falha: {result.get('message')}")
        
        return result
    
    except Exception as e:
        log.error(f"Erro ao recalcular KPI: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"Erro: {str(e)}",
            "error": "RECALCULATE_ERROR",
        }


def _parse_cron_schedule(schedule: str) -> Optional[timedelta]:
    """
    Converte schedule cron simples para timedelta.
    Suporta formatos:
    - "0 0 * * *" (diário às 00:00) -> 24 horas
    - "0 */6 * * *" (a cada 6 horas) -> 6 horas
    - "*/30 * * * *" (a cada 30 minutos) -> 30 minutos
    """
    try:
        parts = schedule.strip().split()
        if len(parts) != 5:
            return None
        
        # Se o minuto tem */N, usar N minutos
        minute_part = parts[0]
        if minute_part.startswith("*/"):
            minutes = int(minute_part[2:])
            return timedelta(minutes=minutes)
        
        # Se a hora tem */N, usar N horas
        hour_part = parts[1]
        if hour_part.startswith("*/"):
            hours = int(hour_part[2:])
            return timedelta(hours=hours)
        
        # Se é "0 0 * * *" (diário), retornar 24 horas
        if minute_part == "0" and hour_part == "0":
            return timedelta(hours=24)
        
        return None
    except Exception:
        return None


async def run_cron_server(interval_hours: float = 6.0, schedule: Optional[str] = None):
    """
    Roda o servidor de cron continuamente, executando KPIs periodicamente.
    
    Args:
        interval_hours: Intervalo entre execuções em horas (padrão: 6)
        schedule: Schedule em formato cron (ex: "0 0 * * *")
    """
    log.info("=" * 60)
    log.info("🚀 Iniciando KPI Cron Server (modo daemon)")
    log.info("=" * 60)
    
    # Determinar intervalo
    if schedule:
        interval = _parse_cron_schedule(schedule)
        if interval:
            log.info(f"📅 Schedule: {schedule} -> Intervalo: {interval}")
        else:
            log.warning(f"⚠️  Schedule '{schedule}' não reconhecido, usando interval_hours")
            interval = timedelta(hours=interval_hours)
    else:
        interval = timedelta(hours=interval_hours)
        log.info(f"⏰ Intervalo: {interval_hours} horas")
    
    # Executar imediatamente na primeira vez
    log.info("🔄 Executando primeira execução...")
    result = await recalculate_active_kpis(dry_run=False)
    if result.get("success"):
        log.info(f"✅ Primeira execução concluída: {result.get('message')}")
    else:
        log.error(f"❌ Primeira execução falhou: {result.get('message')}")
    
    # Loop principal
    log.info(f"⏳ Próxima execução em {interval}")
    log.info("=" * 60)
    
    while True:
        try:
            # Aguardar intervalo
            await asyncio.sleep(interval.total_seconds())
            
            # Executar recálculo
            log.info("")
            log.info("=" * 60)
            log.info(f"🔄 Executando recálculo de KPIs - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            log.info("=" * 60)
            
            result = await recalculate_active_kpis(dry_run=False)
            
            if result.get("success"):
                log.info(f"✅ Recálculo concluído: {result.get('message')}")
            else:
                log.error(f"❌ Recálculo falhou: {result.get('message')}")
            
            log.info(f"⏳ Próxima execução em {interval}")
            log.info("=" * 60)
        
        except asyncio.CancelledError:
            log.info("🛑 Servidor de cron interrompido")
            break
        except Exception as e:
            log.error(f"❌ Erro no servidor de cron: {e}", exc_info=True)
            log.info(f"⏳ Tentando novamente em {interval}")
            await asyncio.sleep(interval.total_seconds())


def main():
    """Entry point para o cron job"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Cron job para recalcular KPIs")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Executa uma vez e encerra (não roda como servidor)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Apenas lista os KPIs que seriam recalculados sem executar",
    )
    parser.add_argument(
        "--kpi",
        type=str,
        help="Recalcula apenas um KPI específico (por nome)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        default=True,
        help="Força recálculo mesmo se já existir valor (padrão: True)",
    )
    parser.add_argument(
        "--interval-hours",
        type=float,
        default=None,
        help="Intervalo entre execuções em horas (padrão: 6 ou KPI_CRON_INTERVAL_HOURS)",
    )
    parser.add_argument(
        "--schedule",
        type=str,
        default=None,
        help="Schedule em formato cron (ex: '0 0 * * *' para diário às 00:00)",
    )
    
    args = parser.parse_args()
    
    # Verificar variáveis de ambiente (prioridade para variáveis com prefixo RAILWAY_)
    railway_connection_string = (
        os.environ.get("RAILWAY_POSTGRES_URL") or 
        os.environ.get("RAILWAY_DATABASE_URL") or
        (os.environ.get("RAILWAY_PGHOST") and os.environ.get("RAILWAY_PGHOST", "").startswith("postgres"))
    )
    railway_individual_vars = all(os.environ.get(var) for var in [
        "RAILWAY_PGHOST", "RAILWAY_PGDATABASE", "RAILWAY_PGUSER", "RAILWAY_PGPASSWORD"
    ])
    
    # Fallback para variáveis sem prefixo
    fallback_connection_string = os.environ.get("POSTGRES_URL") or os.environ.get("DATABASE_URL")
    fallback_individual_vars = all(os.environ.get(var) for var in ["PGHOST", "PGDATABASE", "PGUSER", "PGPASSWORD"])
    
    has_railway_config = railway_connection_string or railway_individual_vars
    has_fallback_config = fallback_connection_string or fallback_individual_vars
    
    if not has_railway_config and not has_fallback_config:
        log.error("Variáveis de ambiente PostgreSQL do Railway não configuradas!")
        log.error("Configure uma das opções (recomendado usar prefixo RAILWAY_):")
        log.error("  - RAILWAY_POSTGRES_URL ou RAILWAY_DATABASE_URL (connection string)")
        log.error("  - Ou variáveis individuais: RAILWAY_PGHOST, RAILWAY_PGDATABASE, RAILWAY_PGUSER, RAILWAY_PGPASSWORD")
        log.error("  - Fallback: POSTGRES_URL ou DATABASE_URL (não recomendado se houver outros bancos)")
        sys.exit(1)
    
    if has_railway_config:
        if railway_connection_string:
            log.info("Usando connection string do Railway (RAILWAY_POSTGRES_URL ou RAILWAY_DATABASE_URL)")
        else:
            log.info("Usando variáveis individuais do Railway (RAILWAY_*)")
    elif has_fallback_config:
        log.warning("Usando variáveis de fallback (sem prefixo RAILWAY_). Considere migrar para RAILWAY_* para evitar conflitos.")
    
    # Configurar handler de sinais para graceful shutdown
    def signal_handler(signum, frame):
        log.info(f"\n🛑 Recebido sinal {signum}, encerrando...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Executar baseado nos argumentos
    if args.kpi:
        # Recalcular KPI específico
        result = asyncio.run(recalculate_specific_kpi(args.kpi, force=args.force))
        sys.exit(0 if result.get("success") else 1)
    elif args.once or args.dry_run:
        # Executar uma vez e encerrar
        result = asyncio.run(recalculate_active_kpis(dry_run=args.dry_run))
        sys.exit(0 if result.get("success") else 1)
    else:
        # Rodar como servidor contínuo
        interval_hours = args.interval_hours or float(os.environ.get("KPI_CRON_INTERVAL_HOURS", "6"))
        schedule = args.schedule or os.environ.get("KPI_CRON_SCHEDULE")
        
        try:
            asyncio.run(run_cron_server(interval_hours=interval_hours, schedule=schedule))
        except KeyboardInterrupt:
            log.info("\n🛑 Servidor interrompido pelo usuário")
            sys.exit(0)


if __name__ == "__main__":
    main()
