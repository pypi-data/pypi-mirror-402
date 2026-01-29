

<img alt="Static Badge" src="https://img.shields.io/badge/version%20-%201.0.0%20-%20green">  

Improved UI because it includes breaking changes.

## Installation

```bash
pip install gradio_improvedfileexplorer
```

## Usage

```python

import gradio as gr
from gradio_improvedfileexplorer import ImprovedFileExplorer


import os

with gr.Blocks() as demo:
    fe = ImprovedFileExplorer(interactive = True, file_count = "multiple")
    fe.change(fn = lambda files: print(files), inputs = fe)

if __name__ == "__main__":
    demo.launch()

```

## `ImprovedFileExplorer`

This component works basically the same as Gradio's original File Explorer, but it has (in my opinion) better UI.

## Changes
### Select single folders
Up to this date, Gradio has a bug that if you allow users to only select folders (`glob = "./**/"`) and `file_count = "single"`, you can not select anything. Look at this [issue](https://github.com/gradio-app/gradio/pull/9835#issuecomment-2490603744).

This problem is solved by changing you select folders. Now the checkbox nect to them select the folder


![](https://github.com/GrunyD/gradio-improved-file-explorer/blob/main/src/image.png?raw=True)

### No recursive selection
When you select folder it no longer selects everything inside nor it opens the file tree. It just selects the folder.


![](https://github.com/GrunyD/gradio-improved-file-explorer/blob/main/src/image_2.png?raw=True)

### Select all contents of a folder
If you need to select all the contents of a folder, you can open the folder and select "Select all contents" whcih will select or deselect everything inside the folder. **It will not select the folder itself*


![](https://github.com/GrunyD/gradio-improved-file-explorer/blob/main/src/image_3.png?raw=True)
