import click
from IPython import embed

from scheduler_service import create_app
from scheduler_service.config import Config

app = create_app(Config)
from scheduler_service.models import User


@click.group()
def cli():
    click.echo("START SCHEDULER SERVICE CLI")


@cli.command()
def shell():
    from scheduler_service import pg_db
    context = {
        "app": app,
        "User": User,
        "pg_db": pg_db
    }
    embed(user_ns=context,
          colors="neutral",
          using="asyncio",
          header="First: await app._database.connect()")


@cli.command()
@click.option("--host", default="localhost")
@click.option("--port", default=8080)
def runserver(host, port):
    app.run(debug=True, host=host, port=port)


@cli.command()
@click.option('--check',
              is_flag=True,
              help='Health Check: run a health check and exit.')
@click.option('-v', '--verbose', is_flag=True, help='Enable verbose output.')
def arq(check, verbose):
    import logging

    from arq.logs import default_log_config
    from arq.worker import check_health, run_worker

    from scheduler_service.service import WorkerSettings
    logging.config.dictConfig(default_log_config(verbose))

    if check:
        exit(check_health(WorkerSettings))
    else:
        kwargs = {}
        run_worker(WorkerSettings, **kwargs)
