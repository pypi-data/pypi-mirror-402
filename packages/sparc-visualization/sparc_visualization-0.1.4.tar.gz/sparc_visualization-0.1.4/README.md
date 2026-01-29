# Visual SPaRC: Visual Puzzle Representations for the SPaRC benchmark

<div align="center">
    <a href="https://pypi.org/project/sparc-visualization/" style="margin-left:1em; text-decoration:none; font-size:1.1em;">
    <strong>📦 PyPI Package</strong>
    </a>    
  |
  <a href="https://huggingface.co/datasets/lkaesberg/SPaRC" style="margin-left:1em; text-decoration:none; font-size:1.1em;">
    <strong>🤗 SPaRC Dataset</strong>
  </a>
</div>

## Overview

SPaRC (sparc-puzzle) provides a comprehensive framework for evaluating language models on spatial reasoning tasks inspired by "The Witness" puzzle game.
This package (sparc-visualization) includes various visual puzzle representations and an improved visual reasoning prompt to complement the functionality of the sparc-puzzle package.

## Installation

Install the package from PyPI:

```bash
pip install sparc-visualization
```

Or install from source:

```bash
git clone https://github.com/flowun/sparc-visualization.git
cd sparc-visualization
pip install -e .
```



### Example Usage


```python
from sparc_visualization.plot import get_puzzle_image
from sparc_visualization.prompt import generate_prompt
from sparc.validation import extract_solution_path, validate_solution, analyze_path
from datasets import load_dataset

# Load the dataset
dataset = load_dataset("lkaesberg/SPaRC", "all", split="test")
puzzle = dataset[0]

# Generate prompt and image, e.g.
plot_type = "path_cell_annotated"
prompt_type = "prompt_engineering"

b64_image = get_puzzle_image(puzzle, plot_type=plot_type, base_64_image=True)
text_prompt = generate_prompt(puzzle, plot_type, prompt_type)

# create message array and payload for an LLM
puzzle_prompt = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{b64_image}"
                    }
                },
                {
                    "type": "text",
                    "text": text_prompt
                }
            ]
        }
    ]

payload = {
    "model": your_model_name,
    "messages": puzzle_prompt,
    "temperature": temperature,
    "max_tokens": max_tokens,
}

# Your model generates a response
model_response = "... model response with path coordinates ..."

# Analysis using sparc-puzzle package

# Extract the path from model response
extracted_path = extract_solution_path(model_response, puzzle)
# Returns: [{"x": 0, "y": 2}, {"x": 0, "y": 1}, ...]

# Validate against ground truth
is_correct = validate_solution(extracted_path, puzzle)
# Returns: True/False

# Get detailed analysis
analysis = analyze_path(extracted_path, puzzle)
# Returns: {
#   "starts_at_start_ends_at_exit": True,
#   "connected_line": True,
#   "non_intersecting_line": True,
#   "no_rule_crossing": True,
#   "fully_valid_path": True
# }
```

### Core Functions

```text
get_puzzle_image(
    puzzle: Dict,
    plot_type: str = "original",
    base_64_image: bool = False,
    path: List[Tuple[int, int]] | List[Dict[str, int]] | None = None,
    show_plot: bool = False,
    save_to_disk: bool = False,
    save_dir: str = ".",
    save_filename: str = "puzzle_image.png",
) -> PIL.Image.Image | str
```
- Renders a SPaRC puzzle into one of the supported visual representations (`plot_type` values).
- To get a base64-encoded string of the image suitable for LLM input, set `base_64_image=True`.
- To overlay a path, specify `path` either as a list of `(x, y)` tuples or a list of `{"x": int, "y": int}` cells. The full solution path can be displayed by passing puzzle["solutions"][0]["path"] to this argument.
- Besides returning the image object or base64 string, the function has options to display the image (`show_plot=True`) or save it to disk (`save_to_disk=True`).

```text
generate_prompt(
    puzzle: Dict,
    plot_type: str = "original",
    prompt_type: str = "prompt_engineering",
) -> str
```
Generates the text prompt (based on `prompt_type` values) that should be paired with the rendered image for an LLM call.
Available `prompt_type` values are:
- "default_tr": visual prompt from the SPaRC paper (with textual coordinates)
- "default_no_tr": visual prompt from the SPaRC paper (however with textual coordinates removed)
- "prompt_engineering": improved vision-only prompt with prompt engineering (no textual coordinates)
`puzzle` and `plot_type` should be provided the same as in `get_puzzle_image` to allow small prompt adjustments.

### Available Puzzle Representations (`plot_type`)

