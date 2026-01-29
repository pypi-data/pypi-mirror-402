import numpy as np
from sklearn.preprocessing import normalize
from reach import Reach
from collections import Counter
from .attention import Attention
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler, RobustScaler

class CAt():
    """
    Implementation of Contrastive Attention Topic Modeling describe in "Embarrassingly Simple Unsupervised Aspect Extraction"
    
    URL : https://aclanthology.org/2020.acl-main.290

    Calculating attribution topic scores for a list of tokens.
    Scores are computed using an approach based on RBF (Radial Basis Function) similarity functions between tokens and candidate aspects, 
    and then using attention to aggregate scores of topics associated with candidate aspects.
    """

    def __init__(self, r: Reach) -> None:
        """
        Parameters:
        -----------
        - r (Reach) : A reach instance for vectorization
        """
        self.r = r
        self.candidates_matrix = None
        self.topics = []
        self.topics_matrix = None
        self.scaler = Pipeline([
            ('robust_scaler', RobustScaler()),  # Step 1: Remove outlier effects
            ('minmax_scaler', MinMaxScaler())  # Step 2: Scale to [0, 1]
        ])

    def add_candidate(self, aspect: str) -> bool:
        """
        Initialize candidate words for aspect extraction

        Parameters:
        -----------
        - aspect (str) : Candidate word to add

        Returns:
        --------
        - bool : True if the candidate word has been added, False otherwise
        """
        if aspect not in self.r.items: return False
        if self.candidates_matrix is None: self.candidates_matrix = self.r[aspect].reshape(1, -1)
        else: self.candidates_matrix = np.vstack((self.candidates_matrix, self.r[aspect]))
        return True
    
    def add_topic(self, topic: str, aspects: list[str]) -> None:
        """
        Add topic and compute its vector based on its composition (mean vector of multiple words)

        Parameters:
        -----------
        - topic (str) : Name of topic
        - aspects (list[str]) : List of aspects that compose the topic
        """

        self.topics.append(topic)
        topic_vector = normalize(np.mean([self.r[a] for a in aspects if a in self.r.items], axis=0).reshape(1, -1))
        if self.topics_matrix is None: self.topics_matrix = topic_vector
        else: self.topics_matrix = np.vstack((self.topics_matrix, topic_vector.squeeze()))

    def get_scores(self, tokens: list[str], attention_func: Attention) -> list[(str,float)]:
        """
        Compute the score of each topics

        Parameters:
        -----------
        - tokens (list[str]) : A list of tokens for which to compute scores.

        Returns:
        --------
        - list(tuple(str, float)) : A list of tuples containing labels and their associated scores, 
          sorted in descending order of score.
        """

        assert self.candidates_matrix is not None, "No candidate aspects have been initialized"
        assert len(self.topics) > 0, "No labels have been added"

        score = Counter({topic: 0 for topic in self.topics})

        if len(tokens) == 0: return score.most_common() # No tokens to process
        tokens_matrix = np.array([self.r[t] for t in tokens if t in self.r.items])
        if len(tokens_matrix) == 0: return score.most_common() # No tokens to process

        att = attention_func.attention(tokens_matrix, self.candidates_matrix)

        z = att.dot(tokens_matrix)
        x = normalize(z).dot(self.topics_matrix.T)
        scores = x.sum(axis=0)
        
        # Normalize scores between 0 and 1
        scores = self.scaler.fit_transform(scores.reshape(-1, 1)).squeeze()

        for i, topic in enumerate(self.topics):
            score[topic] = scores[i]
        return score.most_common()