# epex-spot-scraper
Pulls data from the EPEX Spot Market Results for a given day, writes it to an XLSX file.

## Prereqs

* [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)

## Initialise

On Windows, the current best practice for configuring Python events is `py`:

```pwsh
py install 3.12
py -3.12 -m venv .env
py -m pip install -r requirements.txt
py -m playwright install chromium
```

## Usage

```pwsh
.\.env\Scripts\activate
py scrape_epex.py --date "2025-11-05" --template template.xlsx --out out.xslx
```

Or should you just wish to run this for `today`, use:

```pwsh
py scrape_epex.py --date "$(Get-Date -Format 'yyyy-MM-dd')" --template template.xlsx --out out.xlsx
```

And yesterday's date would be:

```pwsh
$EpexDate=$(Get-Date (Get-Date).AddDays(-1) -Format 'yyyy-MM-dd')
py scrape_epex.py --date "$EpexDate" --template template.xlsx --out "EpexSpotMarketResults-${EpexDate}.xlsx"
```