<table style="width: 100%; table-layout:  fixed;">
  <tr>
    <td align="center" style="width: 33.33%;">
      <code>original</code><br/>
      <img src="https://raw.githubusercontent.com/flowun/sparc-visualization/refs/heads/main/docs/images/original.png" alt="original" style="max-width: 100%; height: auto;" />
    </td>
    <td align="center" style="width: 33.33%;">
      <code>start_end_marked</code><br/>
      <img src="https://raw.githubusercontent.com/flowun/sparc-visualization/refs/heads/main/docs/images/start_end_marked.png" alt="start_end_marked" style="max-width: 100%; height: auto;" />
    </td>
    <td align="center" style="width: 33.33%;">
      <code>coordinate_grid</code><br/>
      <img src="https://raw.githubusercontent.com/flowun/sparc-visualization/refs/heads/main/docs/images/coordinate_grid.png" alt="coordinate_grid" style="max-width: 100%; height: auto;" />
    </td>
  </tr>
  <tr>
    <td align="center" style="width: 33.33%;">
      <code>coordinate_grid_and_start_end_marked</code><br/>
      <img src="https://raw.githubusercontent.com/flowun/sparc-visualization/refs/heads/main/docs/images/coordinate_grid_and_start_end_marked.png" alt="coordinate_grid_and_start_end_marked" style="max-width: 100%; height: auto;" />
    </td>
    <td align="center" style="width: 33.33%;">
      <code>path_cell_annotated</code><br/>
      <img src="https://raw.githubusercontent.com/flowun/sparc-visualization/refs/heads/main/docs/images/path_cell_annotated.png" alt="path_cell_annotated" style="max-width: 100%; height: auto;" />
    </td>
    <td align="center" style="width: 33.33%;">
      <code>text</code><br/>
      <img src="https://raw.githubusercontent.com/flowun/sparc-visualization/refs/heads/main/docs/images/text.png" alt="text" style="max-width: 100%; height: auto;" />
    </td>
  </tr>
  <tr>
    <td align="center" style="width: 33.33%;">
      <code>low_contrast</code><br/>
      <img src="https://raw.githubusercontent.com/flowun/sparc-visualization/refs/heads/main/docs/images/low_contrast.png" alt="low_contrast" style="max-width: 100%; height: auto;" />
    </td>
    <td align="center" style="width: 33.33%;">
      <code>low_contrast_and_path_cell_annotated</code><br/>
      <img src="https://raw.githubusercontent.com/flowun/sparc-visualization/refs/heads/main/docs/images/low_contrast_and_path_cell_annotated.png" alt="low_contrast_and_path_cell_annotated" style="max-width: 100%; height: auto;" />
    </td>
    <td align="center" style="width: 33.33%;">
      <code>low_resolution</code><br/>
      <img src="https://raw.githubusercontent.com/flowun/sparc-visualization/refs/heads/main/docs/images/low_resolution.png" alt="low_resolution" style="max-width: 100%; height: auto;" />
    </td>
  </tr>
  <tr>
    <td align="center" style="width: 33.33%;">
      <code>low_resolution_and_path_cell_annotated</code><br/>
      <img src="https://raw.githubusercontent.com/flowun/sparc-visualization/refs/heads/main/docs/images/low_resolution_and_path_cell_annotated.png" alt="low_resolution_and_path_cell_annotated" style="max-width: 100%; height: auto;" />
    </td>
    <td align="center" style="width: 33.33%;">
      <code>rotated</code><br/>
      <img src="https://raw.githubusercontent.com/flowun/sparc-visualization/refs/heads/main/docs/images/rotated.png" alt="rotated" style="max-width: 100%; height: auto;" />
    </td>
    <td align="center" style="width: 33.33%;">
      <code>rotated_and_path_cell_annotated</code><br/>
      <img src="https://raw.githubusercontent.com/flowun/sparc-visualization/refs/heads/main/docs/images/rotated_and_path_cell_annotated.png" alt="rotated_and_path_cell_annotated" style="max-width: 100%; height: auto;" />
    </td>
  </tr>
  <tr>
    <td align="center" style="width: 33.33%;">
      <code>black_frame</code><br/>
      <img src="https://raw.githubusercontent.com/flowun/sparc-visualization/refs/heads/main/docs/images/black_frame.png" alt="black_frame" style="max-width: 100%; height: auto;" />
    </td>
    <td align="center" style="width: 33.33%;">
      <code>black_frame_and_path_cell_annotated</code><br/>
      <img src="https://raw.githubusercontent.com/flowun/sparc-visualization/refs/heads/main/docs/images/black_frame_and_path_cell_annotated.png" alt="black_frame_and_path_cell_annotated" style="max-width: 100%; height: auto;" />
    </td>
    <td align="center" style="width: 33.33%;"></td>
  </tr>
</table>


## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

## Citation

If you use SPaRC in your research, please cite:

```bibtex
@inproceedings{kaesberg-etal-2025-sparc,
    title = "{SP}a{RC}: A Spatial Pathfinding Reasoning Challenge",
    author = "Kaesberg, Lars Benedikt and Wahle, Jan Philip and Ruas, Terry and Gipp, Bela",
    booktitle = "Proceedings of the 2025 Conference on Empirical Methods in Natural Language Processing",
    month = nov,
    year = "2025",
    address = "Suzhou, China",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/2025.emnlp-main.526/",
    doi = "10.18653/v1/2025.emnlp-main.526",
    pages = "10370--10401"
}
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Links

- 🌐 **Website**: [sparc.gipplab.org](https://sparc.gipplab.org/)
- 📚 **Dataset**: [Hugging Face](https://huggingface.co/datasets/lkaesberg/SPaRC)
- 🐛 **Issues**: [GitHub Issues](https://github.com/flowun/sparc-visualization/issues)
- 📖 **Documentation**: [GitHub Repository](https://github.com/flowun/sparc-visualization)

