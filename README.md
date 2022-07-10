# movie-recommender-based-on-movielens-tag


1. This movie recommender application is built using the Movielens dataset. https://grouplens.org/datasets/movielens/
2. It makes use of the latest MovieLens Tag Genome Dataset 2021.
3. This application provides movie recommendations for search queries based on 
   a. Genre, 
   b. Movie name that starts with the search prefix, 
   c. Popular tags (imdb top 250,...), 
   d. Composite tags (romatic comedy)
4. This application is deployed and hosted in AWS lambda.
5. This application exposes a REST API to the public. 
6. The end user / customer just need to call this REST API with the search query. 
The search results will contain similar title recommendations followed by recommendations based on pre-sorted tags from the MovieLens Genome Dataset 2021.
