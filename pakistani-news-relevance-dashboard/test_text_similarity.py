from ml_engine.text_similarity import calculate_text_similarity

headline1 = "Pakistan defeats India in Asia Cup"

headline2 = "Pakistan beats India in Asia Cup"

score = calculate_text_similarity(headline1, headline2)

print("Similarity:", score)