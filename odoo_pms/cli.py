#!/usr/bin/env python3
from configparser import ConfigParser
from pathlib import Path

import odoorpc
from rich.table import Table
from rich.console import Console

from rich.progress import Progress
from .reservation import Reservation
import click
import os


class Ctx(object):
    def __init__(self, config_file):
        self.config_file = config_file

        cfg = ConfigParser(
            default_section="options",
            defaults={
                "odoo_host": "127.0.0.1",
                "odoo_port": 8069,
                "odoo_user": "admin",
                "odoo_password": "admin",
                "odoo_protocol": "jsonrpc"
            }
        )
        cfg.read(self.config_file)

        self.odoo_host = cfg.get("options", "odoo_host")
        self.odoo_user = cfg.get("options", "odoo_user")
        self.odoo_password = cfg.get("options", "odoo_password")
        self.odoo_port = cfg.get("options", "odoo_port")
        self.odoo_protocol = cfg.get("options", "odoo_protocol")

        self.odoo = odoorpc.ODOO(
            host=self.odoo_host,
            protocol=self.odoo_protocol,
            port=self.odoo_port
        )

        db_list = self.odoo.db.list()
        if len(db_list) > 0:
            self.odoo.login(
                db=db_list[0],
                login=self.odoo_user,
                password=self.odoo_password
            )


class CustomCommandClass(click.Command):
    def invoke(self, ctx):
        config_file = ctx.obj.config_file
        if not config_file:
            config_file = os.getenv("ODOO_CONFIG_FILE") or "{}/.odoo-config".format(Path.home())

        cfg = ConfigParser()
        if not os.path.exists(config_file):
            cfg.add_section("options")
            with open(config_file, "w") as file_config_writer:
                cfg.write(file_config_writer)

        cfg.read(config_file)
        try:
            options = dict(cfg["options"])
        except KeyError:
            options = {}

        for k in options.keys():
            try:
                ctx.params[k] = cfg.getint("options", k)
            except Exception as ex:
                ctx.params["error"] = ex
                ctx.params[k] = cfg.get("options", k)
        return super().invoke(ctx)


@click.group()
@click.option("-c", "--config_file", type=click.Path())
@click.pass_context
def main(ctx, config_file):
    if not config_file:
        config_file = os.getenv("ODOO_CONFIG_FILE") or "{}/.odoo-config".format(Path.home())
    ctx.obj = Ctx(config_file)


@main.group()
def reservations():
    pass


@reservations.command(cls=CustomCommandClass)
@click.option('--limit', type=click.INT, default=10)
@click.option('--order', type=click.STRING, default="create_date desc")
@click.option('--states', type=click.STRING)
@click.option('--no-public', is_flag=True)
@click.pass_context
def get_list(ctx, limit, order, states, no_public, **kw):
    """
    Gets a list of reservations
    """
    if states:
        states = str(states).split(",")

    console = Console()
    reservation = Reservation(ctx.obj)
    reservations_ids = reservation.get_reservations(
        limit=limit,
        states=states,
        order=order,
        no_public=no_public
    )
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("OTAs / External ID", style="dim", width=24)
    table.add_column("Unit")
    table.add_column("State")
    table.add_column("User")
    table.add_column("Order")
    table.add_column("Create Date")

    with Progress() as progress:
        task = progress.add_task("Loading reservation", total=limit)
        for job in reservations_ids:
            progress.advance(task)
            table.add_row(
                job["guesty_id"] or str(),
                job["property_id"][1][0:25],
                job["stage_id"][1],
                job["user_id"][1],
                "{1}".format(*job["sale_order_id"] if job["sale_order_id"] else (0, "------")),
                job["create_date"]
            )

    console.print(table)


@reservations.command()
@click.pass_context
def get_available_stages(ctx):
    console = Console()
    reservation = Reservation(ctx.obj)
    reservations_ids = reservation.get_stages()
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Stage Name", style="dim", width=24)

    with Progress() as progress:
        task = progress.add_task("Loading reservation", total=len(reservations_ids))
        for job in reservations_ids:
            progress.advance(task)
            table.add_row(
                job["name"]
            )

    console.print(table)


if __name__ == '__main__':
    main()
