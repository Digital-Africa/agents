# 🐕 Puppy - Your Data Processing Assistant

## What is this?

Imagine you have a magical post office that automatically sorts and organizes your mail. That's what Puppy does, but for your startup data! 🎯

## How it Works

### The Magic Mailbox (Cloud Storage)
When you drop a CSV file into our special mailbox (Google Cloud Storage), Puppy wakes up and gets to work! It's like having a very efficient mail sorter that knows exactly where each piece of mail should go.

### The Filing Cabinet (Firestore)
Puppy organizes your data into three neat categories, just like a filing cabinet with different drawers:
- 📁 **Startups Drawer**: All your startup information
- 👥 **Cofounders Drawer**: Information about the people behind the startups
- 📝 **Memos Drawer**: Important documents and links

## What Puppy Does

1. **Watches for New Files** 👀
   - Like a vigilant mail carrier, Puppy watches for new files in the mailbox
   - When a new file arrives, it springs into action!

2. **Reads and Organizes** 📚
   - Reads the CSV files (like reading mail)
   - Sorts the information into the right categories
   - Makes sure everything is properly labeled and organized

3. **Stores Everything Safely** 🔒
   - Puts all the information in the right place
   - Makes sure nothing gets lost
   - Keeps track of what's been processed

## Types of Files Puppy Can Handle

- **Startups File**: Contains information about startups (like a company profile)
- **Cofounders File**: Contains information about the people running the startups
- **Memo File**: Contains important documents and links

## Monitoring and Safety

Puppy keeps a detailed log of everything it does, like a security camera in a post office. If something goes wrong, we can check the logs to see what happened and fix it quickly!

## Technical Details (For the Curious)

- Built with Python
- Runs on Google Cloud Functions
- Uses Google Cloud Storage for file storage
- Uses Firestore for data storage
- Includes comprehensive logging for monitoring

## Need Help?

If something goes wrong, don't worry! Puppy keeps detailed logs of everything it does, so we can quickly figure out what happened and fix it. Just like having a security camera in your post office! 🎥

## Fun Fact

The name "Puppy" was chosen because, like a loyal puppy, this system is always watching, always ready to help, and never gets tired of organizing your data! 🐾 