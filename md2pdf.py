import os
import time
import click
import markdown
import shutil
from markdown_include.include import MarkdownInclude
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from weasyprint import HTML

EXISTING_FILE = click.Path(exists=True, dir_okay=False, resolve_path=True)


def _html(markdown_file_name, css_file_name):
    with open(markdown_file_name, mode="r", encoding="utf-8") as markdown_file:
        with open(css_file_name, mode="r", encoding="utf-8") as css_file:
            markdown_input = markdown_file.read()
            css_input = css_file.read()

            markdown_path = os.path.dirname(markdown_file_name)
            markdown_include = MarkdownInclude(configs={"base_path": markdown_path})
            html = markdown.markdown(
                markdown_input, extensions=["extra", markdown_include, "meta", "tables"]
            )

            return f"""
            <html>
              <head>
                <style>{css_input}</style>
              </head>
              <body>{html}</body>
            </html>
            """
        
def create_output_file_name(file_name):
    must_capitalize = [
        "ai",
        "ap",
        "cs",
        "usaco"
    ]
    
    words = file_name.split("_")
    output = ""
    for i in range(len(words)):
        new_word = ""
        if words[i] in must_capitalize:
            new_word = words[i].upper()
        else:
            output += words[i][0].upper() + words[i][1:]
        output += new_word
        if i < len(words)-1:
            output += " "
    return output
    
def _convert(markdown_file_name, css_file_name):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "assets", "output")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    file_name = os.path.splitext(os.path.basename(markdown_file_name))[0]
    file_name = create_output_file_name(file_name)
    html_string = _html(markdown_file_name, css_file_name)

    html_file_path = os.path.join(script_dir, file_name + ".html")
    pdf_file_path = os.path.join(script_dir, file_name + ".pdf")

    with open(html_file_path, "w", encoding="utf-8", errors="xmlcharrefreplace") as output_file:
        output_file.write(html_string)

    markdown_path = os.path.dirname(markdown_file_name)
    html = HTML(string=html_string, base_url=markdown_path)
    html.write_pdf(pdf_file_path)
    click.echo(f"PDF saved to: {pdf_file_path}")

    # Move files to the output directory
    shutil.move(html_file_path, os.path.join(output_dir, file_name + ".html"))
    shutil.move(pdf_file_path, os.path.join(output_dir, file_name + ".pdf"))

    # Delete the HTML file if it still exists
    if os.path.exists(os.path.join(output_dir, file_name + ".html")):
        os.remove(os.path.join(output_dir, file_name + ".html"))


class EventHandler(FileSystemEventHandler):
    def __init__(self, markdown_file_name, css_file_name):
        self.markdown_file_name = markdown_file_name
        self.css_file_name = css_file_name

    def on_modified(self, event):
        if event.src_path in [self.markdown_file_name, self.css_file_name]:
            click.echo(f"{event.src_path} has changed")
            _convert(self.markdown_file_name, self.css_file_name)


@click.group()
def cli():
    pass


@cli.command()
@click.argument("md", type=EXISTING_FILE)
@click.argument("css", type=EXISTING_FILE)
def watch(md, css):
    (
        "Watches Markdown file MD and stylesheet CSS for changes, "
        "and converts them to HTML and PDF documents when they are modified."
    )
    click.echo(f"Watching {md} and {css} for changes. Press CTRL+C to quit.")

    _convert(md, css)

    markdown_path = os.path.dirname(md)
    css_path = os.path.dirname(css)

    event_handler = EventHandler(md, css)
    observer = Observer()
    observer.schedule(event_handler, markdown_path)
    if markdown_path != css_path:
        observer.schedule(event_handler, css_path)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


@cli.command()
@click.argument("md", type=EXISTING_FILE)
@click.argument("css", type=EXISTING_FILE)
def convert(md, css):
    """Converts Markdown file MD and stylesheet CSS to HTML and PDF documents."""
    _convert(md, css)


if __name__ == "__main__":
    cli()
