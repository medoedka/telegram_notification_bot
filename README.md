# telegram_notification_bot

This is telegam bot with two-level administration system (administrators and super administartors).
It can helps you to share news and establish effective notification system within your company.

The main idea is to make a list of your company employees in googlesheets and write down their departments for better usability.
After that users can register in the bot by clicking /add command and write down their name and surname (or nickname, or something you like more). The most important thing is that the registered name must be the same as in googlesheet name column. That's how the validation works.
After this simple procedure when all your employees are registered you can send them notification by calling /send function.

How does it work?
Make a special flag column in googlesheet (for example 'mailing (yes/no)') and put positive flag if you need to send this user any notifications.

Where to set the content of your message?
You need to create one more (and the last) column in googlesheets called something like 'message content' and write down your text there. After calling /send function the bot will update googlesheet table, find persons with positive flag, take messages from 'message content' column and send send it to them in telegram.
So at least you have to create 3 columns: name, flag and message content. I recommend you to put more columns like 'department' for quick user filtering and large-scale mailings.

What commands do you have?

For users:
- /start - little instruction about what the user need to do next
- /add - register the user
- /delete - self-erase function (optional, you can comment it)

For administartors (the same as for users and additionally):
- /show - to see the list of users
- /show_admins - to see the list of administrators
- /delete_user - to delete user by id
- /add_admin - to add administrator by id (from current users)

For super administrators (the same as for administrators and additionally):
- /delete_admin - to delete admin (from current administrators)

Bot also have some prohibitions:
User can't add himself twice, delete himself if he didn't register, call admin and super admin functions.

Enjoy new level of communication in your company!
