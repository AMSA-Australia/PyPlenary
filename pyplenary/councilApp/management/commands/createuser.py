from councilApp.models import *
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

class Command(BaseCommand):
	help = "Create a new user interactively"

	def handle(self, *args, **options):
		name = input("Name: ")
		email = input("Email: ")
		password = None
		while not password:
			password = input("Password: ")
		password2 = None
		while password != password2:
			password2 = input("Password again: ")
		rep = bool(int(input("Rep? [1/0] ")))
		institution = input("Institution? Short name please: ")

		newUser = User.objects.create_user(email, email, password)

		newDelegate = Delegate()
		newDelegate.authClone = newUser
		newDelegate.name = name
		newDelegate.email = email
		newDelegate.rep = True
		newDelegate.institution = Institution.objects.get(shortName=institution)
		newDelegate.save()

		self.stdout.write(self.style.SUCCESS("Created new delegate."))
