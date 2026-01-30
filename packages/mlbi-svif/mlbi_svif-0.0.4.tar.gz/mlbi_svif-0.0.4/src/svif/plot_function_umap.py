from __future__ import annotations

import io
import base64
from dataclasses import dataclass
from typing import Any, Dict, Optional, Sequence, Tuple, Literal, Union, List

import numpy as np
import pandas as pd
import scanpy as sc
import matplotlib.pyplot as plt

from scodaviz import get_abbreviations

