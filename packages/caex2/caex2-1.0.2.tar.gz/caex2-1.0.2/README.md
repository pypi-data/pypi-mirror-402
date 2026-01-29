[![PyPI version](https://badge.fury.io/py/caex2.svg)](https://badge.fury.io/py/caex2)

# CaEx2 (CArpentries EXercises EXtractor)
## What does it do?
No more copy-pasting, automatically extract all exercises from a carpentries lesson.

## How to install?
Install with pip:
```
pip install caex2
```

## How to use?
```commandline
caex2 {LESSON_URL} --output {OPTIONAL_OUTPUT_FILE}
```

### Example
To extract all exercises from the [deep learning lesson](https://github.com/carpentries-incubator/deep-learning-intro):
```commandline
caex2 https://github.com/carpentries-incubator/deep-learning-intro
```
This creates a new file called `exercises-document.md` with all exercises in the lesson,
grouped and ordered by episode.

## Current support
This package currently supports carpentries lessons in the 'old' style, it has been tested on:
* https://github.com/carpentries-incubator/deep-learning-intro
* https://github.com/datacarpentry/r-socialsci (episodes are in Rmarkdown)
* https://github.com/datacarpentry/python-socialsci

## Acknowledgements
This package is based on [this gist](https://gist.github.com/dafnevk/6b235e09d5d72f3a71eb662a72fd3ef2) by Dafne van Kuppevelt (@dafnevk).
