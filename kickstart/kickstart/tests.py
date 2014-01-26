# coding: utf-8
from django.test import LiveServerTestCase
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.keys import Keys
from django.test.utils import override_settings
from django.core.management import call_command
import time

class KickstartSeleniumTests(LiveServerTestCase):
    fixtures = ['test_data.json']

    @classmethod
    def setUpClass(cls):
        cls.selenium = WebDriver()
        super(KickstartSeleniumTests, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super(KickstartSeleniumTests, cls).tearDownClass()

    def login_user(self, username, password):
        browser = self.selenium
        browser.find_element_by_xpath('//a[contains(text(), "Login")]').click()
        browser.find_element_by_name("username").send_keys(username)
        browser.find_element_by_name("password").send_keys(password)
        browser.find_element_by_xpath('//input[@value="Login"]').click()

    @override_settings(DEBUG=True)
    def test_projects(self):
        browser = self.selenium
        browser.implicitly_wait(2)

        browser.get(self.live_server_url)
        self.login_user('project_owner', '1')
        self.assertEqual(self.selenium.find_element_by_xpath('//a[@class="username"]').text, 'project_owner')

        browser.find_element_by_xpath('//a[@class="username"]').click()
        browser.find_element_by_xpath('//a[contains(text(), "Create project")]').click()
        browser.find_element_by_name("name").send_keys('First test project')
        browser.find_element_by_name("short_desc").send_keys('Short description')
        browser.find_element_by_name("desc").send_keys('Description')
        browser.find_element_by_name("amount").send_keys('10000')
        browser.find_element_by_xpath('//input[@type="submit"]').click()
        time.sleep(2)

        self.assertTrue('First test project' in browser.page_source)

        browser.find_element_by_xpath('//div[@class="project"][1]/a[contains(text(), "Edit")]').click()
        browser.find_element_by_xpath('//div[@class="benefit"][2]/form/input[@name="amount"]').send_keys('1000')
        browser.find_element_by_xpath('//div[@class="benefit"][2]/form/input[@name="text"]').send_keys('Large benefit')
        browser.find_element_by_xpath('//div[@class="benefit"][2]/form/a[@class="save"]').click()
        browser.refresh()

        self.assertTrue('Large benefit' in browser.page_source)

        browser.find_element_by_xpath('//button[@class="publish"]').click()

        self.assertTrue('Your project was successfully published' in browser.page_source)

        browser.find_element_by_xpath('//a[@class="username"]').click()
        browser.find_element_by_xpath('//a[contains(text(), "Create project")]').click()
        browser.find_element_by_name("name").send_keys('Second test project')
        browser.find_element_by_name("short_desc").send_keys('Short description 2')
        browser.find_element_by_name("desc").send_keys('Description 2')
        browser.find_element_by_name("amount").send_keys('200')
        browser.find_element_by_xpath('//input[@type="submit"]').click()
        time.sleep(2)

        self.assertTrue('Second test project' in browser.page_source)

        browser.find_element_by_xpath('//a[@class="username"]').click()
        browser.find_element_by_xpath('//div[@class="project"][2]/a[contains(text(), "Edit")]').click()
        browser.find_element_by_xpath('//button[@class="publish"]').click()

        self.assertTrue('Your project was successfully published' in browser.page_source)

        for user in ('donator1', 'donator2'):
            browser.find_element_by_xpath('//a[contains(text(), "Logout")]').click()
            self.login_user(user, '1')
            browser.find_element_by_xpath('//a[@class="username"]').click()
            browser.find_element_by_xpath('//a[contains(text(), "Edit profile")]').click()
            balance = browser.find_element_by_name("balance")
            balance.clear()
            balance.send_keys('200')
            browser.find_element_by_xpath('//input[@type="submit"]').click()

            self.assertEqual(browser.find_element_by_xpath('//span[@class="balance"]').text, '200.00')

            for project in ('First', 'Second'):
                browser.get(self.live_server_url)
                project_link = browser.find_element_by_xpath('//a[contains(text(), "{0} test project")]'.format(project))
                href = project_link.get_attribute('href')
                browser.get(href)
                benefit_select = Select(browser.find_element_by_name('benefit'))

                if project == 'First':
                    benefit_select.select_by_index(2)
                    browser.find_element_by_xpath('//input[@value="Donate"]').click()

                    self.assertTrue('Not enough bucks on balance' in browser.page_source)

                benefit_select.select_by_index(1)
                browser.find_element_by_xpath('//input[@value="Donate"]').click()
                time.sleep(1)

                if user == 'donator1':
                    self.assertEqual(browser.find_element_by_xpath('//div[@class="collected amount"]').text, '100.00')
                    self.assertEqual(browser.find_element_by_xpath('//div[@class="donators"]').text, '1')
                else:
                    self.assertEqual(browser.find_element_by_xpath('//div[@class="collected amount"]').text, '200.00')
                    self.assertEqual(browser.find_element_by_xpath('//div[@class="donators"]').text, '2')

                if project == 'First':
                    self.assertEqual(browser.find_element_by_xpath('//span[@class="balance"]').text, '100.00')
                else:
                    self.assertEqual(browser.find_element_by_xpath('//span[@class="balance"]').text, '0.00')

        browser.find_element_by_xpath('//a[contains(text(), "Logout")]').click()
        self.login_user('project_owner', '1')
        browser.find_element_by_xpath('//a[@class="username"]').click()
        browser.find_element_by_xpath('//div[@class="project"][1]/a[contains(text(), "Edit")]').click()
        deadline = browser.find_element_by_name('deadline')
        deadline.clear()
        deadline.send_keys('2014-01-01 10:00:00' + Keys.ENTER)
        time.sleep(1)
        browser.find_element_by_xpath('//input[@value="Save"]').click()

        browser.find_element_by_xpath('//div[@class="project"][2]/a[contains(text(), "Edit")]').click()
        deadline = browser.find_element_by_name('deadline')
        deadline.clear()
        deadline.send_keys('2014-01-01 10:00:00' + Keys.ENTER)
        time.sleep(1)
        browser.find_element_by_xpath('//input[@value="Save"]').click()

        browser.get(self.live_server_url)
        self.assertFalse('First test project' in browser.page_source)
        self.assertFalse('Second test project' in browser.page_source)

        call_command('closeprojects')

        browser.find_element_by_xpath('//a[@class="username"]').click()        
        browser.find_element_by_xpath('//div[@class="project"][1]/h2/a').click()

        self.assertEqual(browser.find_element_by_xpath('//div[@class="status"]').text, 'Fail')

        browser.find_element_by_xpath('//a[@class="username"]').click()        
        browser.find_element_by_xpath('//div[@class="project"][2]/h2/a').click()

        self.assertEqual(browser.find_element_by_xpath('//div[@class="status"]').text, 'Success')

        for user in ('donator1', 'donator2'):
            browser.find_element_by_xpath('//a[contains(text(), "Logout")]').click()
            self.login_user(user, '1')
            self.assertEqual(browser.find_element_by_xpath('//span[@class="balance"]').text, '100.00')
