from bs4 import BeautifulSoup as bs4
import requests


class Stats():
    def __init__(self, rank: int, global_internet_users: float, impressions: int,
                 visitor_countries: list[str], daily_revenue: float,
                 estimated_value: float, daily_visitors: int,
                 monthly_visits: int):
        """Class to hold website statistics.

        Args:
            rank (int): Global rank of the website
            global_internet_users (float): Percentage of global internet users
            impressions (int): Number of daily impressions
            visitor_countries (list[str]): List of visitor countries
            daily_revenue (float): Daily revenue of the website
            estimated_value (float): Estimated value of the website
            daily_visitors (int): Number of daily visitors
            monthly_visits (int): Number of monthly visitors
        """
        self.rank = rank
        self.global_internet_users = global_internet_users
        self.impressions = impressions
        self.visitor_countries = visitor_countries
        self.daily_revenue = daily_revenue
        self.estimated_value = estimated_value
        self.daily_visitors = daily_visitors
        self.monthly_visits = monthly_visits


class HypeStat():
    def __init__(self):
        """Class to interact with HypeStat website for fetching and updating website statistics.
        """
        self.url = "https://hypestat.com"
        self.session = requests.Session()
        self.session.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:146.0) Gecko/20100101 Firefox/146.0',
            'Accept': '*/*',
            'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://hypestat.com',
            'Connection': 'keep-alive',
            'Referer': 'https://hypestat.com/info/facebook.com',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Priority': 'u=0',
        }

    def update_stats(self, domain: str) -> bool:
        """Update the statistics for a given domain if they are outdated.

        Args:
            domain (str): The domain to update statistics for

        Returns:
            bool: True if the update was initiated, False otherwise
        """
        self.session.get(f"{self.url}/info/{domain}")
        response = self.session.get(f"{self.url}/info/{domain}")
        soup = bs4(response.text, "html.parser")

        if "Update will be available in 24 hours" not in response.text:
            csrf_token = soup.find("meta", {"name": "csrf-token"})['content']  # type: ignore
            data = {
                "url": domain,
                "method": "UpdateDomain",
                "CsrfToken": csrf_token
            }
            response = self.session.post('https://hypestat.com/js_req.php', data=data)
            if response.status_code == 200:
                return True
            else:
                return False
        return False

    def get_stats(self, domain: str) -> Stats:
        """Fetch and return the statistics for a given domain.

        Args:
            domain (str): The domain to fetch statistics for

        Returns:
            Stats: The statistics of the domain
        """
        self.update_stats(domain)
        response = self.session.get(f"{self.url}/info/{domain}")
        soup = bs4(response.text, "html.parser")

        report = soup.find("div", {"class": "website_report"})
        rank = int(report.find_all("strong")[0].text.strip().replace(",", "")[1:])  # type: ignore
        global_internet_users = float(report.find_all("strong")[1].text.strip()[:-1])  # type: ignore
        impressions = int(report.find_all("strong")[3].text.strip().replace(",", "").split(" ")[0])  # type: ignore
        visitor_countries = [strong.text.strip(", ") for strong in report.find_all("div")[3].find_all("strong")]  # type: ignore
        daily_revenue = float(report.find_all("strong")[4 + len(visitor_countries)].text.strip().replace(",", "")[1:])  # type: ignore
        estimated_value = float(report.find_all("strong")[5 + len(visitor_countries)].text.strip().replace(",", "")[1:])  # type: ignore

        report = soup.find("dl", {"class": "traffic_report"})
        daily_visitors = int(report.find_all("dd")[0].text.strip().replace(",", ""))  # type: ignore
        monthly_visits = int(report.find_all("dd")[1].text.strip().replace(",", ""))  # type: ignore

        return Stats(
            rank,
            global_internet_users,
            impressions,
            visitor_countries,
            daily_revenue,
            estimated_value,
            daily_visitors,
            monthly_visits
        )
