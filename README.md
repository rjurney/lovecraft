# Lovecraft RAG - The Resurrection

This is a project to use generative AI to speak to the ghost of Lovecraft through his letter and stories.

## Setup

### Get Poetry

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

OR

```bash
pipx install poetry
```

### Install Dependencies

```bash
poetry install
```

## Run the Project

1. Get the stories from hplovecraft.com [read them, they're great!]

```bash
scrapy runspider lovecraft/scrape.py
```

