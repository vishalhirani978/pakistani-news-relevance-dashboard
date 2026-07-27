from ml_engine.matcher import match_articles

matches = match_articles()

print("\n")

for match in matches:

    print("=" * 80)

    print("Dawn:")
    print(match["dawn_headline"])

    print()

    print("Ummat:")
    print(match["ummat_headline"])

    print()

    print("Score:", match["score"])

    print("Text Similarity:",
          match["details"]["text_similarity"])

    print("Image Similarity:",
          match["details"]["image_similarity"])