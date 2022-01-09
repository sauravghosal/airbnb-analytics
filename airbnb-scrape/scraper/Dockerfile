FROM public.ecr.aws/lambda/python:3.6

# COPY app.py requirements.txt airbnb_parser.py ./
RUN python3.6 -m pip install -r requirements.txt -t .

ADD bin /bin/

RUN chmod 755 /bin/chromedriver

COPY app.py airbnb_parser.py requirements.txt ./

# Command can be overwritten by providing a different command in the template directly.
CMD ["app.lambda_handler"]