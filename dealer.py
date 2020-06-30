import csv
import os
from bs4 import BeautifulSoup
import re
import requests
import urllib.request
from os import walk
from datetime import datetime as dt
from datetime import timedelta as delay


class Dealer:
    def __init__(self):
        self.csv_header = [['NAME', 'REVIEWS', 'LINK', 'REVIEW_DATE', 'DEALERSHIP_RATING', 'SERVICE', 'VISIT', 'IAMGE_URL', 'REVIEW_TITLE', 'CUSTOMER_NAME', 'REVIEW_CONTENT', 'SALESMAN_IMAGE', 'SALESMAN_NAME', 'RATING', 'SALESMAN_IMAGE', 'SALESMAN_NAME', 'RATING', 'SALESMAN_IMAGE', 'SALESMAN_NAME', 'RATING', 'SALESMAN_IMAGE', 'SALESMAN_NAME', 'RATING', 'SALESMAN_IMAGE', 'SALESMAN_NAME', 'RATING']]
        self.reviews = []

    def write_direct_csv(self, lines, filename):
        with open('output/%s' % filename, 'a', encoding="utf-8", newline='') as csv_file:
            writer = csv.writer(csv_file, delimiter=',')
            writer.writerows(lines)
        csv_file.close()

    def write_csv(self, lines, filename):
        if not os.path.isdir('output'):
            os.mkdir('output')
        if not os.path.isfile('output/%s' % filename):
            self.write_direct_csv(lines=self.csv_header, filename=filename)
        self.write_direct_csv(lines=lines, filename=filename)

    def read_csv(self, file_path):
        with open(file=file_path, encoding='utf-8') as csv_reader:
            data = list(csv.reader(csv_reader))
            return data

    def get_review_detail(self, url, page=1, last_page_number=1, count=1, actions=1, count_line=1):
        if int(page) > int(last_page_number):
            return self.reviews
        if 'page' in url:
            page_index = url.find('page')
            url = url[:page_index]
        request_url = url + 'page%s' % page
        print(page, last_page_number, int(page) > int(last_page_number), count, actions, count_line)
        print(request_url)
        soup = BeautifulSoup(requests.request('GET', url=request_url).content, 'html5lib')
        review_images = soup.find_all('img', {'class': re.compile('margin-bottom-md pointer')})
        for review_image in review_images:
            review_entry = review_image.find_parent(attrs={'class': 'review-entry'})
            review_content = review_entry.find(attrs={'class': 'review-content'}).text.strip()
            review_date = review_entry.find('div', attrs={'class': 'review-date'}).next_element.next_element.text.strip()
            sale_ratings = review_entry.find('div', attrs={'class': 'review-date'}).find_next(attrs={'class': 'rating-static'})['class']
            for s in sale_ratings:
                if 'rating' in s:
                    sale = s.split('-')[1]
                    sale_rating = sale[:1] + '.' + sale[1:]
            sales_visit = review_entry.find('div', attrs={'class': 'review-date'}).find_next(attrs={'class': 'small-text'}).text.strip()
            if 'VISIT' in sales_visit.upper():
                visit = sales_visit.upper().split('VISIT')[0].strip()
                new_old = sales_visit.upper().split('VISIT')[1].replace('-', '').strip()
            else:
                visit = ''
                new_old = ''
            image = review_image['src']
            title = review_entry.find_next(attrs={'class': re.compile('no-format')}).text.strip()
            salesman_name = review_entry.find_next(attrs={'class': 'notranslate'}).text.replace('-', '').strip()
            squares = review_entry.find_all(attrs={'class': 'square-image'})
            line = [review_date, sale_rating, visit, new_old, image, title, salesman_name, review_content]
            last_date = dt.today() - delay(days=365)
            try:
                a = dt.strptime(review_date, "%b %d, %Y")
            except:
                a = dt.strptime(review_date, "%B %d, %Y")
            if a < last_date: 
                return self.reviews
            for square in squares:
                table = square.find_parent(attrs={'class': 'table'})
                customer_name = table.find(attrs={'class': 'notranslate'}).text.strip()
                if table.find(attrs={'class': 'relative employee-rating-badge-sm'}):
                    customer_rating = table.find(attrs={'class': 'relative employee-rating-badge-sm'}).text.strip()
                else:
                    customer_rating = ''
                square_style = square['style'].split('url')[1][1:-1]
                line.append(square_style)
                line.append(customer_name)
                line.append(customer_rating)
            print(line)
            self.reviews.append(line)
        return self.get_review_detail(url=url, page=page+1, last_page_number=last_page_number, count=count, actions=actions, count_line=count_line)

    def get_dealers(self, html_file, save_name):
        count = 0
        if os.path.isfile('output/%s' % save_name):
            lines = self.read_csv(file_path='output/%s' % save_name)
        else:
            lines = []
        url = html_file
        page = open(url, encoding="utf8")
        soup = BeautifulSoup(page.read(), 'lxml')
        actions = soup.select('#islrg > div.islrc > div')
        for action in actions:
            count += 1
            if count < 0:
                print(count)
                continue
            link = action.find('a', {'class': 'VFACy kGQAp'})['href']
            # if 'Weber-Chevrolet-Creve-Coeur-dealer-reviews-39422' not in link:
            #     print('Not exist')
            #     continue
            if link[-4:] == '.pdf':
                continue
            link_soup = BeautifulSoup(requests.request('GET', url=link).content, 'html5lib')
            if link_soup.find('h1', {'class': 'h1-header'}):
                name = link_soup.find('h1', {'class': 'h1-header'}).get_text().split('|')[0].strip()
            elif link_soup.find(attrs={'class': re.compile('review-title')}):
                name = link_soup.find(attrs={'class': re.compile('review-title')}).split('"')[0]
            if link_soup.find('a', attrs={'href': '#reviews'}):
                review = link_soup.find('a', {'href': '#reviews'}).text.split(' ')[1].replace('(', '').replace(')', '')
            elif link_soup.select('.h2-header'):
                review = link_soup.select('.h2-header')[0].text.split(' ')[0]
            elif link_soup.select('h2 span.boldest'):
                review = link_soup.select('h2 span.boldest')[0].text.strip()
            last_page = link_soup.find_all(attrs={'class': 'page_active'})
            if len(last_page) > 2:
                last_page_number = last_page[-2].text.strip()
            else:
                last_page_number = 1
            res_reviews = self.get_review_detail(url=link, last_page_number=last_page_number, count=count, actions=len(actions), count_line=len(lines))
            previous_line = [name, review, link]
            for line in res_reviews:
                for insert_index in range(3):
                    line.insert(insert_index, previous_line[insert_index])
                if line not in lines:
                    lines.append(line)
                    self.write_csv(lines=[line], filename=save_name)
            self.reviews = []
            break
        # lines.sort(key=lambda x: (x[0], x[1]))
        # self.write_csv(lines=lines, filename='Chevrolet_Dealer.csv')

    def arrange(self, file, new_name):
        path = 'output/%s' % file
        total = []
        count = False
        with open(path, newline='', encoding='utf-8') as csvfile:
            data = list(csv.reader(csvfile))
        for d in data:
            if not count:
                count = True
                continue
            if d not in total:
                total.append(d)
                d[2] = d[2].split('page')[0]
                from datetime import datetime as dt
                from datetime import timedelta as delay
                last_date = dt.today() - delay(days=14)
                try:
                    a = dt.strptime(d[3], "%b %d, %Y")
                except:
                    a = dt.strptime(d[3], "%B %d, %Y")
                if a > last_date:
                    self.write_csv(lines=[d], filename=new_name)

    def get_fileList(self, file_path):
        f = []
        for (dirpath, dirnames, filenames) in walk(file_path):
            f.extend(filenames)
        return f

    def image_download(self, csv_file):
        if not os.path.isdir('output/images'):
            os.mkdir('output/images')
        files = self.get_fileList(file_path='output/images')
        csv_reader = self.read_csv(file_path='output/%s' % csv_file)
        image_urls = []
        for line in csv_reader:
            image_url = line[7]
            if 'http' in image_url and image_url not in image_urls:
                image_urls.append(image_url)
                name = line[9].replace(' ', '_').replace('/', '_').replace('*', '').replace('<', '').strip() + image_url[-4:]
                save_name = 'output/images/%s' % name
                if name in files:
                    print('Already Download!')
                    continue
                print(csv_file.split('_')[0], len(image_urls), name)
                urllib.request.urlretrieve(image_url, save_name)

    def dealerShip(self, fileName, dealer_file):
        self.csv_header = [['DEALERSHIP', 'NAME', 'TITLE', 'IMAGE', 'WEBSITE_URL']]
        path = 'output/%s' % fileName
        ships = []
        make = fileName.split('_')[0]
        if os.path.isfile('output/%s' % dealer_file):
            lines = self.read_csv(file_path='output/%s' % dealer_file)
        else:
            lines = [[]]
        with open(path, encoding='utf-8') as csv_read:
            rows = list(csv.reader(csv_read))
        count = 0
        for row in rows:
            count += 1
            if count < -1:
                print(count)
                continue
            if 'http' in row[2] and row[2] not in ships:
                ship_soup = BeautifulSoup(requests.request('GET', url=row[2]).content, 'html5lib')
                select = ship_soup.find(id='link')
                if select:
                    ships.append(row[2])
                    employee = 'https://www.dealerrater.com' + select.find('a', text='Employees')['href']
                    employee_soup = BeautifulSoup(requests.request('GET', url=employee).content, 'html5lib')
                    cards = employee_soup.find_all('div', attrs={'class': 'employee-tile'})
                    print(employee)
                    ship = employee_soup.find(attrs={'class': 'h1-header'}).text.strip()
                    for card in cards:
                        image_url = card.find('div', {'class': 'employee-tile-img'}).img['src']
                        wrapper = card.find(class_='employee-details-wrapper')
                        name = wrapper.h3.text.strip()
                        title = wrapper.span.text.strip()
                        line = [ship, name, title, image_url, employee]
                        if line not in lines:
                            print(count/len(rows), count, len(rows))
                            print(line)
                            lines.append(line)
                            self.write_csv(lines=[line], filename=dealer_file)


print('============================= START =============================')
dealer = Dealer()
dealer.get_dealers(html_file='Chevrolet_1.html', save_name='Weber-Chevrolet-Creve-Coeur-dealer-reviews-39422_1.csv')
# dealer.arrange(file='Chevrolet_Dealer_b.csv', new_name='Chevrolet_Dealer_c.csv')
# dealer.image_download(csv_file='Chevrolet_Dealer.csv')

# dealer.dealerShip(fileName='Chevrolet_Dealer.csv', dealer_file='Chevrolet_DealerShip_Again.csv')
print('============================= ENDED =============================')
