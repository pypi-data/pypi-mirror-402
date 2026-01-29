# cat-aspect-extraction🐈

Easy to use library for implement Contrastive Attention Topic Modeling describe in *Embarrassingly Simple Unsupervised Aspect Extraction*

**Read the paper & the original repository for details about the algorithm !**

- PAPER : https://aclanthology.org/2020.acl-main.290/
- REPOSITORY : https://github.com/clips/cat/

![cat walking on a computer keyboard](https://raw.githubusercontent.com/azaismarc/cat-aspect-extraction/master/cat.gif)

## Installation

```bash
pip install cat-aspect-extraction
```

or

```bash
git clone
python -m pip install .
```

## Example

```python
from cat_aspect_extraction import CAt, RBFAttention # for using the model
from reach import Reach # for loading word embeddings

# Load in-domain word embeddings and create a CAt instance
r = Reach.load("path/to/embeddings", unk_word="UNK")
cat = CAt(r)

# Initialize candidate aspects

candidates = [
    "food",
    "service",
    "ambiance",
    "price",
    "location",
    "experience"
]

for aspect in candidates:
    cat.add_candidate(aspect)

# Add topics

cat.add_topic("food", ["taste", "flavor", "quality", "portion", "menu", "dish", "cuisine", "ingredient"])

cat.add_topic("service", ["staff", "waiter", "waitress", "service", "server", "host", "manager", "bartender"])

cat.add_topic("ambiance", ["atmosphere", "decor", "interior", "design", "lighting", "music", "noise", "vibe"])

# Compute topic score

sentence = "The food was great !".split() # tokenize your sentence

att = RBFAttention() # Using attention

cat.get_scores(sentence, attention=att)
>>> [('food', 1), ('service', 0.5), ('ambiance', 0.0)] # Score are scaled by RobustScaler followed by MinMaxScaler
```

## Citations

**I'm not the author of the original paper**, so if you use this library, please cite the original paper :

```bibtex
@inproceedings{tulkens2020embarrassingly,
    title = "Embarrassingly Simple Unsupervised Aspect Extraction",
    author = "Tulkens, St{\'e}phan  and  van Cranenburgh, Andreas",
    booktitle = "Proceedings of the 58th Annual Meeting of the Association for Computational Linguistics",
    month = jul,
    year = "2020",
    address = "Online",
    publisher = "Association for Computational Linguistics",
    url = "https://www.aclweb.org/anthology/2020.acl-main.290",
    doi = "10.18653/v1/2020.acl-main.290",
    pages = "3182--3187",
}
```

## License

GNU General Public License v3.0