"""
Command-line interface for RentCache administration.
"""
import asyncio
import hashlib
import sys
from datetime import datetime, timezone
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich import print as rprint
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, func, and_

from .models import Base, APIKey, CacheEntry, UsageStats
from .server import app, run as run_server

console = Console()

# Database setup
DATABASE_URL = "sqlite+aiosqlite:///./rentcache.db"


async def get_db_session() -> AsyncSession:
    """Get database session for CLI operations."""
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with SessionLocal() as session:
        yield session
        await session.close()
    await engine.dispose()


@click.group()
def cli():
    """RentCache CLI - Administration tool for RentCache API proxy."""
    pass


@cli.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=8000, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
@click.option("--log-level", default="info", help="Log level")
def server(host: str, port: int, reload: bool, log_level: str):
    """Start the RentCache server."""
    import uvicorn
    
    rprint(f"🚀 Starting RentCache server on {host}:{port}")
    rprint(f"📚 API docs will be available at: http://{host}:{port}/docs")
    
    uvicorn.run(
        "rentcache.server:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level
    )


@cli.command()
@click.argument("key_name")
@click.argument("rentcast_api_key")
@click.option("--daily-limit", default=1000, help="Daily API call limit")
@click.option("--monthly-limit", default=10000, help="Monthly API call limit")
@click.option("--expires", help="Expiration date (YYYY-MM-DD)")
def create_key(key_name: str, rentcast_api_key: str, daily_limit: int, monthly_limit: int, expires: Optional[str]):
    """Create a new API key."""
    async def _create_key():
        async for db in get_db_session():
            try:
                # Check if key name already exists
                existing_stmt = select(APIKey).where(APIKey.key_name == key_name)
                result = await db.execute(existing_stmt)
                if result.scalar_one_or_none():
                    rprint(f"❌ API key with name '{key_name}' already exists")
                    return
                
                # Parse expiration date
                expires_at = None
                if expires:
                    try:
                        expires_at = datetime.strptime(expires, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    except ValueError:
                        rprint("❌ Invalid date format. Use YYYY-MM-DD")
                        return
                
                # Hash the API key
                key_hash = hashlib.sha256(rentcast_api_key.encode()).hexdigest()
                
                # Create new API key
                new_key = APIKey(
                    key_name=key_name,
                    key_hash=key_hash,
                    daily_limit=daily_limit,
                    monthly_limit=monthly_limit,
                    expires_at=expires_at,
                    last_daily_reset=datetime.now(timezone.utc),
                    last_monthly_reset=datetime.now(timezone.utc)
                )
                
                db.add(new_key)
                await db.commit()
                
                rprint(f"✅ Created API key: {key_name}")
                rprint(f"   Daily limit: {daily_limit}")
                rprint(f"   Monthly limit: {monthly_limit}")
                if expires_at:
                    rprint(f"   Expires: {expires_at.strftime('%Y-%m-%d')}")
                
                rprint(f"\n🔑 Use this bearer token in your requests:")
                rprint(f"   Authorization: Bearer {rentcast_api_key}")
                
            except Exception as e:
                rprint(f"❌ Error creating API key: {e}")
                await db.rollback()
    
    asyncio.run(_create_key())


@cli.command()
def list_keys():
    """List all API keys."""
    async def _list_keys():
        async for db in get_db_session():
            try:
                stmt = select(APIKey).order_by(APIKey.created_at.desc())
                result = await db.execute(stmt)
                keys = result.scalars().all()
                
                if not keys:
                    rprint("📭 No API keys found")
                    return
                
                table = Table(title="API Keys")
                table.add_column("Name", style="cyan")
                table.add_column("Status", style="green")
                table.add_column("Daily Usage", style="yellow")
                table.add_column("Monthly Usage", style="yellow") 
                table.add_column("Created", style="blue")
                table.add_column("Expires", style="red")
                
                for key in keys:
                    status = "🟢 Active" if key.is_active else "🔴 Inactive"
                    daily_usage = f"{key.daily_usage}/{key.daily_limit}"
                    monthly_usage = f"{key.monthly_usage}/{key.monthly_limit}"
                    created = key.created_at.strftime("%Y-%m-%d")
                    expires = key.expires_at.strftime("%Y-%m-%d") if key.expires_at else "Never"
                    
                    table.add_row(
                        key.key_name,
                        status,
                        daily_usage,
                        monthly_usage,
                        created,
                        expires
                    )
                
                console.print(table)
                
            except Exception as e:
                rprint(f"❌ Error listing API keys: {e}")
    
    asyncio.run(_list_keys())


@cli.command()
@click.argument("key_name")
@click.option("--daily-limit", help="New daily limit")
@click.option("--monthly-limit", help="New monthly limit") 
@click.option("--active/--inactive", default=None, help="Enable/disable key")
def update_key(key_name: str, daily_limit: Optional[int], monthly_limit: Optional[int], active: Optional[bool]):
    """Update an API key."""
    async def _update_key():
        async for db in get_db_session():
            try:
                stmt = select(APIKey).where(APIKey.key_name == key_name)
                result = await db.execute(stmt)
                api_key = result.scalar_one_or_none()
                
                if not api_key:
                    rprint(f"❌ API key '{key_name}' not found")
                    return
                
                # Update fields
                updated = []
                if daily_limit is not None:
                    api_key.daily_limit = daily_limit
                    updated.append(f"daily limit: {daily_limit}")
                
                if monthly_limit is not None:
                    api_key.monthly_limit = monthly_limit
                    updated.append(f"monthly limit: {monthly_limit}")
                
                if active is not None:
                    api_key.is_active = active
                    updated.append(f"status: {'active' if active else 'inactive'}")
                
                if not updated:
                    rprint("❌ No updates specified")
                    return
                
                await db.commit()
                
                rprint(f"✅ Updated API key '{key_name}':")
                for update in updated:
                    rprint(f"   - {update}")
                
            except Exception as e:
                rprint(f"❌ Error updating API key: {e}")
                await db.rollback()
    
    asyncio.run(_update_key())


@cli.command()
@click.argument("key_name")
@click.confirmation_option(prompt="Are you sure you want to delete this API key?")
def delete_key(key_name: str):
    """Delete an API key."""
    async def _delete_key():
        async for db in get_db_session():
            try:
                stmt = select(APIKey).where(APIKey.key_name == key_name)
                result = await db.execute(stmt)
                api_key = result.scalar_one_or_none()
                
                if not api_key:
                    rprint(f"❌ API key '{key_name}' not found")
                    return
                
                await db.delete(api_key)
                await db.commit()
                
                rprint(f"✅ Deleted API key: {key_name}")
                
            except Exception as e:
                rprint(f"❌ Error deleting API key: {e}")
                await db.rollback()
    
    asyncio.run(_delete_key())


@cli.command()
@click.option("--endpoint", help="Show stats for specific endpoint")
@click.option("--days", default=7, help="Number of days to analyze")
def stats(endpoint: Optional[str], days: int):
    """Show usage statistics."""
    async def _show_stats():
        async for db in get_db_session():
            try:
                # Total requests
                total_stmt = select(func.count(UsageStats.id))
                if endpoint:
                    total_stmt = total_stmt.where(UsageStats.endpoint == endpoint)
                
                total_result = await db.execute(total_stmt)
                total_requests = total_result.scalar()
                
                # Cache hits
                hits_stmt = select(func.count(UsageStats.id)).where(UsageStats.cache_hit == True)
                if endpoint:
                    hits_stmt = hits_stmt.where(UsageStats.endpoint == endpoint)
                
                hits_result = await db.execute(hits_stmt)
                cache_hits = hits_result.scalar()
                
                cache_misses = total_requests - cache_hits
                hit_ratio = cache_hits / total_requests if total_requests > 0 else 0
                
                # Average response time
                avg_time_stmt = select(func.avg(UsageStats.response_time_ms))
                if endpoint:
                    avg_time_stmt = avg_time_stmt.where(UsageStats.endpoint == endpoint)
                
                avg_time_result = await db.execute(avg_time_stmt)
                avg_response_time = avg_time_result.scalar() or 0
                
                # Total estimated cost
                cost_stmt = select(func.sum(UsageStats.estimated_cost)).where(UsageStats.cache_hit == False)
                if endpoint:
                    cost_stmt = cost_stmt.where(UsageStats.endpoint == endpoint)
                
                cost_result = await db.execute(cost_stmt)
                total_cost = cost_result.scalar() or 0
                
                # Cache entries count
                cache_count_stmt = select(func.count(CacheEntry.id)).where(CacheEntry.is_valid == True)
                if endpoint:
                    cache_count_stmt = cache_count_stmt.where(CacheEntry.endpoint == endpoint)
                
                cache_count_result = await db.execute(cache_count_stmt)
                cache_entries = cache_count_result.scalar()
                
                # Display stats
                title = f"Usage Statistics" + (f" - {endpoint}" if endpoint else "")
                table = Table(title=title)
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="green")
                
                table.add_row("Total Requests", str(total_requests))
                table.add_row("Cache Hits", str(cache_hits))
                table.add_row("Cache Misses", str(cache_misses))
                table.add_row("Hit Ratio", f"{hit_ratio:.2%}")
                table.add_row("Avg Response Time", f"{avg_response_time:.1f}ms")
                table.add_row("Total Cost", f"${total_cost:.2f}")
                table.add_row("Cache Entries", str(cache_entries))
                
                console.print(table)
                
                # Top endpoints (if not filtering by specific endpoint)
                if not endpoint:
                    rprint("\n📊 Top Endpoints:")
                    top_endpoints_stmt = select(
                        UsageStats.endpoint,
                        func.count(UsageStats.id).label('count')
                    ).group_by(UsageStats.endpoint).order_by(func.count(UsageStats.id).desc()).limit(5)
                    
                    top_result = await db.execute(top_endpoints_stmt)
                    
                    endpoint_table = Table()
                    endpoint_table.add_column("Endpoint", style="cyan")
                    endpoint_table.add_column("Requests", style="yellow")
                    
                    for row in top_result:
                        endpoint_table.add_row(row.endpoint, str(row.count))
                    
                    console.print(endpoint_table)
                
            except Exception as e:
                rprint(f"❌ Error getting stats: {e}")
    
    asyncio.run(_show_stats())


