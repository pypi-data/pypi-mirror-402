import sys
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler


def main():
    if len(sys.argv) != 2:
        print("Usage: recommend <csv_file>")
        sys.exit(1)

    file_path = sys.argv[1]

    try:
        data = pd.read_csv(file_path)

        # First column = item names
        items = data.iloc[:, 0]
        features = data.iloc[:, 1:]

        scaler = MinMaxScaler()
        normalized = scaler.fit_transform(features)

        similarity = cosine_similarity(normalized)
        scores = similarity[0]

        result = pd.DataFrame({
            "Item": items,
            "Similarity Score": scores
        })

        result = result.sort_values(
            by="Similarity Score", ascending=False
        ).reset_index(drop=True)

        result["Rank"] = result.index + 1

        print("\nRECOMMENDATION RESULTS")
        print("-" * 30)
        print(result)

    except FileNotFoundError:
        print("Error: CSV file not found.")
    except Exception as e:
        print("Error:", e)


if __name__ == "__main__":
    main()

