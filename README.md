# 📖 Daily Bible Diary (Gospel + NKKT Reflection)

Tự động lấy Tin Mừng hằng ngày (Gospel only) từ USCCB, tạo ghi chú thiêng liêng theo format NKKT (3 mục: Kinh thánh nói gì / Bài học / Áp dụng) bằng Google Gemini, rồi gửi email vào 06:00 (Việt Nam) mỗi ngày.

## ✨ Features (Hiện tại)

- 🌅 **Daily Automation**: 06:00 Asia/Ho_Chi_Minh (cron 23:00 UTC ngày trước)
- 📖 **Gospel-Only Scraper**: Lấy đúng phần Tin Mừng (citation + link + full body) tối ưu token
- 🧩 **Structured Fields**: `gospel_citation`, `gospel_link`, `gospel_body` + combined `Gospel`
- 🤖 **Gemini Integration**: Model cấu hình qua `GEMINI_MODEL` (mặc định `gemini-1.5-flash`), retry khi MAX_TOKENS
- 📝 **NKKT Prompt Template**: `template_prompt.txt` (tiếng Việt, placeholder `{date}` & `{bible_content}`)
- 🔁 **Resilient Generation**: Token budget env override `GEMINI_MAX_OUTPUT_TOKENS`; rút gọn prompt khi bị cắt
- 📧 **Multi-Provider Email**: Gmail, SendGrid, Amazon SES; HTML + plain text fallback (nếu sử dụng bản đầy đủ EmailSender)
- 🛡️ **Safe Config**: Secrets không commit; lỗi sẽ tạo GitHub Issue (nếu bật bước notify)
- 🐞 **Debug Mode**: Thêm log chi tiết với `DEBUG=true`

## 🗂️ Tech Overview

| Layer                                     | Purpose                                           |
| ----------------------------------------- | ------------------------------------------------- |
| `bible_fetcher.py`                        | Gọi USCCB -> parse chỉ Gospel                     |
| `gemini_client.py`                        | Format NKKT prompt -> gọi Gemini -> retry khi cần |
| `email_sender.py`                         | Render email (Gospel + NKKT) & gửi qua provider   |
| `template_prompt.txt`                     | NKKT template tiếng Việt chuẩn nhóm               |
| `.github/workflows/daily-bible-diary.yml` | Lên lịch & chạy hằng ngày                         |

## ⚙️ Environment / Secrets

Required GitHub **Secrets** (Settings → Actions → Secrets → New repository secret):

```
GEMINI_API_KEY=xxxxxxxxxxxxxxxx
EMAIL_FROM=your_email@example.com
EMAIL_TO=recipient@example.com            # có thể giống EMAIL_FROM
EMAIL_PASSWORD=app_password_or_api_key    # Gmail App Password / SendGrid API Key / trống nếu SES dùng access keys
```

If using **SendGrid**:

```
EMAIL_PROVIDER=sendgrid
```

If using **Amazon SES**:

```
EMAIL_PROVIDER=ses
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=xxxx
AWS_SECRET_ACCESS_KEY=xxxx
```

Optional **Variables** (Settings → Actions → Variables):

```
EMAIL_PROVIDER=gmail
GEMINI_MODEL=gemini-1.5-flash
GEMINI_MAX_OUTPUT_TOKENS=800
DEBUG=true
```

Local `.env` (không commit):

```
GEMINI_API_KEY=...
EMAIL_FROM=...
EMAIL_TO=...
EMAIL_PASSWORD=...
EMAIL_PROVIDER=gmail
GEMINI_MODEL=gemini-1.5-flash
GEMINI_MAX_OUTPUT_TOKENS=800
DEBUG=true
```

## 🧠 NKKT Prompt Template

File `template_prompt.txt` (rút gọn, tiếng Việt) chứa placeholders:

```
NKKT:{date}

1. Kinh thánh nói gì
... (Gemini sẽ chèn trích câu) ...

2. Bài học
...

3. Áp dụng
...

DỮ LIỆU NGUỒN:
{bible_content}
```