@cli.command()
@click.option("--endpoint", help="Clear cache for specific endpoint")
@click.option("--older-than", type=int, help="Clear entries older than N hours")
@click.confirmation_option(prompt="Are you sure you want to clear cache entries?")
def clear_cache(endpoint: Optional[str], older_than: Optional[int]):
    """Clear cache entries."""
    async def _clear_cache():
        async for db in get_db_session():
            try:
                from sqlalchemy import update
                
                conditions = [CacheEntry.is_valid == True]
                
                if endpoint:
                    conditions.append(CacheEntry.endpoint == endpoint)
                
                if older_than:
                    from datetime import timedelta
                    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=older_than)
                    conditions.append(CacheEntry.created_at < cutoff_time)
                
                # Mark entries as invalid (soft delete)
                stmt = update(CacheEntry).where(and_(*conditions)).values(is_valid=False)
                result = await db.execute(stmt)
                await db.commit()
                
                cleared_count = result.rowcount
                rprint(f"✅ Marked {cleared_count} cache entries as invalid")
                
                if endpoint:
                    rprint(f"   Endpoint: {endpoint}")
                if older_than:
                    rprint(f"   Older than: {older_than} hours")
                
            except Exception as e:
                rprint(f"❌ Error clearing cache: {e}")
                await db.rollback()
    
    asyncio.run(_clear_cache())


