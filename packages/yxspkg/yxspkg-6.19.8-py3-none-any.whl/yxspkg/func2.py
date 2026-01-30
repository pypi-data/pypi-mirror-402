import click 

@click.command()
@click.option('--passwd', '-p', prompt=True, hide_input=True)
def cli(passwd):
    return passwd