#!/bin/bash
cd pyplenary
SECRET_KEY="tempKey"
python manage.py collectstatic
