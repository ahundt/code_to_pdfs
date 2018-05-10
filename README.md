# grading-deep-learning
Utilities and notes for grading assignments

# bulk clone github repositories

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

# convert repositories to pdfs

make sure requirements are installed

```
pip install tensorflow pypdf2
brew install librsvg
# you may / may not need this next line
brew link --overwrite librsvg
```

[MacTex](https://www.tug.org/mactex/)

```
```