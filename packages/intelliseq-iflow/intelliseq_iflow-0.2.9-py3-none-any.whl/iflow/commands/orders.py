"""Order commands for iFlow CLI."""

import asyncio

import click

from iflow.api import APIError, MinerAPIClient
from iflow.config import require_project
from iflow.curl import miner_curl


@click.group()
def orders():
    """Manage clinical orders."""
    pass


@orders.command("list")
@click.option("-p", "--project", help="Project ID (uses default if not specified)")
@click.option("--status", help="Filter by status (created, analyzing, ready_for_review, etc.)")
@click.option("--priority", help="Filter by priority (routine, urgent, stat)")
@click.option("--limit", default=20, help="Maximum orders to display")
@click.option("--curl", is_flag=True, help="Output curl command instead of executing")
def list_orders(
    project: str | None, status: str | None, priority: str | None, limit: int, curl: bool
):
    """List orders for a project.

    \b
    Examples:
      iflow orders list
      iflow orders list --status created
      iflow orders list --priority urgent
    """
    project_id = require_project(project)

    if curl:
        params = {"limit": str(limit)}
        if status:
            params["status"] = status
        if priority:
            params["priority"] = priority
        print(miner_curl("GET", "/orders", project_id, params=params))
        return

    async def _list():
        client = MinerAPIClient()
        try:
            orders_list = await client.list_orders(
                project_id=project_id,
                status=status,
                priority=priority,
                limit=limit,
            )

            if not orders_list:
                click.echo("No orders found.")
                return

            # Print header
            click.echo(f"{'ID':<40} {'NAME':<30} {'STATUS':<18} {'PRIORITY':<10}")
            click.echo("-" * 100)

            for o in orders_list:
                click.echo(f"{o.id:<40} {o.name:<30} {o.status:<18} {o.priority:<10}")

        except APIError as e:
            click.echo(f"Error: {e}", err=True)
            raise SystemExit(1)

    asyncio.run(_list())


@orders.command("create")
@click.option("-p", "--project", help="Project ID (uses default if not specified)")
@click.option("-n", "--name", required=True, help="Order name")
@click.option("--accession", help="Lab accession number")
@click.option("--external-id", help="External system reference")
@click.option("--description", help="Order description")
@click.option(
    "--priority",
    type=click.Choice(["routine", "urgent", "stat"]),
    default="routine",
    help="Priority level",
)
@click.option("--indication", help="Clinical indication / reason for testing")
@click.option("--test-type", help="Type of genetic test")
@click.option("--provider", help="Ordering provider name")
@click.option("--facility", help="Ordering facility name")
@click.option("--tag", "-t", multiple=True, help="Tag for the order")
@click.option("--curl", is_flag=True, help="Output curl command instead of executing")
def create_order(
    project: str | None,
    name: str,
    accession: str | None,
    external_id: str | None,
    description: str | None,
    priority: str,
    indication: str | None,
    test_type: str | None,
    provider: str | None,
    facility: str | None,
    tag: tuple[str, ...],
    curl: bool,
):
    """Create a new order.

    \b
    Examples:
      iflow orders create -n "Patient Smith Case"
      iflow orders create -n "Urgent Case" --priority urgent \\
        --accession ACC-001 --indication "Family history of cancer"
    """
    project_id = require_project(project)

    data = {"name": name, "priority": priority}
    if accession:
        data["accession_number"] = accession
    if external_id:
        data["external_id"] = external_id
    if description:
        data["description"] = description
    if indication:
        data["indication"] = indication
    if test_type:
        data["test_type"] = test_type
    if provider:
        data["ordering_provider"] = provider
    if facility:
        data["ordering_facility"] = facility
    if tag:
        data["tags"] = list(tag)

    if curl:
        print(miner_curl("POST", "/orders", project_id, data=data))
        return

    async def _create():
        client = MinerAPIClient()
        try:
            order = await client.create_order(
                project_id=project_id,
                name=name,
                accession_number=accession,
                external_id=external_id,
                description=description,
                priority=priority,
                indication=indication,
                test_type=test_type,
                ordering_provider=provider,
                ordering_facility=facility,
                tags=list(tag) if tag else None,
            )

            click.echo("Order created successfully!")
            click.echo(f"  ID: {order.id}")
            click.echo(f"  Name: {order.name}")
            click.echo(f"  Status: {order.status}")
            click.echo(f"  Priority: {order.priority}")
            if order.accession_number:
                click.echo(f"  Accession: {order.accession_number}")

        except APIError as e:
            click.echo(f"Error: {e}", err=True)
            raise SystemExit(1)

    asyncio.run(_create())


