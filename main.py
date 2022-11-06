from bs4 import BeautifulSoup as bs
import requests
import json


class AnimeParser:
    headers = ({'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/69.0'})
    NORMAL_STATUS_CODE = 200

    def __init__(self):
        self.proxy = self.get_free_proxies()

    def get_response(self, url: str, session: requests.Session = requests) -> requests.Response:
        """
        Method for getting a response, using a proxy from generated list
        """
        for ip in self.proxy:
            proxies = {
                'http': f'http://{ip}',
                'https': f'https://{ip}'
            }

            try:
                response = session.get(url=url, headers=self.headers, proxies=proxies, timeout=2)
                # if the IP does not work, it is removed from the list
                if response.status_code != self.NORMAL_STATUS_CODE:
                    self.proxy.pop(self.proxy.index(ip))
                    continue
                return response

            except Exception:
                self.proxy.pop(self.proxy.index(ip))
                continue

    def _get_set_links_anime(self, session: requests.Session, next_limit: str = '') -> set:
        """
        Parses one page of rating for given positions
        """
        url = f'http://www.world-art.ru/animation/rating_top.php{next_limit}'

        response = self.get_response(url, session)

        soup = bs(response.text, 'lxml')
        urls = soup.find_all('a', class_='review')
        urls = {data.text: data['href'] for data in urls}

        # The next selection of anime by rating is set
        if urls[list(urls.keys())[1]].startswith('http://www.world-art.ru/') and next_limit != '':
            next_limit = False
            urls.pop(list(urls.keys())[0])
            urls.pop(list(urls.keys())[-1])

        elif urls[list(urls.keys())[1]].startswith('http://www.world-art.ru/') and next_limit == '':
            next_limit = urls[list(urls.keys())[0]]
            next_limit = next_limit[next_limit.index('?'):]
            urls.pop(list(urls.keys())[0])
            urls.pop(list(urls.keys())[-1])

        else:
            next_limit = urls[list(urls.keys())[1]]
            next_limit = next_limit[next_limit.index('?'):]
            urls.pop(list(urls.keys())[0])
            urls.pop(list(urls.keys())[-1])

        return urls, next_limit

    def get_all_links_anime(self) -> dict:
        """
        Method of compiling one dict of anime by rating from all pages
        """
        anime_links = {}
        next_limits = ''

        with requests.session() as session:
            while True:
                urls_set, next_limits = self._get_set_links_anime(session, next_limits)
                anime_links.update(urls_set)
                print(f'parsing page: {next_limits}, with ip: {self.proxy[0]}\n')

                # If the next sample is False, then it is the last one
                if next_limits is False:
                    break

        return self.filter_anime_links(anime_links)

    def filter_anime_links(self, anime_links: dict[str, str]) -> dict[str, str]:
        """
        Removing redundant links to votes history
        """
        item = anime_links.copy().items()
        for url in item:
            if url[1].startswith('http://www.world-art.ru/animation/votes_history'):
                anime_links.pop(url[0])
        return anime_links

    def save_to_json(self, anime_links: dict[str, str]):
        """
        convert dictionary to json and save to file
        """
        with open("anime_links.json", "w", encoding='utf-8') as json_file:
            json.dump(anime_links, json_file, ensure_ascii=False, indent=2)
        print("Data successfully saved to file!")

    def get_list_link_anime(self) -> list:
        """
        We give out all links to anime in list format
        """
        anime_dict = self.get_all_links_anime()
        anime_dict = self.filter_anime_links(anime_dict)
        return list(anime_dict.values())

    def get_free_proxies(self) -> list[str]:
        """
        Сreate a proxy list using the free site free-proxy-list.net
        """
        url = "https://free-proxy-list.net/"
        soup = bs(requests.get(url).content, "lxml")
        proxies = []

        for row in soup.find("table").find_all("tr")[1:]:
            tds = row.find_all("td")
            try:
                ip = tds[0].text.strip()
                port = tds[1].text.strip()
                host = f"{ip}:{port}"
                proxies.append(host)
            except IndexError:
                continue

        return proxies


def main():
    parser = AnimeParser()
    urls = parser.get_all_links_anime()
    parser.save_to_json(urls)


if __name__ == '__main__':
    main()
