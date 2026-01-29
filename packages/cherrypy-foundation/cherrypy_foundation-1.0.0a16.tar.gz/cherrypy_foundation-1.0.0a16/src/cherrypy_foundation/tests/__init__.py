# CherryPy foundation
# Copyright (C) 2026 IKUS Software
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import tempfile
import unittest
from contextlib import contextmanager

from selenium import webdriver


class SeleniumUnitTest:

    @property
    def _session_id(self):
        if hasattr(self, 'cookies') and self.cookies:
            for unused, value in self.cookies:
                for part in value.split(';'):
                    key, unused, value = part.partition('=')
                    if key == 'session_id':
                        return value

    @contextmanager
    def selenium(self, headless=True, implicitly_wait=3):
        """
        Decorator to load selenium for a test.
        """
        # Skip selenium test is display is not available.
        if not os.environ.get('DISPLAY', False):
            raise unittest.SkipTest("selenium require a display")
        # Start selenium driver
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1280,800')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--lang=en-US')
        driver = webdriver.Chrome(options=options)
        try:
            # If logged in, reuse the same session id.
            if self._session_id:
                driver.get(f'{self.baseurl}/login/')
                driver.add_cookie({"name": "session_id", "value": self.session_id})
            # Configure download folder
            download = os.path.join(os.path.expanduser('~'), 'Downloads')
            os.makedirs(download, exist_ok=True)
            self._selenium_download_dir = tempfile.mkdtemp(dir=download, prefix='selenium-download-')
            driver.execute_cdp_cmd(
                'Page.setDownloadBehavior', {'behavior': 'allow', 'downloadPath': self._selenium_download_dir}
            )
            # Set default wait.
            driver.implicitly_wait(implicitly_wait)
            yield driver
        finally:
            # Code to release resource, e.g.:
            driver.close()
            driver = None
