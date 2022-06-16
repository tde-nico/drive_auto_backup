# drive_auto_backup

## A Python program to auto backup files on google drive

In order to use thi script you'll need to set first your google account.
Go to "Google App", scroll down and press on "More from Google", 
now scroll down again and press on "Google Cloud" witch you can find into "For Business" or in "For Developers".
You are on the google cloud site. Now you click on "Console" on top-left of the screen, to get to the cloud platform.
Now we need to create our credentials; on the left you'll find "API & Services",
in the sub-menù press on "OAuth consent screen", and then you'll need to create a project, insert the name and create.
Select th "External" option and continue.
Now it will ask for other credentials, the App's name is of your choice,
the "User support email" and the "Developer contact mail" will be the mail that you are using.
Continue and you can skip the "Scopes", because are already specified into the script;
now add a test user using the current email.
Now you can go to "Credentials" and by clicking on "Create Credentials" and on "OAuth client ID",
you will ask to select the Application's type, in this case is "Desktop App", now inster the name of your choice
and you'll get the credential's key, download it as json (this is the "credentials.json" in the script).

The first time that you upload something it will ask you to select a google account,
continue by selecting the same as the previous ones, (you can trust yourself) and continue on this "unverified app"
until it prints "The authentication flow has completed. You may close this window."

Now by closing the tab you'll find an "HttpError 403", visit the link reported in the error, in order to enable the source 
(you will recive the "token.json" file) and after a few minutes you should be able to get the script working.
