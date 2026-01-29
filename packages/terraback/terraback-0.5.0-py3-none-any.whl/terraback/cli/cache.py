import typer
from typing import Optional
from functools import wraps
import time
import hashlib
import json

app = typer.Typer(help="Manage terraback cache")


def cache_result(ttl: int = 300):
    """
    Decorator to cache function results with time-to-live (TTL).
    
    Args:
        ttl: Time to live in seconds (default: 300 seconds / 5 minutes)
    
    Returns:
        Decorated function with caching capability
    """
    def decorator(func):
        cache = {}
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create a cache key from function name and arguments
            cache_key = f"{func.__name__}:{hashlib.md5(str(args).encode() + str(kwargs).encode()).hexdigest()}"
            
            # Check if result is in cache and not expired
            if cache_key in cache:
                result, timestamp = cache[cache_key]
                if time.time() - timestamp < ttl:
                    return result
            
            # Call the function and cache the result
            result = func(*args, **kwargs)
            cache[cache_key] = (result, time.time())
            
            return result
        
        # Add method to clear cache for this function
        wrapper.clear_cache = lambda: cache.clear()
        
        return wrapper
    
    return decorator


@app.command("stats")
def cache_stats():
    """Show cache statistics."""
    from terraback.utils.scan_cache import get_scan_cache

    cache = get_scan_cache()
    stats = cache.get_stats()

    typer.echo("\nCache Statistics:")
    typer.echo(f"  Hit Rate: {stats['hit_rate']}")
    typer.echo(f"  Total Hits: {stats['hits']}")
    typer.echo(f"  Total Misses: {stats['misses']}")
    typer.echo(f"  Cache Size: {stats['total_size_kb']} KB")
    typer.echo(f"  Memory Cache Items: {stats['memory_cache_size']}")
    typer.echo(f"  TTL: {stats['ttl_minutes']:.0f} minutes")


@app.command("clear")
def cache_clear(
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation")
):
    """Clear all cached data."""
    from terraback.utils.scan_cache import get_scan_cache

    if not confirm:
        confirm = typer.confirm("Are you sure you want to clear all cached data?")

    if confirm:
        cache = get_scan_cache()
        cache.clear()
        typer.echo("Cache cleared successfully!")
    else:
        typer.echo("Cache clear cancelled.")


@app.command("invalidate")
def cache_invalidate(
    service: Optional[str] = typer.Option(None, help="Cloud service name (e.g., ec2, s3)"),
    operation: Optional[str] = typer.Option(None, help="Operation name (e.g., describe_instances)"),
):
    """Invalidate specific cache entries."""
    from terraback.utils.scan_cache import get_scan_cache

    cache = get_scan_cache()
    count = cache.invalidate_pattern(service, operation)

    if service and operation:
        typer.echo(f"Invalidated {count} cache entries for {service}:{operation}")
    elif service:
        typer.echo(f"Invalidated {count} cache entries for service: {service}")
    elif operation:
        typer.echo(f"Invalidated {count} cache entries for operation: {operation}")
    else:
        typer.echo(f"Invalidated {count} cache entries")
