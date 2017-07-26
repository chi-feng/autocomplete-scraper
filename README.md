# autocomplete-scraper

## Testing instructions
 * Run `autocomplete_server.py` to start listening on localhost:8888
 * Then run `scrape.py` with `options['test'] = True`
 * this will populate a SQLite3 database `data.db` with the following tables:

### entries table
![Alt text](/entries.png?raw=true "entries table")

### search_strings table
![Alt text](/search_strings.png?raw=true "search_strings table")