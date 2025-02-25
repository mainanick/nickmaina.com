#!/usr/bin/env python3

from datetime import datetime
from pathlib import Path
import markdown
import frontmatter
from jinja2 import Environment, FileSystemLoader
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import click
import shutil

@dataclass
class Post:
    layout: str = "post"
    title: str = ""
    tags: List[str] = field(default_factory=list)
    content: str = ""
    date: str = ""
    py_date: Optional[datetime] = None
    permalink: str = ""
    private: bool = True
    published: bool = False


class StaticSiteGenerator:
    def __init__(self):
        self.cwd = Path.cwd()
        self.env = Environment(loader=FileSystemLoader(self.cwd / "templates"))
        self.templates = {
            "post": self.env.get_template("post.html"),
            "index": self.env.get_template("index.html"),
            "tags": self.env.get_template("tags.html"),
            "tag_list": self.env.get_template("tag_list.html")
        }
        
        self.notes_dir = self.cwd / "notes"
        self.private_notes_dir = self.notes_dir / "__private"
        self.dist_dir = self.cwd / "dist"
        self.private_dist_dir = self.dist_dir / "__private"
        
        self.posts = []
    
    def load_posts(self) -> None:
        """Load all posts from notes directories"""
        # Process public notes
        for note_path in self.notes_dir.glob("*.md"):
            post = self._parse_post(note_path)
            if post.published:
                self.posts.append(post)
        
        # Process private notes
        for note_path in self.private_notes_dir.glob("*.md"):
            post = self._parse_post(note_path)
            if post.published:
                self.posts.append(post)
        
        # Sort posts by date (newest first)
        self.posts.sort(key=lambda p: p.py_date or datetime.min, reverse=True)
    
    def _parse_post(self, note_path: Path) -> Post:
        """Parse a markdown file into a Post object"""
        md = frontmatter.load(note_path)
        
        # Parse date once
        date_str = md.get("date", "")
        py_date = None
        if date_str:
            try:
                py_date = datetime.strptime(date_str, "%d-%m-%Y %H:%M:%S %z")
            except ValueError:
                pass  # Handle invalid date format gracefully
        
        return Post(
            layout=md.get("layout", "post"),
            title=md.get("title", ""),
            tags=md.get("tags", []),
            content=markdown.markdown(md.content),
            date=date_str,
            py_date=py_date,
            permalink=md.get("permalink", ""),
            private=md.get("private", True),
            published=md.get("published", False)
        )
    
    def clear_dist(self) -> None:
        """Remove the dist directory if it exists"""
        if self.dist_dir.exists():
            shutil.rmtree(self.dist_dir)
    
    def make_dist_dirs(self) -> None:
        """Create necessary directories"""
        self.dist_dir.mkdir(exist_ok=True)
        self.private_dist_dir.mkdir(exist_ok=True)
        (self.dist_dir / "tags").mkdir(exist_ok=True)
    
    def build_posts(self) -> None:
        """Build HTML files for all posts"""
        for post in self.posts:
            template = self.templates.get(post.layout, self.templates["post"])
            html = template.render(**post.__dict__)
            
            output_dir = self.private_dist_dir if post.private else self.dist_dir
            output_path = output_dir / f"{post.permalink}.html"
            output_path.write_text(html)
    
    def build_indexes(self) -> None:
        """Build index pages for public and private posts"""
        public_posts = [p for p in self.posts if not p.private]
        private_posts = [p for p in self.posts if p.private]
        
        # Build public index
        public_index_html = self.templates["index"].render(posts=public_posts)
        (self.dist_dir / "index.html").write_text(public_index_html)
        
        # Build private index
        private_index_html = self.templates["index"].render(posts=private_posts)
        (self.private_dist_dir / "index.html").write_text(private_index_html)
    
    def build_tag_pages(self) -> None:
        """Build tag index and individual tag pages"""
        # Skip tag generation if no public posts
        public_posts = [p for p in self.posts if not p.private]
        if not public_posts:
            return
            
        # Group posts by tag
        tag_posts: Dict[str, List[Post]] = {}
        for post in public_posts:
            for tag in post.tags:
                tag_posts.setdefault(tag, []).append(post)
        
        # Build tag index page
        tag_index_html = self.templates["tag_list"].render(tags=sorted(tag_posts.keys()))
        (self.dist_dir / "tags" / "index.html").write_text(tag_index_html)
        
        # Build individual tag pages
        for tag, posts in tag_posts.items():
            tag_dir = self.dist_dir / "tags" / tag
            tag_dir.mkdir(parents=True, exist_ok=True)
            
            tag_html = self.templates["tags"].render(posts=posts, tag=tag)
            (tag_dir / "index.html").write_text(tag_html)
    
    def build(self) -> None:
        """Execute the full build process"""
        self.clear_dist()
        self.make_dist_dirs()
        self.load_posts()
        self.build_posts()
        self.build_indexes()
        self.build_tag_pages()
    
    def publish(self, skip_build=False) -> None:
        """Publish the site. SFPT to a server, etc."""
        pass 

@click.group()
def cli():
    """Static site generator for my notes"""
    pass


@click.command()
def clear():
    """Clear the dist directory"""
    generator = StaticSiteGenerator()
    generator.clear_dist()
    click.echo("Dist directory cleared")


@click.command()
@click.option("--publish", "-p", is_flag=True, help="Publish the site after building")
def build(publish):
    """Build the static site"""
    generator = StaticSiteGenerator()
    generator.build()
    click.echo("Build completed successfully")

    if publish:
        generator.publish()
        click.echo("Site published successfully")


cli.add_command(clear)
cli.add_command(build)

if __name__ == "__main__":
    cli()