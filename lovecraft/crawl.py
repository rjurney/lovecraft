import scrapy
from bs4 import BeautifulSoup


class LovecraftSpider(scrapy.Spider):
    """LovecraftSpider Retrieves Lovecraft stories from hplovecraft.com

    This spider retrieves the URLs of Lovecraft stories from the hplovecraft.com website
    """

    name = "lovecraft"
    allowed_domains = ["hplovecraft.com"]
    start_urls = ["https://www.hplovecraft.com/writings/texts/"]
    custom_settings = {
        "FEED_FORMAT": "jsonlines",
        "FEED_URI": "data/stories.json",
        "DOWNLOAD_DELAY": 0.25,
    }

    def parse(self, response):
        # Extract and follow story links that match the expected pattern
        links = response.css("a::attr(href)").re(r"^fiction/.+\.aspx$")
        for link in links:
            full_url = response.urljoin(link)
            yield scrapy.Request(full_url, callback=self.parse_story)

    def parse_story(self, response):
        # Use BeautifulSoup to parse and extract the plaintext
        soup = BeautifulSoup(response.text, "lxml")
        # Assuming the story text might not always be within a specific id, we extract all text
        # You may need to adjust the extraction method based on the page structure
        # story_text = "\n".join([p.get_text(strip=True) for p in soup.select("p")])
        yield {"url": response.url, "text": soup.get_text(strip=True)}
