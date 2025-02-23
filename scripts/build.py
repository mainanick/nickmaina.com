from datetime import datetime
from pathlib import Path
import markdown
import frontmatter
from jinja2 import Environment, FileSystemLoader, select_autoescape
import shortuuid
from slugify import slugify
from dataclasses import dataclass
import click

cwd = Path.cwd()
env = Environment(
    loader=FileSystemLoader(cwd / "templates"),
    # autoescape=select_autoescape()
)

post_template = env.get_template("post.html")
index_template = env.get_template("index.html")
tags_template = env.get_template("tags.html")
tag_list_template = env.get_template("tag_list.html")

notes = cwd / "notes"
private_notes = notes / "__private"
dist = cwd / "dist"
private_dist = dist / "__private"

all_public_notes = list(notes.glob("*.md"))
all_private_notes = list(private_notes.glob("*.md"))


@dataclass
class Post:
    layout: str
    title: str
    slug: str
    tags: list[str]
    content: str
    date: str
    py_date: datetime
    permalink: str
    filename: str
    filepath: Path
    url: str
    private: bool
    published: bool


def mini_id():
    return str(shortuuid.uuid())[:4]


def to_post(note: Path) -> Post:
    md = frontmatter.load(note)
    content = markdown.markdown(md.content)
    slug = slugify(md.get("title", "")) + "-" + mini_id()

    private = md.get("private", True)
    p = private_dist if private else dist
    url = md.get("permalink", slug) + ".html"
    u = url if not private else "__private/" + url

    post = Post(
        layout=md.get("layout", "post"),
        title=md.get("title", ""),
        slug=slug,
        tags=md.get("tags", []),
        content=content,
        date=md.get("date", ""),
        py_date=datetime.strptime(md.get("date", ""), "%d-%m-%Y %H:%M:%S %z"),
        permalink=md.get("permalink", url),
        url=u,
        filename=url,
        filepath=p / url,
        private=private,
        published=md.get("published", False),
    )
    return post


all_posts: list[Post] = []

# read all notes and append to all_posts
for note in all_public_notes:
    post = to_post(note)
    if post.published:
        all_posts.append(post)

for note in all_private_notes:
    post = to_post(note)
    if post.published:
        all_posts.append(post)

# sort all_posts by date
all_posts.sort(key=lambda p: p.py_date, reverse=True)


def rmdir(directory: Path):
    for item in directory.iterdir():
        if item.is_dir():
            rmdir(item)
        else:
            item.unlink()
    directory.rmdir()


def _clear_dist():
    if dist.exists():
        rmdir(dist)


def make_dist():
    dist.mkdir(exist_ok=True)
    private_dist.mkdir(exist_ok=True)


def render_post(post: Post) -> str:
    if post.layout == "post":
        html = post_template.render(**post.__dict__)
    return html


def build_by_tags(posts: list[Post]):
    tag_posts: dict[str, Post] = {}
    for post in posts:
        if post.private:
            continue
        tags = post.tags
        for tag in tags:
            tag_posts.setdefault(tag, []).append(post)
    tag_path = dist / "tags"
    tag_path.mkdir(exist_ok=True)
    tag_index_html = tag_list_template.render(tags=tag_posts.keys())
    (tag_path / "index.html").write_text(tag_index_html)

    for tag, posts in tag_posts.items():
        html = tags_template.render(posts=posts, tag=tag)
        path = dist / "tags" / tag
        path.mkdir(parents=True, exist_ok=True)
        path = path / "index.html"
        path.write_text(html)


def build_index(posts: list[Post]):
    public_posts = [p for p in posts if not p.private]
    private_posts = [p for p in posts if p.private]

    public_index_html = index_template.render(posts=public_posts)
    private_index_html = index_template.render(posts=private_posts)

    (dist / "index.html").write_text(public_index_html)
    (private_dist / "index.html").write_text(private_index_html)


def build_posts(posts: list[Post]):
    for post in posts:
        html = render_post(post)
        post.filepath.write_text(html)


@click.group()
def cli():
    pass


@click.command()
def clear():
    _clear_dist()
    click.echo("Dist cleared")


@click.command()
def build():
    _clear_dist()
    make_dist()
    build_index(all_posts)
    build_posts(all_posts)
    build_by_tags(all_posts)
    click.echo("Build completed")


cli.add_command(clear)
cli.add_command(build)

if __name__ == "__main__":
    cli()
