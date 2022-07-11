FROM public.ecr.aws/lambda/python:3.9

COPY app.py requirements.txt md2.csv cosine_similarity_recommender_df.csv ./


RUN python3.9 -m pip install -r requirements.txt -t .

CMD ["app.lambda_handler"]
