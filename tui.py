from pathlib import Path
import re
import zipfile

from textual.app import App, ComposeResult
from textual.message import Message
from textual.widgets import ListView, ListItem, Label, Tree, Static

from pengolodh.config import books_configuration
from pengolodh.epub import process_volume
from pengolodh.extract import extract_node, extract_xml


def get_path(book_id_or_path: str) -> Path | zipfile.Path | None:

    books = books_configuration()

    if book_id_or_path in books:
        path_string = books[book_id_or_path]
    else:
        path_string = book_id_or_path

    path = Path(path_string)
    book_path: Path | zipfile.Path
    if not path.is_dir():
        if not zipfile.is_zipfile(path):
            return None
        book_path = zipfile.Path(zipfile.ZipFile(path))
    else:
        book_path = path
    
    return book_path


class BookSelected(Message):
    def __init__(self, book_id: str, title: str):
        self.book_id = book_id
        self.title = title
        super().__init__()


class BookList(ListView):
    BORDER_TITLE = "Books"

    def on_mount(self):
        if books := books_configuration():
            for book_id, path in books.items():
                if path := get_path(book_id):
                    title = process_volume(path)["metadata"]["title"]
                    item = ListItem(Label(f"[cyan]{book_id}[/cyan] [bold]{title}[/bold]"))
                    item.book_id = book_id
                    item.title = title
                    self.append(item)
        else:
            # @@@
            self.append(ListItem(Label("No books found.")))
    
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if hasattr(event.item, 'book_id'):
            self.post_message(BookSelected(event.item.book_id, event.item.title))


def build_nav_tree(book_path: Path | zipfile.Path, node, nav_point) -> None:

    styled_label = ""
    if nav_point.get("playOrder"):
        styled_label += f"[dim][{nav_point['playOrder']}][/dim] "
    styled_label += f"[cyan]{nav_point['id']}[/cyan] "
    styled_label += f"[bold]{nav_point['label']}[/bold] "
  
    if nav_point["children"]:
        child_node = node.add(styled_label, expand=True)

        for child in nav_point["children"]:
            build_nav_tree(book_path, child_node, child)
    else:
        child_node = node.add_leaf(styled_label)

    child_node.data = {
        "book_path": book_path,
        "item_path": nav_point["src"]
    }


class ItemSelected(Message):
    def __init__(self, book_path, item_path: str):
        self.book_path = book_path
        self.item_path = item_path
        super().__init__()


class NCX(Tree[str]):
    BORDER_TITLE = "Navigation Map"

    def load_book(self, book_id: str, title: str) -> None:
        self.clear()
        self.root.label = title
        self.root.expand()
        if path := get_path(book_id):
            volume_data = process_volume(path)
            for nav_point in volume_data["ncx"]["navMap"]:
                build_nav_tree(path, self.root, nav_point)

    def on_tree_node_selected(self, event: Tree.NodeSelected[str]) -> None:
        self.post_message(
            ItemSelected(event.node.data["book_path"], event.node.data["item_path"]))


def build_tree(node, data):

    address, label, offset, total_length, text, children, tail = data

    if "#" in label:
        a, d = label.split("#")
    else:
        a, d = label, ""
    if "." in a:
        b, c = a.split(".")
    else:
        b, c = a, ""
    styled_label = f"[bold]{address}[/bold] " if address else ""
    styled_label += f"[green]{b}[/green]"
    if c:
        styled_label += f".[cyan]{c}[/cyan]"
    if d:
        styled_label += f"[dim]#{d}[/dim]"

    styled_label += f" [magenta][{offset}:{offset+total_length}][/magenta]"

    if children or text:
        child_node = node.add(styled_label, expand=True)
    else:
        child_node = node.add_leaf(styled_label)

    if text:
        child_node.add_leaf(f"[yellow]{repr(text)}[/yellow]")

    for child in children:
        build_tree(child_node, child)

    if tail:
        node.add_leaf(f"[yellow]{repr(tail)}[/yellow]")

    child_node.data = address


class AddressSelected(Message):
    def __init__(self, address: str):
        self.address = address
        super().__init__()


class XMLTree(Tree[str]):
    BORDER_TITLE = "XML Tree"

    def load_item(self, book_path, item_path) -> None:
        self.clear()
        path = process_volume(book_path)["ncx_path"].parent / item_path.split("#")[0]
        self.root.label = str()
        self.root.expand()
        node = extract_node(path, None, recurse=True, dictionary=False)
        build_tree(self.root, node)

    def on_tree_node_selected(self, event: Tree.NodeSelected[str]) -> None:
        if event.node.data:
            self.post_message(AddressSelected(event.node.data))


class Content(Static):
    BORDER_TITLE = "Content"

    def load_content(self, book_path, item_path, address):
        path = process_volume(book_path)["ncx_path"].parent / item_path.split("#")[0]
        content = extract_xml(path, address)
        content = re.sub(r"\s+", " ", content)
        content = re.sub(r"<div[^>]*>", "", content)
        content = re.sub(r"</div>", "\n", content)
        content = re.sub(r"<p[^>]*>", "", content)
        content = re.sub(r"</p>", "\n", content)
        content = re.sub(r"<br[^/]*/>", "\n", content)
        content = re.sub(r"<span[^>]*>", "[yellow]", content)
        content = re.sub(r"</span>", "[/yellow]", content)
        content = re.sub(r"<a[^>]*/>", "[cyan]#[/cyan]", content)
        content = re.sub(r"<a[^>]*>", "[underline]", content)
        content = re.sub(r"</a>", "[/underline]", content)
        content = re.sub(r"<b[^>]*>", "[bold]", content)
        content = re.sub(r"</b>", "[/bold]", content)
        content = re.sub(r"<img[^>]*/>", "[magenta]*[/magenta]", content)
        content = re.sub(r"<i[^>]*>", "[italic]", content)
        content = re.sub(r"</i>", "[/italic]", content)
        if content:
            self.update(content)


class PengolodhApp(App):
    CSS_PATH = "pengolodh.tcss"

    def compose(self) -> ComposeResult:
        yield BookList(classes="box")
        yield NCX(label="...", classes="box")
        yield XMLTree(label="...", classes="box")
        yield Content(classes="box")

    def on_book_selected(self, message: BookSelected) -> None:
        ncx_widget = self.query_one(NCX)
        ncx_widget.load_book(message.book_id, message.title)
        self.book_path = get_path(message.book_id)

    def on_item_selected(self, message: ItemSelected) -> None:
        xmltree_widget = self.query_one(XMLTree)
        xmltree_widget.load_item(message.book_path, message.item_path)
        self.item_path = message.item_path

    def on_address_selected(self, message: AddressSelected) -> None:
        content_widget = self.query_one(Content)
        content_widget.load_content(self.book_path, self.item_path, message.address)


if __name__ == "__main__":
    app = PengolodhApp()
    app.run()
