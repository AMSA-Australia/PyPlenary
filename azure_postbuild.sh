#!/bin/bash
cd pyplenary
REDIS_URL= EMAIL_HOST_USER= EMAIL_HOST_PASSWORD= python manage.py collectstatic
