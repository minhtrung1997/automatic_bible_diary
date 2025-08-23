# 📖 Daily Bible Diary Automation

Automatically fetches daily Bible readings from USCCB, generates personalized diary entries using Google Gemini AI, and delivers them via email every day at 6 AM Vietnam time.

## ✨ Features

- 🌅 **Daily Automation**: Runs every day at 6 AM GMT+7 using GitHub Actions
- 📖 **Bible Reading Fetcher**: Scrapes daily readings from USCCB website
- 🤖 **AI-Powered Diary**: Uses Google Gemini to generate thoughtful reflections
- 📧 **Multi-Provider Email**: Supports Gmail, SendGrid, and Amazon SES
- 🔒 **Secure**: All credentials stored as GitHub Secrets
- 🛠️ **Customizable**: Easy to modify prompts and templates

## 🚀 Quick Setup

### 1. Repository Setup

1. Create this repository: `minhtrung1997/automatic_bible_diary`
2. Add all the provided files to your repository
3. Commit and push the changes

### 2. Get Required API Keys

#### Google Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the key for later use

#### Email Service Setup (Choose One)

**Option A: Gmail (Recommended for personal use)**

1. Enable 2-Factor Authentication on your Google account
2. Generate an App Password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
3. Use your Gmail address and the app password

**Option B: SendGrid**

1. Sign up at [SendGrid](https://sendgrid.com)
2. Create an API key in Settings → API Keys
3. Verify your sender email address

**Option C: Amazon SES**

1. Set up AWS account and SES service
2. Verify your email addresses
3. Get AWS Access Key and Secret Key

### 3. Configure GitHub Secrets

Go to your repository → Settings → Secrets and variables → Actions

**Required Secrets:**

```
GEMINI_API_KEY=your_gemini_api_key_here
EMAIL_FROM=your-email@gmail.com
EMAIL_TO=recipient@gmail.com
EMAIL_PASSWORD=your_app_password_or_api_key
```

**For SendGrid (additional):**

```
EMAIL_PROVIDER=sendgrid
```

**For Amazon SES (additional):**

```
EMAIL_PROVIDER=ses
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
```

### 4. Repository Variables (Optional)

In Repository → Settings → Secrets and variables → Actions → Variables tab:

```
EMAIL_PROVIDER=gmail  # or sendgrid, ses
```

## 📅 How It Works

1. **6:00 AM Vietnam Time**: GitHub Actions triggers the workflow
2. **Bible Fetching**: Script accesses USCCB website for today's readings
3. **AI Processing**: Gemini generates a personalized diary entry
4. **Email Delivery**: Formatted email sent to your inbox
5. **Error Handling**: Creates GitHub issue if anything fails

## 🔧 Customization

### Modify the AI Prompt

Edit `template_prompt.txt` to customize how Gemini generates your diary entries:

```text
Your custom prompt here...
Use {bible_content} where you want the readings inserted...
```

### Change Email Template

Modify the `_create_email_body()` method in `email_sender.py` to customize the email format.

### Adjust Schedule

Edit `.github/workflows/daily-bible-diary.yml` to change the execution time:

```yaml
schedule:
  # Daily at 7 AM Vietnam time (12 AM UTC)
  - cron: "0 0 * * *"
```

## 🧪 Testing

### Test Locally

1. Create `.env` file with your secrets:

```bash
GEMINI_API_KEY=your_key
EMAIL_FROM=your_email
EMAIL_TO=recipient_email
EMAIL_PASSWORD=your_password
EMAIL_PROVIDER=gmail
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the script:

```bash
python main.py
```

### Test via GitHub Actions

1. Go to Actions tab in your repository
2. Find "Daily Bible Diary" workflow
3. Click "Run workflow" to test manually

## 📊 Monitoring

### Check Logs

- Go to Actions → Daily Bible Diary → Latest run
- View logs for debugging information

### Failure Notifications

- Failed runs automatically create GitHub issues
- Check Issues tab for error notifications

## 🛡️ Security Best Practices

- ✅ All credentials stored as GitHub Secrets
- ✅ No sensitive data in source code
- ✅ API keys properly secured
- ✅ Input validation for web scraping
- ✅ Error handling throughout

## 📝 File Structure

```
automatic_bible_diary/
├── main.py                          # Main orchestration script
├── bible_fetcher.py                 # USCCB website scraper
├── gemini_client.py                 # Gemini AI integration
├── email_sender.py                  # Multi-provider email sender
├── config.py                        # Configuration management
├── template_prompt.txt              # AI prompt template (customizable)
├── requirements.txt                 # Python dependencies
├── .github/workflows/
│   └── daily-bible-diary.yml       # GitHub Actions workflow
└── README.md                        # This file
```

## 🔧 Troubleshooting

### Common Issues

**1. Workflow Not Running**

- Check if GitHub Actions are enabled for your repository
- Verify the cron schedule format
- Ensure the repository is not private (or you have GitHub Pro)

**2. Bible Fetching Fails**

- USCCB website might be down or changed structure
- Check logs for specific parsing errors
- Script has fallback mechanisms for content extraction

**3. Gemini API Errors**

- Verify API key is correct and active
- Check quota limits on your Gemini account
- Review prompt length (should be under token limits)

**4. Email Sending Fails**

- Verify email credentials and provider settings
- Check spam folder for delivered emails
- For Gmail, ensure App Password is used (not account password)

### Debug Mode

Add this secret to enable detailed logging:

```
DEBUG=true
```

## 📞 Support

### Need Help?

1. Check the [Issues](../../issues) tab for similar problems
2. Create a new issue with:
   - Error logs from GitHub Actions
   - Configuration details (without secrets!)
   - Expected vs actual behavior

### Feature Requests

Open an issue with the "enhancement" label to request new features.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source. Feel free to modify and distribute according to your needs.

## 🙏 Acknowledgments

- **USCCB** for providing daily Bible readings
- **Google Gemini** for AI-powered reflections
- **GitHub Actions** for reliable automation
- **Beautiful Soup** for web scraping capabilities

---

**Enjoy your daily spiritual journey! 🌟**
