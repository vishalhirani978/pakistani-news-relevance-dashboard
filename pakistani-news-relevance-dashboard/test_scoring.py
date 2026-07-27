from ml_engine.scoring import calculate_relevance

headline1 = "Pakistan defeats India in Asia Cup"

headline2 = "Pakistan beats India in Asia Cup"

image1 = "data/raw/images/article_1.webp"
image2 = "data/raw/images/article_2.webp"

result = calculate_relevance(
    headline1,
    headline2,
    image1,
    image2
)

print(result)