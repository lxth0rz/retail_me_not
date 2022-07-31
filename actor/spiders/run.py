import re
import os
import apify
import logging
from scrapy import Spider
from urllib.parse import urljoin
from apify_client import ApifyClient
from scrapy.http.request import Request


class amazon_products_reviews(Spider):

    name = 'retailmenot'

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0',
               'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
               'Accept-Language': 'en-US,en;q=0.5',
               'Upgrade-Insecure-Requests': '1',
               'Sec-Fetch-Dest': 'document',
               'Sec-Fetch-Mode': 'navigate',
               'Sec-Fetch-Site': 'none',
               'Sec-Fetch-User': '?1',}

    client = None

    logger = None

    directory_path = os.getcwd()

    env = os.getenv("SCRAPY_ENV")

    input_urls = [{'url': 'https://www.amazon.com/s?i=electronics-intl-ship&bbn=16225009011&rh=n%3A541966%2Cn%3A13896617011%2Cn%3A565108%2Cp_36%3A10000-&s=price-asc-rank&dc&qid=1655371808&rnid=2421885011&ref=sr_nr_p_36_6'}]

    scrape_cats = False

    client = None

    def start_requests(self):

        self.logger = logging.getLogger()

        if self.env is None:

            # Initialize the main ApifyClient instance
            client = ApifyClient(os.environ['APIFY_TOKEN'], api_url=os.environ['APIFY_API_BASE_URL'])

            # Get the resource subclient for working with the default key-value store of the actor
            default_kv_store_client = client.key_value_store(os.environ['APIFY_DEFAULT_KEY_VALUE_STORE_ID'])

            # Get the value of the actor input and print it
            self.logger.info('Loading input...')
            actor_input = default_kv_store_client.get_record(os.environ['APIFY_INPUT_KEY'])['value']
            self.logger.info(actor_input)

            #self.input_urls = actor_input["input_urls"]
            self.scrape_cats = actor_input["scrape_cats"]

        if self.scrape_cats:
            yield Request(url='https://www.retailmenot.com/coupons/',
                          callback=self.extract_cats)

        # for input_url in self.input_urls:
        #     url = input_url['url']
        #
        #     #url = 'https://www.amazon.com/s?i=electronics-intl-ship&bbn=16225009011&rh=n%3A541966%2Cn%3A13896617011%2Cn%3A565108%2Cp_36%3A10000-&s=price-asc-rank&dc&qid=1655371808&rnid=2421885011&ref=sr_nr_p_36_6'
        #     if url.startswith('https://www.amazon.com/') or url.startswith("https://amazon.com/"):
        #         yield Request(url=url,
        #                       callback=self.parse_overview_page)

    def extract_cats(self, response):
        print("")

    def parse_overview_page(self, response):

        results = response.xpath('.//div[@class="sg-col-inner"]/span/div/div')
        if results and len(results) > 0:
            for result in results:

                res = result.xpath('@data-asin')
                res = res.extract()
                res = [x.strip() for x in res]
                res = [x.strip() for x in res if x != '']

                if res and len(res) > 0:

                    res = res[0].strip()

                    image = ''
                    image_node = result.xpath('.//a/div/img[@class="s-image"]/@src')
                    if image_node and len(image_node) > 0:
                        image = image_node.extract()[0].strip()

                    price = result.xpath('.//span[@class="a-price-whole"]/text()')
                    if price and len(price) > 0:
                        price = price.extract()[0].strip()
                    else:
                        price = 'N/A'

                    obj = {'ASIN': res,
                           'price': price,
                           'image': image,
                           'OverviewPageURL': response.url}

                    comments_url = 'https://www.amazon.com/product-reviews/{0}/'.format(res.strip())
                    yield Request(comments_url,
                                  meta=obj,
                                  headers=self.headers,
                                  callback=self.parse_reviews_page)

        if not self.first_page_only:
            next_url = response.xpath('.//a[contains(@class, "s-pagination-item s-pagination-next")]/@href')
            if next_url and len(next_url) > 0:
                next_url = next_url.extract()[0]
                next_url = urljoin(response.url, next_url)
                yield Request(url=self.client.scrapyGet(url=next_url),
                              meta=response.meta,
                              headers=self.headers,
                              callback=self.parse_overview_page)

    def parse_reviews_page(self, response):

        print("apply the proxies of Apify just in case the client uses it:")

        meta = response.meta

        product_url = ''
        product_title = ''
        product_url_node = response.xpath('.//a[@data-hook="product-link"]')
        if product_url_node and len(product_url_node) > 0:
            product_url = product_url_node.xpath('@href').extract()[0].strip()
            product_url = urljoin(response.url, product_url)
            product_title = product_url_node.xpath('text()').extract()[0].strip()

        brand = ''
        brand_node = response.xpath('.//div[@data-hook="cr-product-byline"]/.//a/text()')
        if brand_node and len(brand_node) > 0:
            brand = brand_node.extract()[0].strip()

        global_rating = ''
        global_rating_node = response.xpath('.//div[@data-hook="total-review-count"]/.//text()')
        if global_rating_node and len(global_rating_node) > 0:
            global_rating = global_rating_node.extract()[0].replace("global ratings", "")

        reviews = response.xpath('.//div[@data-hook="review"]')
        for review in reviews:

            review_id = ''
            review_url = ''
            review_title = ''
            review_url_node = review.xpath('.//a[@data-hook="review-title"]')
            if review_url_node and len(review_url_node) > 0:
                review_title = review_url_node.xpath('span/text()').extract()[0].strip()
                review_url = review_url_node.xpath('@href').extract()[0].strip()
                review_url = urljoin(response.url, review_url)
                review_id = re.findall('customer\-reviews/(\w+)', review_url)
                if review_id and len(review_id) > 0:
                    review_id = review_id[0].strip()

            reviewer_name = review.xpath('.//span[@class="a-profile-name"]/text()')
            if reviewer_name and len(reviewer_name) > 0:
                reviewer_name = reviewer_name.extract()
                reviewer_name = reviewer_name[0].strip()
            else:
                reviewer_name = ""

            reviewer_link = ''
            reviewer_link_node = review.xpath('.//a[@class="a-profile"]/@href')
            if reviewer_link_node and len(reviewer_link_node) > 0:
                reviewer_link = reviewer_link_node.extract()[0].strip()
                reviewer_link = urljoin(response.url, reviewer_link)

            review_body = review.xpath('.//span[@data-hook="review-body"]/.//text()')
            if review_body and len(review_body) > 0:
                review_body = review_body.extract()
                review_body = [x.strip().replace('"', "'") for x in review_body]
                review_body = [x for x in review_body if x != '']
                review_body = '"'.join(review_body)
            else:
                review_body = ""

            verified_purchase = 0
            verified_purchase_node = review.xpath('.//a/span[contains(text(), "Verified Purchase")]')
            if verified_purchase_node and len(verified_purchase_node) > 0:
                verified_purchase = 1

            rating = 0
            rating_node = review.xpath('.//*[@data-hook="review-star-rating"]/.//text()')
            if rating_node and len(rating_node) > 0:
                rating = rating_node.extract()[0].strip()

            location = ''
            review_date = ''
            review_location_date_node = review.xpath('.//*[contains(@class, "review-date")]/text()')
            if review_location_date_node and len(review_location_date_node) > 0:
                location_date_node = review_location_date_node.extract()[0].strip()
                location_date_node = location_date_node.split(" on ")
                location = location_date_node[0].replace('Reviewed in the', '').strip()
                review_date = location_date_node[1]

            helpful = 0
            helpful_node = review.xpath('.//*[@data-hook="helpful-vote-statement"]/.//text()')
            if helpful_node and len(helpful_node) > 0:
                helpful = helpful_node.extract()[0].replace("people found this helpful", "").strip()

            review_urls = {'reviewer_link': reviewer_link,
                           'product_url': product_url,
                           'image_url': meta['ASIN'],
                           'review_url': review_url,
                           'source_url': meta['OverviewPageURL']}

            # NLTK
            # https://likegeeks.com/nlp-tutorial-using-python-nltk/
            # chrome://bookmarks/?id=6631
            # tokens = nltk.word_tokenize(review_body)
            # tokens_l = [w.lower() for w in tokens if w not in stopwords.words('english') and w.isalpha() and w.lower() != 'i']
            #
            # all_counts = FreqDist(tokens_l)
            # all_counts = sorted(all_counts.items(), key=lambda x: x[1], reverse=True)
            # review_words_count_word_frequency = all_counts[:10]

            review_data = {'ASIN': meta['ASIN'],
                           'brand': brand,
                           'product_title': product_title,
                           'price': meta['price'],
                           'review_id': review_id,
                           'review_title': review_title,
                           'reviewer_name': reviewer_name,
                           'verified_purchase': verified_purchase,
                           'review_rating': rating,
                           'found_helpful': helpful,
                           'global_rating': global_rating,
                           'review_location': location,
                           #"review_words_count_word_frequency": review_words_count_word_frequency,
                           'review_date': review_date,
                           'review': review_body,
                           'URLs': review_urls}

            print (review_data)

            yield review_data
            # if self.env is None:
            #     apify.pushData(review_data)
            # else:
            #     yield review_data
