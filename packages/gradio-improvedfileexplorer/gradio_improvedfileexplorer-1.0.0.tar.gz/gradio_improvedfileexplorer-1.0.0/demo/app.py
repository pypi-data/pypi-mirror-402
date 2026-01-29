
import gradio as gr
from gradio_improvedfileexplorer import ImprovedFileExplorer


import os

with gr.Blocks() as demo:
    fe = ImprovedFileExplorer(interactive = True, file_count = "multiple")
    fe.change(fn = lambda files: print(files), inputs = fe)

if __name__ == "__main__":
    demo.launch()