GeminiClient sẽ thay `{date}` dạng `d/m/YYYY` & `{bible_content}` = Gospel (citation + body). Giữ prompt ngắn → ít rủi ro MAX_TOKENS.

## 🚀 Run Locally

```bash
pip install -r requirements.txt
python main.py
```

Nếu cần đổi model nhanh:

```bash
export GEMINI_MODEL=gemini-1.5-pro
python main.py
```

Tăng giới hạn token:

```bash
export GEMINI_MAX_OUTPUT_TOKENS=1200
python main.py
```

## ⏱️ Schedule (GitHub Actions)

Workflow cron: `0 23 * * *` (UTC) → 06:00 GMT+7 ngày kế tiếp tại VN.

Chạy thủ công: Actions tab → chọn workflow → Run workflow.

## 📤 Email Rendering

Email gồm:

1. Header (date)
2. Gospel section (citation + link + full text, paragraph hóa)
3. NKKT Reflection (giữ line breaks)
4. Footer

Muốn đổi giao diện: sửa `_create_email_body` trong `email_sender.py`.

## 🛡️ Error Handling

- Thiếu `GEMINI_API_KEY` → raise ngay trong `Config`
- Model 404 hoặc MAX_TOKENS → log + retry với nhiều token hơn + prompt rút gọn
- Không tìm được Gospel → log error & dừng
- Email fail → log provider-specific error

## 🔍 Troubleshooting (Cập nhật)

| Issue                        | Nguyên nhân                                    | Cách xử lý                                          |
| ---------------------------- | ---------------------------------------------- | --------------------------------------------------- |
| KeyError 'date'              | Template có `{date}` nhưng prompt không truyền | Đã fix: luôn format date trước generation           |
| Model 404                    | `GEMINI_MODEL` cũ (vd gemini-pro)              | Dùng `gemini-1.5-flash` hoặc list models qua API    |
| MAX_TOKENS (finish_reason=2) | Output vượt giới hạn                           | Tăng `GEMINI_MAX_OUTPUT_TOKENS` hoặc rút gọn prompt |
| Email trắng / thiếu Gospel   | Parse USCCB thay đổi                           | Kiểm tra CSS selectors trong `bible_fetcher.py`     |
| Gmail auth fail              | Dùng mật khẩu thường                           | Tạo App Password (2FA)                              |

Kiểm tra log chi tiết: set `DEBUG=true`.

## 🧪 Simple Validation Idea

Bạn có thể thêm bước regex kiểm NKKT trước gửi:

```
^NKKT:\d{1,2}/\d{1,2}/\d{4}\n\n1\. Kinh thánh nói gì\n[\s\S]+?2\. Bài học\n[\s\S]+?3\. Áp dụng\n
```

(Chưa bật mặc định để giảm độ phức tạp.)

## � File Structure (Tóm tắt)

```
automatic_bible_diary/
├── main.py
├── bible_fetcher.py          # Gospel-only scraper
├── gemini_client.py          # Gemini NKKT generator (configurable model)
├── email_sender.py           # Email sender (HTML + providers)
├── config.py                 # Env config validation
├── template_prompt.txt       # NKKT prompt template (VN)
├── requirements.txt          # Dependencies
└── .github/workflows/daily-bible-diary.yml
```

## 🔒 Security Notes

- Không commit secrets / .env
- Giới hạn quyền workflow: chỉ cần `contents: read`
- Thay đổi model qua variable thay vì sửa code

## ➕ Planned Enhancements (Ideas)

- Regex validator cho output NKKT
- Artifact lưu email HTML mỗi ngày
- Multi-language mode (VN + EN song song)
- Cảnh báo khi USCCB thay đổi DOM (hash diff)

## 🙏 Credits

USCCB · Google Gemini · BeautifulSoup · GitHub Actions

Chúc bạn hành trình suy niệm lời Chúa được sâu sắc mỗi ngày! 🌟
