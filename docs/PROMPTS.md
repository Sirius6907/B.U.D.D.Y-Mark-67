# B.U.D.D.Y — Full Prompt Benchmark Suite

40 prompts at maximum complexity, designed to validate autonomous operation across browser and OS environments.

---

## Browser-Only Operations

| # | Prompt |
|---|---|
| 1 | Research the current top 5 AI models for coding, extract their pricing tables from 5 different sites, and generate a side-by-side comparison CSV. |
| 2 | Login to my GitHub, find the repository with the most issues, and summarize the top 3 critical bugs across all of them. |
| 3 | Navigate to a flight booking site, find the cheapest flight from NYC to London for next week, and take a screenshot of the checkout page. |
| 4 | Automate the signup process for a new service using a temporary email provider, verifying the link in the inbox automatically. |
| 5 | Crawl a documentation site, find all broken internal links, and report them in a structured JSON format. |
| 6 | Monitor a stock price on Yahoo Finance; if it hits a target price, login to my trading platform and place a limit order. |
| 7 | Extract all comments from a trending Reddit thread, filter by those mentioning a specific keyword, and perform sentiment analysis. |
| 8 | Navigate to a complex SaaS dashboard, find the Billing section, and download the last 3 invoices as PDFs. |
| 9 | Perform a Google Search for "best recursive algorithms", visit the first 3 links, and extract all Python code snippets found. |
| 10 | Login to a forum, find the most popular thread in the Security section, and summarize the main debate in 5 bullet points. |
| 11 | Navigate to LinkedIn, search for "Senior AI Engineer" roles in SF, and extract the job description and company name for the first 10 results. |
| 12 | Go to a news site, find the Politics section, and extract the headline, author, and timestamp for every article on the front page. |
| 13 | Find a product on Amazon, compare its price with eBay and Walmart, and report where it's cheapest including shipping. |
| 14 | Navigate to a mapping service, find the distance between 5 different cities, and calculate the optimal route for a delivery truck. |
| 15 | Login to a project management tool (e.g., Trello), find all cards labeled "Urgent", and move them to the top of the "Doing" column. |
| 16 | Search for "Next.js 14 server components" tutorials, visit the top 5 results, and list the common pitfalls mentioned. |
| 17 | Navigate to a weather site, extract the 7-day forecast for 10 different locations, and identify the city with the highest humidity. |
| 18 | Login to a CRM, find all leads created in the last 24 hours, and send a personalized "Welcome" message to each. |
| 19 | Go to a research paper database (e.g., ArXiv), search for "Autonomous Agents", and download the PDFs of the 3 most cited papers. |
| 20 | Navigate to a social media site, find all posts with the hashtag #BUDDY, and extract the usernames and follower counts of the authors. |

---

## Cross-Environment Operations (Browser + OS)

| # | Prompt |
|---|---|
| 21 | Research the latest FastAPI best practices, then create a local directory `api_project`, initialize a git repo, and write a production-ready `main.py`. |
| 22 | Scan my local `Downloads` folder for images, upload them to an AI image-upscaling site one by one, and download the enhanced versions to a `high_res` folder. |
| 23 | Scrape the documentation for a new Python library, generate a local Markdown cheatsheet, and save it to my `Documents/Guides` folder. |
| 24 | Find the 5 most popular VS Code extensions for Rust on the Marketplace, and write a local shell script to install all of them automatically. |
| 25 | Monitor my local CPU usage; if it exceeds 80%, search the web for "Windows 11 high CPU fixes" and summarize the top 3 solutions. |
| 26 | Search for a public dataset on Kaggle, download it, unzip it locally, and perform a basic data analysis using a local Python script. |
| 27 | Extract the Requirements section from a local project's `README.md`, search for the latest versions of those libraries on PyPI, and update the `requirements.txt`. |
| 28 | Research a list of 10 companies, find their LinkedIn profiles, and save a local Excel file with their headquarters' locations and employee counts. |
| 29 | Download 5 different open-source fonts from the web, install them on my system, and create a local HTML file showcasing all of them. |
| 30 | Scan my local `projects` folder for `TODO` comments, search for solutions for each on Stack Overflow, and save the links as comments next to the TODOs. |
| 31 | Research "modern glassmorphic CSS" trends, create a local React component file named `GlassCard.tsx`, and implement the styles found. |
| 32 | Find the documentation for the `nmap` CLI on Kali Linux, and create a local Security Audit checklist based on the recommended flags. |
| 33 | Download the latest version of a specific open-source software, verify its checksum locally, and run the installer if the checksum matches. |
| 34 | Scrape a news site for the Tech headlines, generate a local PDF summary with images, and email it using a local mail server. |
| 35 | Search for "Docker optimization tips", find the top 5 configurations, and update my local `docker-compose.yml` accordingly. |
| 36 | Research the current weather in London, and if it's raining, create a local desktop reminder to "Bring an umbrella". |
| 37 | Extract all links from a web page, check which ones are currently accessible from my local network, and log the results to `network_log.txt`. |
| 38 | Find the latest release of a GitHub project, download the source code, and run the local `pytest` suite to ensure it works in my environment. |
| 39 | Search for "best color palettes for dark mode", and create a local `theme.json` file with the hex codes found. |
| 40 | Research a specific bug error message from my local logs on Google, find the fix on GitHub, and apply the suggested patch to my local code. |
