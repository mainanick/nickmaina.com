from pathlib import Path
import markdown
import frontmatter
from jinja2 import Environment, FileSystemLoader, select_autoescape
from slugify import slugify

cwd = Path.cwd()
env = Environment(
    loader=FileSystemLoader(cwd / 'templates'),
    # autoescape=select_autoescape()
)

post_template = env.get_template("post.html")

notes = cwd / 'notes'
private_notes = notes / '__private'
dist = cwd / 'dist'
private_dist = dist / '__private'

all_notes = list(notes.glob('*.md'))
all_private_notes = list(private_notes.glob('*.md'))

def clear_dist():
    if dist.exists():
        for file in dist.glob('*'):
            if file.is_file():
                file.unlink()
            else:
                for f in file.glob('*'):
                    f.unlink()
    else:
        dist.mkdir()

def make_dist():
    if not dist.exists():
        dist.mkdir()
    if not private_dist.exists():
        private_dist.mkdir()
    
def render_markdown(note: Path)-> tuple[str, str]:
    with open(note, 'r') as f:
        content = f.read()
    
    md = frontmatter.load(note)
    content = md.content
    matter = md.metadata

    html_content = markdown.markdown(content)
    
    # if layout metadata is "post" render jinja post html
    if matter.get('layout', "") == 'post':
        html = post_template.render(content=html_content, **matter)
        print("rendered post")
        print(html)

    filename = slugify(matter["title"])+".html"
    return filename, html

if __name__ == "__main__":
    clear_dist()
    make_dist()

    for note in all_notes:
        filename, html = render_markdown(note)
        with open(dist / filename, 'x') as f:
            f.write(html)

    for note in all_private_notes:
        filename, html = render_markdown(note)
        with open(private_dist / filename, 'x') as f:
            f.write(html)