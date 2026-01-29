import depoc
import click
import sys

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from .utils._response import _handle_response
from .utils._format import _format_member


client = depoc.DepocClient()
console = Console()


@click.group(invoke_without_command=True)
@click.pass_context
def member(ctx) -> None:
    ''' Manage members of the system. '''
    if ctx.invoked_subcommand is None:
        service = client.members.all
        if response := _handle_response(service):
            for obj in response.results:
                _format_member(obj, obj.name)

@member.command
def create() -> None:
    ''' Create a new member. '''
    panel = Panel('[bold]+ ADD NEW MEMBER')
    console.print(panel)

    data: dict[str, Any] = {}
    data.update({'name': Prompt.ask('✏️  Name', default=None)})
    console.rule('',style=None, align='left')
    data.update({'cpf': Prompt.ask('📋 CPF', default=None)})
    console.rule('',style=None, align='left')
    data.update({'date_of_birth': Prompt.ask('📅 Date of Birth', default=None)})
    console.rule('',style=None, align='left')
    data.update({'role': Prompt.ask('💼 Role', default=None)})
    console.rule('',style=None, align='left')
    data.update({'hire_date': Prompt.ask('📆 Hire Date', default=None)})
    console.rule('',style=None, align='left')
    data.update({'salary': Prompt.ask('💵 Salary', default=None)})
    console.rule('',style=None, align='left')
    data.update({'phone': Prompt.ask('📱 Phone', default=None)})
    console.rule('',style=None, align='left')
    data.update({'email': Prompt.ask('✉️  Email', default=None)})
    console.rule('',style=None, align='left')
    data.update({
        'has_access': Prompt.ask('🖥️  has_access',
        choices=['True', 'False'])
    })
    console.rule('',style=None, align='left')

    service = client.members.create
    if obj := _handle_response(service, data=data):
        _format_member(obj, obj.name)

@member.command
@click.argument('id')
@click.option('--cpf')
@click.option('-r', '--role')
@click.option('-n', '--name')
@click.option('-p', '--phone')
@click.option('-e', '--email')
@click.option('-s', '--salary')
@click.option('-h', '--has-access')
@click.option('-hd', '--hire-date')
@click.option('-dob', '--date-of-birth')
@click.option('-A', '--activate', is_flag=True)
def update(
    id: str,
    cpf: str,
    role: str,
    name: str,
    phone: str,
    email: str,
    salary: str,
    has_access: str,
    hire_date: str,
    date_of_birth: str,
    activate: bool,
    ) -> None:
    ''' Update an specific member. '''
    if not any([
       cpf, role, name, phone, email, salary, has_access,
       hire_date, date_of_birth, activate
    ]):
        console.print('🚨 Specify a field to update')
        sys.exit()
    data: dict[str, Any] = {}
    data.update({'role': role}) if role else None
    data.update({'name': name}) if name else None
    data.update({'salary': salary}) if salary else None
    data.update({'has_access': has_access}) if has_access else None
    data.update({'cpf': cpf}) if cpf else None
    data.update({'hire_date': hire_date}) if hire_date else None
    data.update({'phone': phone}) if phone else None
    data.update({'email': email}) if email else None
    data.update({'date_of_birth': date_of_birth}) if date_of_birth else None
    data.update({'is_active': True}) if activate else None

    service = client.members.update

    if obj := _handle_response(service, data, resource_id=id):
        _format_member(obj, 'UPDATED', update=True)

@member.command
@click.argument('id')
def delete(id: str) -> None:
    ''' Delete an specific member. '''
    service = client.members.delete

    while True:
        prompt = click.style('Proceed to deletion? [y/n] ', fg='red')
        confirmation = input(prompt)
        if confirmation == 'n':
            sys.exit(0)
        elif confirmation == 'y':
            break

    if _handle_response(service, resource_id=id):
        console.print('✅ Member inactivated')
