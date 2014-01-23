from django.test import LiveServerTestCase
from selenium.webdriver.firefox.webdriver import WebDriver
from django.test.utils import override_settings


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

        browser.get('%s%s' % (self.live_server_url, '/'))
        self.login_user('project_owner', '1')
        self.assertEqual(self.selenium.find_element_by_xpath('//a[@class="username"]').text, 'project_owner')

        browser.find_element_by_xpath('//a[@class="username"]').click()
        browser.find_element_by_xpath('//a[contains(text(), "Create project")]').click()
        browser.find_element_by_name("name").send_keys('Test project')
        browser.find_element_by_name("short_desc").send_keys('Short description')
        browser.find_element_by_name("desc").send_keys('Description')
        browser.find_element_by_name("amount").send_keys('10000')
        browser.find_element_by_xpath('//input[@type="submit"]').click()

        self.assertTrue('Test project' in browser.page_source)

        browser.find_element_by_xpath('//div[@class="project"][1]/a[contains(text(), "Edit")]').click()
        browser.find_element_by_xpath('//button[@class="publish"]').click()

        self.assertTrue('Your project was successfully published' in browser.page_source)

        browser.find_element_by_xpath('//a[contains(text(), "Logout")]').click()
        self.login_user('donator1', '1')
        browser.find_element_by_xpath('//a[@class="username"]').click()
        browser.find_element_by_xpath('//a[contains(text(), "Edit profile")]').click()

        browser.find_element_by_name("first_name").send_keys('First name')
        browser.find_element_by_name("last_name").send_keys('Last name')
        balance = browser.find_element_by_name("balance")
        balance.clear()
        balance.send_keys('200')
        browser.find_element_by_xpath('//input[@type="submit"]').click()

        self.assertEqual(browser.find_element_by_xpath('//span[@class="balance"]').text, '200.00')
