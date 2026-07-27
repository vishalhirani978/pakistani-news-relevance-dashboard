from ml_engine.image_similarity import calculate_image_similarity

image1 = "data/raw/images/article_1.webp"
image2 = "data/raw/images/article_2.webp"

score = calculate_image_similarity(image1, image2)

print("Image Similarity:", score)
