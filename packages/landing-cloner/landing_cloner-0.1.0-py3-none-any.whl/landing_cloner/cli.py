import os
import click
import sys
from landing_cloner.utils import get_folder_name
from landing_cloner.server_builder import build_server
from landing_cloner.url2file import url2singlefile


@click.group(invoke_without_command=True)
@click.option("-p", "--path", help="URL of the web page to clone.",default=None)
@click.option("--name", "-n", help="Custom name for the project folder.", default=None)
@click.option("--dockerfile", "-d", is_flag=True, help="Generate a Dockerfile.", default=False)
@click.pass_context
def cli(ctx, path, name, dockerfile):
    """Flask Clone CLI - Create Flask apps from web pages or local HTML files.
    
    Examples:
    
      landing_cloner clone https://example.com
      landing_cloner up_file ./page.html -n myapp
      landing_cloner clone https://example.com -p ../path/to/project -d
      landing_cloner --help for detailed information

    """
    click.echo(ctx.get_help())



@cli.command("clone")
@click.argument("url")
@click.option("-p", "--path", help="URL of the web page to clone.",default=None)
@click.option("--name", "-n", help="Custom name for the project folder.", default=None)
@click.option("--dockerfile", "-d", is_flag=True, help="Generate a Dockerfile.", default=False)
def clone(url, path=None, name=None, dockerfile=False):
    """Create a Flask app from a cloned web page."""
    html_content = url2singlefile(url)


    # Determine folder name
    folder_name = name if name else get_folder_name(url)
    folder_path = os.path.join(os.getcwd(), folder_name)
    
    # Check if folder exists
    if os.path.exists(folder_path):
        click.echo(click.style(f"Error: Folder '{folder_name}' already exists.", fg="red"))
        sys.exit(1)
    
    click.echo(click.style(f"Creating Flask app from: {url}", fg="cyan"))
    click.echo(click.style(f"Project folder: {folder_path}", fg="cyan"))
    
    build_server(folder_path, html_content, dockerfile)

    

@cli.command("up_file")
@click.argument("folder_name")
@click.option("-p", "--path", help="URL of the web page to clone.",default=None)
@click.option("--name", "-n", help="Custom name for the project folder.", default=None)
@click.option("--dockerfile", "-d", is_flag=True, help="Generate a Dockerfile.", default=False)
def run(folder_name, path=None, name=None, dockerfile=False):
    """Serve an existing HTML File."""
    source_path = os.path.join(os.getcwd(), folder_name)
    
    if not os.path.exists(folder_path):
        click.echo(click.style(f"Error: Folder '{folder_name}' not found.", fg="red"))
        sys.exit(1)
    
    html_content = open(folder_path, 'r').read()
    
    # Determine folder name
    folder_name = name if name else get_folder_name(folder_name)
    folder_path = os.path.join(os.getcwd(), folder_name)
    
    # Check if folder exists
    if os.path.exists(folder_path):
        click.echo(click.style(f"Error: Folder '{folder_name}' already exists.", fg="red"))
        sys.exit(1)
    
    click.echo(click.style(f"Creating Flask app from file: {source_path}", fg="cyan"))
    click.echo(click.style(f"Project folder: {folder_path}", fg="cyan"))
    
    build_server(folder_path, html_content, dockerfile)


if __name__ == "__main__":
    cli()
    