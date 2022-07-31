## ASINs Extractor

This actor allows you to extract ASINs from Amazon input URL.
 
## Input configuration

The actor has the following input options:

- **Input URL** - Specify an input url.
- **First Page Only** - Only extract ASINs from first overview page only the stops the actor.
- **Proxy** - Optionally, select a proxy to be used by the actor,
  in order to avoid IP address-based blocking by the target website.
  The actor automatically executes all the Scrapy's HTTP(S) requests through the proxy.

## Results:

Each record represent a title. The following fields is the current data you will get from the scraper...

```json
{
    "ASIN": "1593279507",
    "https://www.amazon.com/s?k=javascript&crid=UELNOIWXRCMO&sprefix=javascr%2Caps%2C277&ref=nb_sb_noss_2"
  }
```

If you have any problem or anything does not work,
please file an [issue on Apify](https://console.apify.com/actors/3vRNQLMhy0TLxnUg8#/issues).
