# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pandas",
#     "matplotlib",
#     "seaborn",
#     "pillow",
#     "requests",
#     "httpx",
#     "platformdirs",
#     "python-dotenv",
#     "rich",
#     "python-dotenv",
# ]
# ///

import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image
from PIL.Image import Resampling
import requests
from dotenv import load_dotenv

load_dotenv()
aip_token = os.getenv('AIPROXY_TOKEN')


# Function to load the data from a CSV file
def load_data(file_name):
    """
    Loads the CSV file with fallback encodings in case of Unicode errors.
    """
    try:
        data = pd.read_csv(file_name, encoding="utf-8")
        return data
    except UnicodeDecodeError:
        print("UTF-8 decoding failed. Retrying with 'latin1' encoding...")
        try:
            data = pd.read_csv(file_name, encoding="latin1")
            return data
        except Exception as e:
            print(f"An error occurred while loading the file: {e}")
            raise

# Perform basic analysis on the dataset (summary statistics, missing values)
def basic_analysis(data):
    summary = {
        "shape": data.shape,
        "columns": data.dtypes.to_dict(),
        "missing_values": data.isnull().sum().to_dict(),
        "summary_statistics": data.describe(include="all").to_dict(),
    }
    return summary

# Generate visualizations (such as heatmap) for correlation matrix
def generate_visualizations(data, output_file="heatmap.png", image_size=(512, 512)):
    # Select only numeric columns for correlation
    numeric_data = data.select_dtypes(include=["number"])

    if numeric_data.shape[1] < 2:  # Check if there are at least 2 numeric columns
        print("Not enough numeric columns for correlation analysis.")
        return

    # Dynamically adjust the figure size based on the number of columns
    num_cols = numeric_data.shape[1]
    fig_width = max(10, num_cols * 1.5)
    fig_height = max(10, num_cols * 1.5)

    # Plot the heatmap
    plt.figure(figsize=(fig_width, fig_height))
    sns.heatmap(
        numeric_data.corr(),
        annot=True,
        cmap="coolwarm",
        fmt=".2f",
        annot_kws={"size": 18},  # Increased annotation font size
        cbar_kws={"label": "Correlation Coefficient"}  # Add label to the color bar
    )
    plt.title("Correlation Heatmap", fontsize=20)  # Increased title font size
    plt.xticks(fontsize=18)  # Increased font size for column labels
    plt.yticks(fontsize=18)  # Increased font size for row labels

    # Save the plot
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)  # Save with high resolution
    plt.close()

    # Resize the saved image to the desired size
    resize_image(output_file, output_file, size=image_size)
    print(f"Heatmap saved as {output_file} with size {image_size}.")

# Function to resize images to the desired output size
def resize_image(input_file, output_file, size=(512, 512)):
    """Resize an image to the specified dimensions."""
    with Image.open(input_file) as img:
        img = img.resize(size, Resampling.LANCZOS)
        img.save(output_file)

# Function to interact with LLM API and generate a story
def ask_llm(prompt):
    chat_url = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
    api_key = aip_token  # Replace with your actual API key
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-4o-mini",  # Update the model as per availability
        "messages": [{"role": "system", "content": prompt}],
        "max_tokens": 1500  # Adjust as needed
    }

    response = requests.post(chat_url, headers=headers, json=payload)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

# Function to generate a technical blog post or report from analysis results
def narrate_story(data_summary, analysis_results, api_key):
    prompt = f"""
    Create a story from the following analysis:

    ### Data Summary:
    {data_summary}

    ### Analysis Results:
    {analysis_results}

    Include insights, implications, and next steps in the story. Write it like a technical blog post.
    """
    story = ask_llm(prompt)
    if story:
        return f"Generated story:\n{story}"  # Assuming the API returns valid text or data
    else:
        return "No story generated due to API issues."

# Function to write the final report and visualizations into a README
def write(data, file_name):
    api_key = os.getenv('AIPROXY_TOKEN')  # Get your API token from environment variables
    summary = basic_analysis(data)

    generate_visualizations(data)

    story = narrate_story(str(summary), "No advanced analysis for now.", api_key)

    with open("README.md", "w") as f:
        f.write("# Automated Analysis\n\n")
        f.write(story or "Unable to generate a story. Please check the API or your data.")
        f.write("\n\n## Visualizations\n")
        f.write("![Correlation Matrix](heatmap.png)\n")

# Main function to load the data, perform analysis, and save the results
def main():
    # Ensure a dataset file name is provided
    if len(sys.argv) != 2:
        print("Usage: python autolysis.py <dataset.csv>")
        sys.exit(1)

    # Get the dataset name from the command-line argument
    file_name = sys.argv[1]
    print(f"Processing dataset: {file_name}")

    # Load the data
    try:
        data = load_data(file_name)
        print(f"Dataset loaded successfully with {data.shape[0]} rows and {data.shape[1]} columns.")
    except Exception as e:
        print(f"Failed to process the dataset: {e}")
        sys.exit(1)

    # Perform operations on the dataset (e.g., calling the write function)
    try:
        write(data, file_name)
        print("Data processing completed successfully.")
    except Exception as e:
        print(f"An error occurred during data processing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

