import sys
import httpx
import typer
import IPython
import lxml.html
from rich.table import Table
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from typing_extensions import Annotated
from importlib.metadata import version
from .user_agents import USER_AGENTS

cli = typer.Typer(help="whsk: Web Harvesting/Scraping toolKit")

VERSION = version("whsk")
_default_user_agent = f"whsk/{VERSION}"

# Common Options
opt = {
    "user_agent": typer.Option("--ua", help="User agent to make requests with"),
    "postdata": typer.Option(
        "--postdata", "-p", help="POST data (will make a POST instead of GET)"
    ),
    "headers": typer.Option(
        "--header", "-h", help="Additional headers in format 'Name: Value'"
    ),
    "css": typer.Option("--css", "-c", help="css selector"),
    "xpath": typer.Option("--xpath", "-x", help="xpath selector"),
}


def parse_headers(headers: list[str]) -> dict:
    """Parse list of header strings into a dictionary"""
    header_dict = {}
    for header in headers:
        try:
            name, value = header.split(":", 1)
            header_dict[name.strip()] = value.strip()
        except ValueError:
            typer.echo(f"Invalid header format: {header}", fg="red")
            raise typer.Exit(1)
    return header_dict


def make_request(url, *, headers, user_agent, postdata):
    """
    Helper function for redundant code between methods.

    Will take all parameters related to request and return
    a 2-tuple of the raw response and the parsed response.

    The second parameter may be a:
        - JSON dict
        - lxml.html.HtmlElement
        - lxml.etree.Element
    """
    header_dict = parse_headers(headers)

    # user agent either from headers, shortcut, or default
    if "user-agent" in headers and user_agent:
        typer.secho("Cannot use --ua shortcut and also pass --header User-Agent")
        raise typer.Exit(1)
    elif "user-agent" in header_dict:
        pass  # make no changes
    elif not user_agent:
        header_dict["user-agent"] = _default_user_agent
    elif user_agent in USER_AGENTS:
        header_dict["user-agent"] = USER_AGENTS[user_agent]
    else:
        typer.secho("--ua shortcut must be one of: " + ", ".join(USER_AGENTS))
        raise typer.Exit(1)

    # code executed, to give users a starting point
    code = []
    method = "GET"
    if postdata:
        method = "POST"
    resp = httpx.request(method, url, headers=header_dict, data=postdata)
    code.append(f"""# executed code
resp = httpx.request({method!r}, {url!r},
                     headers={headers!r},
                     data={postdata!r})""")
    if resp.headers["content-type"] == "application/json":
        root = resp.json()
        code.append("root = resp.json()")
    elif "xml" in resp.headers["content-type"]:
        root = lxml.etree.fromstring(resp.content)
        code.append("lxml.etree.fromstring(resp.content)")
    else:
        root = lxml.html.fromstring(resp.text)
        code.append("root = lxml.html.fromstring(resp.text)")
    return resp, root, code


def parse_selectors(root, css, xpath):
    # check for a selector
    code = selected = selector = None
    if css and xpath:
        typer.secho("Cannot specify css and xpath", fg="red")
        raise typer.Exit(1)
    if css:
        selector = css
        selected = root.cssselect(css)
        code = f"root.cssselect({css!r})"
    if xpath:
        selector = xpath
        selected = root.xpath(xpath)
        code = f"root.xpath({xpath!r})"
    return selector, selected, code


@cli.command()
def version():
    pyversion = sys.version.split(" ")[0]
    console = Console()
    console.print(
        Panel(
            f""" 
W   H H H  SS K K
W W W HHH  S  KK
WWWWW H H SS  K K       v{VERSION}
                """.lstrip()
            + f"\npython {pyversion:>23}"
            f"\nipython {IPython.__version__:>22}"
            f"\nlxml.html {lxml.__version__:>20}"
            f"\nhttpx {httpx.__version__:>24}",
            style="cyan",
            expand=False,
        )
    )


@cli.command()
def query(
    url: Annotated[str, typer.Argument(help="URL to scrape")],
    user_agent: Annotated[str, opt["user_agent"]] = "",
    postdata: Annotated[str, opt["postdata"]] = "",
    headers: Annotated[list[str], opt["headers"]] = [],
    css: Annotated[str, opt["css"]] = "",
    xpath: Annotated[str, opt["xpath"]] = "",
):
    """Run a one-off query against the URL"""
    resp, root, _ = make_request(
        url, headers=headers, user_agent=user_agent, postdata=postdata
    )
    if not isinstance(root, lxml.html.HtmlElement):
        typer.secho(f"Expecting HTML response, got:\n{root}", fg="red")
        raise typer.Exit(1)
    selector, selected, _ = parse_selectors(root, css, xpath)

    if selector is None:
        typer.secho("Must provide either --css or --xpath to query", fg="red")
        raise typer.Exit(1)

    for s in selected:
        print(s)


@cli.command()
def shell(
    url: Annotated[str, typer.Argument(help="URL to scrape")],
    user_agent: Annotated[str, opt["user_agent"]] = "",
    postdata: Annotated[str, opt["postdata"]] = "",
    headers: Annotated[list[str], opt["headers"]] = [],
    css: Annotated[str, opt["css"]] = "",
    xpath: Annotated[str, opt["xpath"]] = "",
):
    """Launch an interactive Python shell for scraping"""

    resp, root, code = make_request(
        url, headers=headers, user_agent=user_agent, postdata=postdata
    )
    selector, selected, selcode = parse_selectors(root, css, xpath)
    if selcode:
        code.append(selcode)

    console = Console()
    syntax = Syntax("\n".join(code), "python")
    table = Table(
        title="variables",
        show_header=False,
        title_style="bold green",
        border_style="green",
    )
    table.add_row("[green]url[/green]", url)
    table.add_row("[green]resp[/green]", str(resp))
    # if this list of parsed types expands there's probably a better way
    if isinstance(root, lxml.html.HtmlElement):
        table.add_row("[green]root[/green]", "lxml.html.HtmlElement")
    elif isinstance(root, lxml.etree._Element):
        table.add_row("[green]root[/green]", "lxml.etree.Element (XML)")
    elif isinstance(root, dict):
        table.add_row("[green]root[/green]", "dict (JSON)")
    if selector:
        table.add_row("[green]selector[/green]", selector)
        table.add_row("[green]selected[/green]", f"{len(selected)} elements")
    console.print(syntax)
    console.print(table)
    #    typer.secho(f"root: `lxml HTML element` <{root.tag}>", fg="green")
    IPython.embed(
        banner1="",
        banner2="",
        confirm_exit=False,
        colors="neutral",
    )


if __name__ == "__main__":
    cli()
