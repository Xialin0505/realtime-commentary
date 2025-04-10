import openai
import os
import sys
import base64
import pandas as pd
import numpy as np
from collections import defaultdict
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from matplotlib.cm import get_cmap

load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

sample_size = 10
batch_size = 4

def get_image_info(image_path):
        """Returns base64 and MIME type"""
        _, ext = os.path.splitext(image_path)
        ext = ext.lower()[1:]
        mime = f"image/{ext}" if ext in ["jpeg", "jpg", "png"] else None
        if not mime:
            return None, None
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        return b64, mime

def evaluate_transcript_quality(reference_transcript, test_transcript):

    prompt = f"""
    You are an expert at evaluating the quality of generated transcripts.

    You will receive two inputs: a reference transcript and a test transcript. Ignore speaker names or match participants. 
    Focus ONLY on similarity in tone, structure, and the style.
"
    Score the quality of the test transcript **from 0 to 5**, consider the limitation of OpenAI generated transcript, be very lenient.

    Output ONLY the number. No explanation.

    Reference Transcript:
    \"\"\"{reference_transcript}\"\"\"

    Test Transcript:
    \"\"\"{test_transcript}\"\"\"
    """
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
    )

    score = response.choices[0].message.content.strip()
    
    return score

def eval_all_data(folder_path="./text", output_path="./eval.csv"):
    scores = []
    file_name = []
    with open("reference.txt", "r") as f:
        reference = f.read()

    text_files = os.listdir(folder_path)
    text_files = [os.path.join(folder_path, f) for f in text_files if f.endswith(".txt")]
    text_files = sorted(text_files)

    sample_size = len(text_files)
    test = []
    idx = 0
    for i, txt in enumerate(text_files):
        with open(txt, 'r', encoding='utf-8') as f:
            test.append(f.read())

        if len(test) == batch_size:
            print(f"Processing {(i/sample_size)*100:.2f}%", end="\r") 
            score = evaluate_transcript_quality(reference, "".join(test))
            test = []
            scores.append(score)
            file_name.append(idx)
            idx += 1

    if len(test) > 0:
        print(f"Processing {100:.2f}%", end="\r") 
        score = evaluate_transcript_quality(reference, "".join(test))
        test = []
        scores.append(score)
        file_name.append(idx)

    df = pd.DataFrame({
        "score": scores
    })
    df.to_csv(output_path, index=False)


def plot(filename="./eval.csv"): 

    df = pd.read_csv(filename)

    # Define score range
    score_range = range(1, 6)  # Assuming scores are between 1 and 5

    # Count frequencies of each score in each column
    freq_data = pd.DataFrame(index=score_range)
    for col in df.columns:
        freq_data[col] = df[col].value_counts().reindex(score_range, fill_value=0)

    freq_df = pd.DataFrame(index=score_range)
    for col in df.columns:
        freq_df[col] = df[col].value_counts().reindex(score_range, fill_value=0)

    # Plotting
    bar_width = 0.15
    x = np.arange(len(score_range))

    # Use a nicer colormap
    colors = get_cmap('Set2').colors  # 8 soft pastel colors

    plt.figure(figsize=(10, 6))

    for i, (col, color) in enumerate(zip(freq_df.columns, colors)):
        plt.bar(x + i * bar_width, freq_df[col], width=bar_width, label=col, color=color, edgecolor='black')

    # Labels and formatting
    plt.xlabel('Score', fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    plt.title('Score Frequencies by Category', fontsize=14, weight='bold')
    plt.xticks(x + bar_width * (len(freq_df.columns) / 2 - 0.5), score_range)
    plt.legend(title='Category', fontsize=10)
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.show()


def main(file_path=None):
    if not file_path:
        eval_all_data()
        plot()
    else:   
        plot(file_path)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        main(file_path)
    else:
        main()