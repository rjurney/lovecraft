import scrapy
from bs4 import BeautifulSoup


class LovecraftSpider(scrapy.Spider):
    name = "lovecraft"
    allowed_domains = ["hplovecraft.com"]
    start_urls = ["https://www.hplovecraft.com/writings/texts/"]
    custom_settings = {"FEED_FORMAT": "jsonlines", "FEED_URI": "lovecraft_stories.jl"}

    def parse(self, response):
        # Extract and follow story links that match the expected pattern
        soup = BeautifulSoup(response.text)
        url = "https://www.hplovecraft.com/writings/texts/"
        prefix = "fiction/"
        links = [
            url + a["href"] for a in soup.find_all("a", href=True) if a["href"].startswith(prefix)
        ]

        # Print or return the links
        for link in links:
            print(link)

    def parse_story(self, response):
        # Use BeautifulSoup to parse and extract the plaintext
        soup = BeautifulSoup(response.text, "html.parser")
        # Assuming the story text might not always be within a specific id, we extract all text
        # You may need to adjust the extraction method based on the page structure
        story_text = "\n".join([p.get_text(strip=True) for p in soup.select("p")])
        yield {"url": response.url, "text": story_text}
