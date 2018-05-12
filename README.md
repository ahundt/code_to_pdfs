# Code to PDFs

Utilities and notes for converting code repositories to pdfs.
I created this as a helpful tool for grading assignments.

setup is tested with [homebrew](brew.sh) on mac,
might work with [linuxbrew](http://linuxbrew.sh) on linux,
or you can find the steps to install the equivalent packages
and if you do, please update this readme!

# Bulk clone github repositories

1. set up your [github API token](https://developer.github.com/v3/auth/).

2. Install bulk clone software [https://github.com/muhasturk/gitim](github.com/muhasturk/gitim)

```
git clone https://github.com/muhasturk/gitim
cd gitim
python setup.py
```

3. Run the bulk clone command, substituting your name and token

```
python gitim.py -t <token>  -u <username> -o deep-learning-jhu -d ~/src/p03
```

All github repositories will be cloned.

# Convert repositories to pdfs

1. Install dependencies

Make sure requirements are installed, and `~/.local/bin` is on your `PATH` in your `.bashrc` file:

```
pip2 install tensorflow pypdf2 weasyprint --user --upgrade
brew install librsvg npm node
npm install -g chrome-headless-render-pdf
npm install -g marked
# https://www.princexml.com/ for pdf conversion
brew cask install caskroom/versions/prince-latest
```

- [chrome-headless-render-pdf](https://www.npmjs.com/package/chrome-headless-render-pdf) - for rendering html to pdf
- [marked](https://github.com/markedjs/marked) - for rendering markdown to html
- [node.js](https://changelog.com/posts/install-node-js-with-homebrew-on-os-x) - installer for chrome-headless-render-pdf

2. Run code_to_pdfs.py

```
python code_to_pdfs.py
```

# Troubleshooting

Many people used private urls as if they were public, so it isn't possible to view the `*answers.md` files if it is cloned locally.
Doing a globbed find and replace over the whole
directory seemed to do the trick using the
following string:

```
https://.*blob/master/
```


### brew linking problems

You probably don't need the following `--overwrite` line, but if you see:

```
The formula built, but is not symlinked into /usr/local
```

the following commands will help.
```
brew link --overwrite librsvg
brew link --overwrite npm
```
be very careful if you do it will blast things away!