@orders.command("get")
@click.option("-p", "--project", help="Project ID (uses default if not specified)")
@click.argument("order_id")
@click.option("--curl", is_flag=True, help="Output curl command instead of executing")
def get_order(project: str | None, order_id: str, curl: bool):
    """Get details of an order.

    ORDER_ID is the order identifier.
    """
    project_id = require_project(project)

    if curl:
        print(miner_curl("GET", f"/orders/{order_id}", project_id))
        return

    async def _get():
        client = MinerAPIClient()
        try:
            order = await client.get_order(project_id, order_id)

            click.echo(f"Order: {order.name}")
            click.echo(f"  ID: {order.id}")
            click.echo(f"  Status: {order.status}")
            click.echo(f"  Priority: {order.priority}")

            if order.accession_number:
                click.echo(f"  Accession: {order.accession_number}")
            if order.external_id:
                click.echo(f"  External ID: {order.external_id}")
            if order.description:
                click.echo(f"  Description: {order.description}")
            if order.indication:
                click.echo(f"  Indication: {order.indication}")
            if order.test_type:
                click.echo(f"  Test Type: {order.test_type}")
            if order.ordering_provider:
                click.echo(f"  Provider: {order.ordering_provider}")
            if order.ordering_facility:
                click.echo(f"  Facility: {order.ordering_facility}")

            if order.created_at:
                click.echo(f"  Created: {order.created_at}")
            if order.updated_at:
                click.echo(f"  Updated: {order.updated_at}")

            if order.tags:
                click.echo(f"  Tags: {', '.join(order.tags)}")

        except APIError as e:
            click.echo(f"Error: {e}", err=True)
            raise SystemExit(1)

    asyncio.run(_get())


@orders.command("transition")
@click.option("-p", "--project", help="Project ID (uses default if not specified)")
@click.argument("order_id")
@click.argument(
    "status",
    type=click.Choice([
        "created",
        "analyzing",
        "ready_for_review",
        "reviewed",
        "signed_off",
        "completed",
        "amended",
        "cancelled",
    ]),
)
@click.option("--curl", is_flag=True, help="Output curl command instead of executing")
def transition_order(project: str | None, order_id: str, status: str, curl: bool):
    """Transition order to a new status.

    \b
    ORDER_ID is the order identifier.
    STATUS is the target status.

    \b
    Status flow:
      created -> analyzing -> ready_for_review -> reviewed -> signed_off -> completed
                                                                              -> amended

    \b
    Examples:
      iflow orders transition ORDER_ID analyzing
      iflow orders transition ORDER_ID ready_for_review
    """
    project_id = require_project(project)

    if curl:
        data = {"status": status}
        print(miner_curl("POST", f"/orders/{order_id}/transition", project_id, data=data))
        return

    async def _transition():
        client = MinerAPIClient()
        try:
            order = await client.transition_order(project_id, order_id, status)

            click.echo("Order transitioned successfully!")
            click.echo(f"  ID: {order.id}")
            click.echo(f"  Name: {order.name}")
            click.echo(f"  Status: {order.status}")

        except APIError as e:
            click.echo(f"Error: {e}", err=True)
            raise SystemExit(1)

    asyncio.run(_transition())


