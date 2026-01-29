import click

from ._version import VERSION

from .commands import account
from .commands import login
from .commands import logout
from .commands import me
from .commands import bank
from .commands import finance
from .commands import contact
from .commands import receivable
from .commands import payable
from .commands import report
from .commands import customer
from .commands import supplier
from .commands import owner
from .commands import balance
from .commands import business
from .commands import member
from .commands import p as product
from .commands import inventory

@click.group()
@click.version_option(message=f'Depoc {VERSION}')
def main() -> None:
   pass
 
main.add_command(account)
main.add_command(login)
main.add_command(logout)
main.add_command(me)
main.add_command(bank)
main.add_command(finance.f)
main.add_command(contact)
main.add_command(receivable)
main.add_command(payable)
main.add_command(report)
main.add_command(customer)
main.add_command(supplier)
main.add_command(owner)
main.add_command(balance)
main.add_command(business)
main.add_command(member)
main.add_command(product)
main.add_command(inventory)
