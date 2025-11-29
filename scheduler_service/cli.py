import logging
import sys
import asyncio

import click
from aerich import Command
from tortoise import Tortoise

from scheduler_service import close_tortoise, setup_tortoise
from scheduler_service.main import create_app
from scheduler_service.config import Config, TORTOISE_ORM
from scheduler_service.models import User


@click.group()
def scheduler():
    """Scheduler Service CLI"""
    click.echo("Scheduler Service CLI")


@scheduler.command()
def shell():
    """Start interactive shell"""
    from IPython import embed
    app = create_app()
    context = {
        "app": app,
        "User": User
    }
    embed(user_ns=context,
          colors="neutral",
          using="asyncio",
          header="First: await app._database.connect()")


@scheduler.command()
@click.option('-h', "--host", default="localhost")
@click.option('-p', "--port", default=8080, type=int)
@click.option('-w', "--workers", default=1, type=int)
@click.option('--debug/--no-debug', default=True)
@click.option('--access-log/--no-access-log', default=True)
def runserver(host, port, workers, debug, access_log):
    """Start Web server (for development)"""
    import uvicorn

    # Use string import path to support hot reload
    # create_app function will automatically call Config.to_dict() to get config
    uvicorn.run(
        "scheduler_service.main:create_app",
        host=host,
        port=port,
        reload=debug,  # Enable hot reload in development mode
        access_log=access_log,
        factory=True  # Tell uvicorn this is an app factory function
    )


@scheduler.command()
@click.option('-v', '--verbose', is_flag=True, help='Enable verbose output')
@click.option('-p', '--processes', default=1, type=int, help='Number of worker processes')
def worker(verbose, processes):
    """Start dramatiq worker"""
    # Configure logging
    if verbose:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)

    # Ensure app is initialized (load config and register tasks)
    _ = create_app()

    # Run dramatiq worker
    from dramatiq.cli import main

    # Save original argv to avoid modifying global state
    original_argv = sys.argv.copy()
    try:
        sys.argv = [sys.argv[0], 'scheduler_service.service',
                    '--processes', str(processes)]
        main()
    except KeyboardInterrupt:
        print("Worker stopped")
    finally:
        sys.argv = original_argv


@scheduler.command()
def init_db():
    """Initialize database (using Aerich)"""
    async def run():
        try:
            command = Command(tortoise_config=TORTOISE_ORM,
                              location="./migrations")
            await command.init()
            await command.init_db(safe=True)
            click.echo("Database initialized (Aerich)")
        except FileExistsError:
            # If migrations folder exists, init() will error, but this is usually fine, continue to try init-db
            # However, Aerich's init() internally might just print info or error depending on version if folder exists.
            # Here we assume init() failure might be because it's already initialized, try init-db directly
            pass
        except Exception as e:
            click.echo(f"Error during initialization: {e}")
            click.echo(
                "Try running 'scheduler migrate init-db' for details or use different options.")

    asyncio.run(run())


@scheduler.group()
def migrate():
    """Database migration tool (Aerich)"""
    pass


@migrate.command()
def init():
    """Initialize Aerich config and directory"""
    async def run():
        command = Command(tortoise_config=TORTOISE_ORM,
                          location="./migrations")
        await command.init()
        click.echo("Aerich initialized")
    asyncio.run(run())


@migrate.command()
@click.option("--safe", is_flag=True, default=True, help="Safe mode")
def init_db(safe):
    """Initialize database (create tables)"""
    async def run():
        command = Command(tortoise_config=TORTOISE_ORM,
                          location="./migrations")
        await command.init()
        await command.init_db(safe=safe)
        click.echo("Database initialized")
    asyncio.run(run())


@migrate.command()
@click.option("--name", default="update", help="Migration name")
def create(name):
    """Create new migration file"""
    async def run():
        command = Command(tortoise_config=TORTOISE_ORM,
                          location="./migrations")
        await command.init()
        await command.migrate(name)
        click.echo(f"Migration '{name}' created")
    asyncio.run(run())


@migrate.command()
def upgrade():
    """Apply migrations"""
    async def run():
        command = Command(tortoise_config=TORTOISE_ORM,
                          location="./migrations")
        await command.init()
        await command.upgrade()
        click.echo("Database upgraded")
    asyncio.run(run())


@migrate.command()
def downgrade():
    """Revert migrations"""
    async def run():
        command = Command(tortoise_config=TORTOISE_ORM,
                          location="./migrations")
        await command.init()
        await command.downgrade(delete=False, version=-1)
        click.echo("Database downgraded")
    asyncio.run(run())


@migrate.command()
def history():
    """View migration history"""
    async def run():
        command = Command(tortoise_config=TORTOISE_ORM,
                          location="./migrations")
        await command.init()
        versions = await command.history()
        for version in versions:
            click.echo(version)
    asyncio.run(run())


@migrate.command()
def heads():
    """View current migration heads"""
    async def run():
        command = Command(tortoise_config=TORTOISE_ORM,
                          location="./migrations")
        await command.init()
        heads = await command.heads()
        for head in heads:
            click.echo(head)
    asyncio.run(run())


@scheduler.command()
def create_admin():
    """Create default admin user from config"""
    async def run():
        await setup_tortoise(Config.to_dict())  # Pass the Config object
        try:
            username = Config.DEFAULT_ADMIN_NAME
            email = Config.DEFAULT_ADMIN_EMAIL
            password = Config.DEFAULT_ADMIN_PASSWORD

            user = await User.get_or_none(name=username)
            if not user:
                password_hash = User.hash_password(password)
                await User.create(
                    name=username,
                    password_hash=password_hash,
                    email=email
                )
                click.echo(f"Admin user '{username}' created successfully.")
            else:
                click.echo(f"User '{username}' already exists.")
        except Exception as e:
            click.echo(f"Error creating admin user: {e}")
        finally:
            await close_tortoise()  # Close Tortoise connections

    asyncio.run(run())


@scheduler.command()
@click.option('--path', '-p', help='Path to test, default is tests/')
@click.option('--coverage', '-c', is_flag=True, help='Generate coverage report')
@click.option('--verbose', '-v', is_flag=True, help='Show verbose output')
@click.option('--parallel', '-n', type=int, help='Number of parallel processes')
@click.option(
    "--coverage-threshold", "-t",
    type=int,
    default=80,
    help="Coverage threshold, default is 80%%"
)
def test(path, coverage, verbose, parallel, coverage_threshold):
    """Start coverage test"""
    import subprocess

    # Build pytest command
    cmd = [sys.executable, "-m", "pytest"]

    # Add test path
    if path:
        cmd.append(path)
    else:
        cmd.append("tests/")

    # Add coverage options
    if coverage:
        cmd.extend([
            "--cov=scheduler_service",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "--cov-report=xml"
        ])

        # Add coverage threshold
        if coverage_threshold:
            cmd.append(f"--cov-fail-under={coverage_threshold}")

    # Add verbose output
    if verbose:
        cmd.append("-v")

    # Add parallel execution
    if parallel:
        cmd.append(f"-n={parallel}")

    click.echo(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd)

    # If HTML coverage report is generated, show path
    if coverage and result.returncode == 0:
        click.echo("\nHTML coverage report generated in htmlcov/index.html")

    sys.exit(result.returncode)


if __name__ == '__main__':
    scheduler()
