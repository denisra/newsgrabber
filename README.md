# Newsgrabber
Grabs news articles from gmail and publish them in pelican.


I like to send links/articles to my gmail account, as a way to save them for further readin/consultation.

I use "virtual addresses" to categorize these emails automatically. For example:

my email address = *my.email@gmail.com*

python articles  = *my.email+python@gmail.com*

ruby articles    = *my.email+ruby@gmail.com*


My goal with this project is to:

- fetch all my emails that match a specific query
- parse its contents
- create an html file for each email

If the email is plain/text, with a single url in it, we'll use the requests library and beautifulsoup to generate an html file.
If the email is multipart (text/html), we'll just save its contents as an html file.

I'm using [pelican](https://github.com/getpelican/pelican/) to generate a static blog, using the above mentioned html files.

Requirements
============

```bash
pip install beaultifulsoup4
pip install requests
pip install google-api-python-client
pip install PyYaml
sudo apt-get install python-html5lib
```


### TODOs


- Create sample config files
- Create a cleanup function to remove email addresses from the final html file (email list provided in the config file)
- Create a package to install all the dependencies automatically
- Add an option to fetch only new messages based on the message id
- Create unittests
- Refactor the create_metadata, create_content and parse_messages functions

