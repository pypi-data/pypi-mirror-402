# Selenium setup

This file is editable; the manual is in the ` ```tspec ` block.

```tspec
manual:
  id: selenium-env
  title: Selenium setup
  tags:
  - selenium
  - web
  - setup
  summary: Install Selenium and browser drivers for UI automation.
  prerequisites:
  - Chrome or Firefox
  - ChromeDriver / GeckoDriver
  steps:
  - title: 1) Install Selenium extras
    body: Install Python extras.
  - title: 2) Install driver
    body: Install the matching driver and add to PATH.
  - title: 3) Run sample
    body: Run a sample spec.
  troubleshooting:
  - title: Driver not found
    body: Set driver path in tspec.toml or PATH.
  references:
  - 'Selenium Documentation: https://www.selenium.dev/documentation/'
  - 'ChromeDriver: https://chromedriver.chromium.org/'
```