@cli.command()
def health():
    """Check system health."""
    async def _health_check():
        async for db in get_db_session():
            try:
                # Test database connection
                await db.execute(select(1))
                rprint("✅ Database: Connected")
                
                # Count active keys
                active_keys_stmt = select(func.count(APIKey.id)).where(APIKey.is_active == True)
                active_result = await db.execute(active_keys_stmt)
                active_keys = active_result.scalar()
                rprint(f"🔑 Active API Keys: {active_keys}")
                
                # Count cache entries
                cache_stmt = select(func.count(CacheEntry.id)).where(CacheEntry.is_valid == True)
                cache_result = await db.execute(cache_stmt)
                cache_entries = cache_result.scalar()
                rprint(f"💾 Valid Cache Entries: {cache_entries}")
                
                # Recent requests (last 24h)
                from datetime import timedelta
                recent_time = datetime.now(timezone.utc) - timedelta(hours=24)
                recent_stmt = select(func.count(UsageStats.id)).where(UsageStats.created_at >= recent_time)
                recent_result = await db.execute(recent_stmt)
                recent_requests = recent_result.scalar()
                rprint(f"📈 Requests (24h): {recent_requests}")
                
                rprint("\n🎉 System is healthy!")
                
            except Exception as e:
                rprint(f"❌ Health check failed: {e}")
                sys.exit(1)
    
    asyncio.run(_health_check())


def main():
    """Main CLI entry point."""
    cli()


if __name__ == "__main__":
    main()