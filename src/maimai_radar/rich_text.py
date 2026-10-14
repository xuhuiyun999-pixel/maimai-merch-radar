from html.parser import HTMLParser


class PlainDescription(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.images = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in {'script', 'style'}:
            self.hidden += 1
        elif not self.hidden:
            if tag in {'br', 'p', 'div', 'li'}:
                self.parts.append('\n')
            if tag == 'img':
                src = dict(attrs).get('src')
                if src:
                    self.images.append(src)

    def handle_endtag(self, tag):
        if tag in {'script', 'style'}:
            self.hidden = max(0, self.hidden - 1)
        elif not self.hidden and tag in {'p', 'div', 'li'}:
            self.parts.append('\n')

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def parse_html(value: str) -> tuple[str, list[str]]:
    parser = PlainDescription()
    parser.feed(value)
    parser.close()
    text = '\n'.join(line.strip() for line in ''.join(parser.parts).splitlines() if line.strip())
    return text, parser.images
