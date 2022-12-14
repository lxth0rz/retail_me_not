const Apify = require('apify');
// const playwright = require('playwright');
const { handleStart, handleList, handleDetail } = require('./src/routes');

const { utils: { log } } = Apify;

Apify.main(async () => {
    // Apify.openRequestQueue() creates a preconfigured RequestQueue instance.
    // We add our first request to it - the initial page the crawler will visit.

    // https://sdk.apify.com/docs/examples/accept-user-input
    const { CategoriesOnly } = await Apify.getInput();

    const envObj = Apify.getEnv();
    const { userId } = envObj;

    let dataset;
    let startUrls = [];
    if (CategoriesOnly === true) {
        if (userId === '8pcsYfKdPip3DPAHv') {
            dataset = await Apify.openDataset('retail-me-not-cats');
            // set as default dataset or check if user is MedH
            const datasetInfo = await dataset.getInfo();
            const { itemCount } = datasetInfo;
            if (itemCount > 0) {
                await dataset.drop();
                dataset = await Apify.openDataset('retail-me-not-cats')
            }
        }

        console.log('CategoriesOnly === true');
        startUrls = [
            'https://www.retailmenot.com/coupons/?nav=A',
        ];
    }

    const requestList = await Apify.openRequestList('start-urls', startUrls);
    const requestQueue = await Apify.openRequestQueue();
    // const proxyConfiguration = await Apify.createProxyConfiguration();

    // Create an instance of the PlaywrightCrawler class - a crawler
    // that automatically loads the URLs in headless Chrome / Playwright.
    const crawler = new Apify.PlaywrightCrawler({
        requestList,
        requestQueue,
        // proxyConfiguration,
        launchContext: {
            // Here you can set options that are passed to the playwright .launch() function.
            launchOptions: {
                headless: false,
            },
        },

        // Stop crawling after several pages
        maxRequestsPerCrawl: 50,

        // This function will be called for each URL to crawl.
        // Here you can write the Playwright scripts you are familiar with,
        // with the exception that browsers and pages are automatically managed by the Apify SDK.
        // The function accepts a single parameter, which is an object with a lot of properties,
        // the most important being:
        // - request: an instance of the Request class with information such as URL and HTTP method
        // - page: Playwright's Page object (see https://playwright.dev/docs/api/class-page)
        handlePageFunction: async ({ request, page }) => {
            console.log(`Processing ${request.url}...`);

            // A function to be evaluated by Playwright within the browser context.
            // eslint-disable-next-line camelcase
            let source_url;
            const data = await page.$$eval('.styles__LinkListEntry-dlih3y-2.iswSRg', ($posts, source_url) => {
                const scrapedData = [];

                // We're getting the title, rank and URL of each post on Hacker News.
                $posts.forEach(($post) => {
                    scrapedData.push({
                        category_url: `https://www.retailmenot.com${$post.getAttribute('href')}`,
                        category_name: $post.innerText,
                        source_url,
                    });
                });

                return scrapedData;
            }, source_url = request.url);

            // Store the results to the default dataset.
            if (userId === '8pcsYfKdPip3DPAHv') {
                await dataset.pushData(data);
            } else {
                await Apify.pushData(data);
            }

            // Find a link to the next page and enqueue it if it exists.
            const infos = await Apify.utils.enqueueLinks({
                page,
                requestQueue,
                selector: '.styles__LetterNavItemLink-bwj2bv-2.eoXEWS',
            });

            if (infos.length === 0) console.log(`${request.url} is the last page!`);
        },

        // This function is called if the page processing failed more than maxRequestRetries+1 times.
        handleFailedRequestFunction: async ({ request }) => {
            console.log(`Request ${request.url} failed too many times.`);
        },
    });

    // Run the crawler and wait for it to finish.
    await crawler.run();

    console.log('Crawler finished.');
});
