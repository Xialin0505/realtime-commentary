import openai
import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv

load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

sample_size = 10

def evaluate_transcript_quality(reference_transcript, test_transcript):

    prompt = f"""
    You are an expert at evaluating the quality of generated transcripts.

    You will receive two inputs: a reference transcript and a test transcript. Ignore speaker names or match participants. 
    Focus ONLY on similarity in tone, structure, commentary style, detail, and semantic meaning.

    Score the quality of the test transcript **from 0 to 5**, where:
    - 0 = completely unrelated
    - 1 = very poor alignment
    - 2 = somewhat relevant but limited
    - 3 = moderately aligned, some issues
    - 4 = good alignment with minor issues
    - 5 = nearly identical in tone and structure

    Output ONLY the number. No explanation.

    Reference Transcript:
    \"\"\"{reference_transcript}\"\"\"

    Test Transcript:
    \"\"\"{test_transcript}\"\"\"
    """
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )

    score = response.choices[0].message.content.strip()
    
    return score

def eval_all_data(folder_path="./text", output_path="./eval.csv"):
    scores = []
    file_name = []
    with open("reference.txt", "r") as f:
        reference = f.read()

    test = []
    idx = 0
    for filename in os.listdir(folder_path):
        if filename.endswith('.txt'):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                test.append(f.read())

                if len(test) == 10:
                    print(f"Processing {(len(scores)/sample_size)*100:.2f}%", end="\r")
                    score = evaluate_transcript_quality(reference, "".join(test))
                    test = []
                    scores.append(score)
                    file_name.append(idx)
                    idx += 1
        
        if len(scores) > sample_size:
            break

    df = pd.DataFrame({
        "filename": file_name,
        "score": scores
    })
    df.to_csv(output_path, index=False)

    return df
    

def plot(data_frame=None, filename=None):
    if data_frame:
        scores = data_frame["score"].tolist()
    elif filename:
        data_frame = pd.read_csv(filename)
        scores = data_frame["score"].tolist()
    else:
        return

    plt.figure(figsize=(8, 5))
    plt.hist(scores, bins=6, edgecolor='black', range=(0, 5))
    plt.xlabel("Score")
    plt.ylabel("Number of Transcripts")
    plt.title("Distribution of Transcript Quality Scores")
    plt.xticks([0, 1, 2, 3, 4, 5])
    plt.grid(axis='y')
    plt.tight_layout()
    plt.show()


def main(file_path=None):
    if not file_path:
        df = eval_all_data()
        plot(df)
    else:
        plot(data_frame=None, filename=file_path)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        main(file_path)
    else:
        main()