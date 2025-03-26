import json
import os
from io import StringIO
import openai
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.environ.get("OPENAI_API_KEY")

train_data_file = "./train_data.jsonl"
train_id_file = "./id.txt"
prompt = """provide an professional, one or two sentence commentary for this fencing game picture for 
the audience that is natural and does not delve into too many details. If there is score, provide the
current score, if the picture does not have two people wearing white suit (Fencer), holding the weapon, then provide a summary
of the game so far. If the piste lights up, track the score. Either describe the image, provide tactical insight or track the score.
Consider not only the current game state but also the previous three game states."""

def convert_folder_to_jsonl(folder_path, output_path, prompt):
    with open(output_path, 'w', encoding='utf-8') as out_f:
        for filename in os.listdir(folder_path):
            if filename.endswith('.txt'):
                file_path = os.path.join(folder_path, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()

                paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
                for para in paragraphs:
                    record = {
                        "messages": [
                            {"role": "user", "content": prompt},
                            {"role": "assistant", "content": para}
                        ]
                    }
                    out_f.write(json.dumps(record, ensure_ascii=False) + '\n')

def train_chat():
    with open(train_data_file, "rb") as f:
        file_response = openai.files.create(file=f, purpose="fine-tune")
    
    file_id = file_response.id
    
    fine_tune_response = openai.fine_tuning.jobs.create(
        training_file=file_id,
        model="gpt-3.5-turbo"
    )
    fine_tune_id = fine_tune_response.id
    
    print(f"Fine-tuning job started: {fine_tune_id}")
    
    with open(train_id_file, 'w') as file:
        file.write(fine_tune_id)

def main():
    convert_folder_to_jsonl("./transcript/", train_data_file, prompt.replace("\n", ""))
    train_chat()
    return

if __name__ == "__main__":
    main()