@orders.command("delete")
@click.option("-p", "--project", help="Project ID (uses default if not specified)")
@click.argument("order_id")
@click.option("--curl", is_flag=True, help="Output curl command instead of executing")
@click.confirmation_option(prompt="Are you sure you want to delete this order?")
def delete_order(project: str | None, order_id: str, curl: bool):
    """Delete an order.

    ORDER_ID is the order identifier.
    """
    project_id = require_project(project)

    if curl:
        print(miner_curl("DELETE", f"/orders/{order_id}", project_id))
        return

    async def _delete():
        client = MinerAPIClient()
        try:
            await client.delete_order(project_id, order_id)
            click.echo(f"Order {order_id} deleted.")

        except APIError as e:
            click.echo(f"Error: {e}", err=True)
            raise SystemExit(1)

    asyncio.run(_delete())


@orders.command("samples")
@click.option("-p", "--project", help="Project ID (uses default if not specified)")
@click.argument("order_id")
@click.option("--curl", is_flag=True, help="Output curl command instead of executing")
def list_order_samples(project: str | None, order_id: str, curl: bool):
    """List samples in an order.

    ORDER_ID is the order identifier.
    """
    project_id = require_project(project)

    if curl:
        print(miner_curl("GET", f"/orders/{order_id}/samples", project_id))
        return

    async def _samples():
        client = MinerAPIClient()
        try:
            samples = await client.get_order_samples(project_id, order_id)

            if not samples:
                click.echo("No samples in this order.")
                return

            click.echo(f"{'ID':<40} {'NAME':<30} {'STATUS':<15}")
            click.echo("-" * 85)

            for s in samples:
                click.echo(f"{s.id:<40} {s.name:<30} {s.status:<15}")

        except APIError as e:
            click.echo(f"Error: {e}", err=True)
            raise SystemExit(1)

    asyncio.run(_samples())


@orders.command("add-sample")
@click.option("-p", "--project", help="Project ID (uses default if not specified)")
@click.argument("order_id")
@click.argument("sample_id")
@click.option("--curl", is_flag=True, help="Output curl command instead of executing")
def add_sample_to_order(project: str | None, order_id: str, sample_id: str, curl: bool):
    """Add a sample to an order.

    \b
    ORDER_ID is the order identifier.
    SAMPLE_ID is the sample identifier.
    """
    project_id = require_project(project)

    if curl:
        data = {"sample_id": sample_id}
        print(miner_curl("POST", f"/orders/{order_id}/samples", project_id, data=data))
        return

    async def _add():
        client = MinerAPIClient()
        try:
            await client.add_sample_to_order(project_id, order_id, sample_id)
            click.echo(f"Sample {sample_id} added to order {order_id}.")

        except APIError as e:
            click.echo(f"Error: {e}", err=True)
            raise SystemExit(1)

    asyncio.run(_add())


@orders.command("remove-sample")
@click.option("-p", "--project", help="Project ID (uses default if not specified)")
@click.argument("order_id")
@click.argument("sample_id")
@click.option("--curl", is_flag=True, help="Output curl command instead of executing")
def remove_sample_from_order(project: str | None, order_id: str, sample_id: str, curl: bool):
    """Remove a sample from an order.

    \b
    ORDER_ID is the order identifier.
    SAMPLE_ID is the sample identifier.
    """
    project_id = require_project(project)

    if curl:
        print(miner_curl("DELETE", f"/orders/{order_id}/samples/{sample_id}", project_id))
        return

    async def _remove():
        client = MinerAPIClient()
        try:
            await client.remove_sample_from_order(project_id, order_id, sample_id)
            click.echo(f"Sample {sample_id} removed from order {order_id}.")

        except APIError as e:
            click.echo(f"Error: {e}", err=True)
            raise SystemExit(1)

    asyncio.run(_remove())
