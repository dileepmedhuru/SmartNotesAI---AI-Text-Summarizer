# SmartNotes AI - Complete Setup Guide

## 📁 Project Structure

```
smartnotesAI/
├── static/
│   ├── css/
│   │   └── style.css          # Main stylesheet
│   └── js/
│       ├── main.js             # Main application JavaScript
│       ├── history.js          # History page JavaScript
│       └── admin.js            # Admin dashboard JavaScript
├── templates/
│   ├── index.html              # Main application page
│   ├── login.html              # Login page
│   ├── register.html           # Registration page
│   ├── history.html            # User history page (NEW)
│   └── admin.html              # Admin dashboard (NEW)
├── app.py                      # Main Flask application
├── models.py                   # Database models
├── summarizer.py               # AI summarization logic
├── pdf_handler.py              # File processing
├── init_db.py                  # Database initialization script
├── requirements.txt            # Python dependencies
└── smartnotes.db              # SQLite database (created automatically)
```
INFO:__main__:============================================================
INFO:__main__:TEST USER CREDENTIALS:
INFO:__main__:  Username: admin
INFO:__main__:  Email: admin@smartnotes.com
INFO:__main__:  Password: admin123
INFO:__main__:============================================================
## 🚀 Quick Start

### 1. Create the new files

Create these new files in your project:

**templates/history.html** - Copy from the artifact "history.html"
**templates/admin.html** - Copy from the artifact "admin.html"
**static/js/history.js** - Copy from the artifact "history.js"
**static/js/admin.js** - Copy from the artifact "admin.js"

### 2. Update existing files

**app.py** - Add all the routes from "app.py - Additional Routes" artifact to your existing app.py file. Add them BEFORE the `if __name__ == '__main__':` line.

**templates/index.html** - Replace the user info bar section with the code from "Updated Navigation Links" artifact.

### 3. Install dependencies (if not already done)

```bash
pip install -r requirements.txt
```

### 4. Initialize the database

```bash
python init_db.py
```

This will create:
- Database tables (users, summary_history)
- Test admin account (username: `admin`, password: `admin123`)

### 5. Start the application

```bash
python app.py
```

Visit: http://localhost:5000

## 👥 User Features

### For Regular Users:

1. **Login/Register** at http://localhost:5000/login or http://localhost:5000/register

2. **Create Summaries**
   - Type or paste text manually
   - Upload PDF, DOCX, TXT, or PPTX files
   - Choose summary type (brief, balanced, detailed)
   - Select target language
   - Extract key points

3. **View History** at http://localhost:5000/history
   - See all your past summaries
   - Search and filter summaries
   - View detailed summary information
   - Mark favorites
   - Delete unwanted summaries
   - Copy summaries to clipboard
   - View statistics (total summaries, words processed, etc.)

4. **Features**:
   - Multi-language support (18+ languages)
   - Auto language detection
   - File upload support
   - PDF and text export
   - Summary history tracking
   - Favorites system

## 👑 Admin Features

### For Admin Users:

1. **Login as Admin**
   - Username: `admin`
   - Password: `admin123`

2. **Access Admin Dashboard** at http://localhost:5000/admin

3. **Admin Capabilities**:

   **Dashboard Statistics**:
   - Total users
   - Total summaries
   - Today's activity
   - Average compression ratio
   - Total words processed
   - Most active user
   - Most popular language

   **User Management**:
   - View all registered users
   - See user details (email, join date, activity)
   - View user's summary count
   - Export user data as CSV
   - Search users by name or email

   **Summary Management**:
   - View all summaries from all users
   - See summary details
   - Filter by date, user, language
   - Export summaries as CSV
   - Search summaries

   **Activity Monitor**:
   - Recent user registrations
   - Recent summary creations
   - Real-time activity feed
   - Timeline of system usage

   **Analytics**:
   - Usage statistics
   - User engagement metrics
   - Language distribution
   - Compression statistics

   **Export Features**:
   - Export all users to CSV
   - Export all summaries to CSV
   - Export individual user data
   - Bulk data export

## 🔐 Security Features

- Password hashing with werkzeug
- Session-based authentication with Flask-Login
- Protected admin routes
- CSRF protection
- Secure file upload validation
- SQL injection prevention (SQLAlchemy ORM)

## 📊 Database Schema

### Users Table
```
- id (Primary Key)
- username (Unique)
- email (Unique)
- password_hash
- created_at
- last_login
```

### Summary History Table
```
- id (Primary Key)
- user_id (Foreign Key)
- title
- original_text
- summary_text
- key_points (JSON)
- original_word_count
- summary_word_count
- compression_ratio
- filename
- file_type
- detected_language
- language_name
- target_language
- summary_type
- created_at
- updated_at
- tags
- is_favorite
```

## 🎯 API Endpoints

### User Endpoints
- `GET /` - Main application page
- `GET /login` - Login page
- `POST /login` - Login user
- `GET /register` - Registration page
- `POST /register` - Register new user
- `GET /logout` - Logout user
- `GET /history` - User history page

### API Endpoints
- `POST /summarize` - Summarize text
- `POST /key-points` - Extract key points
- `POST /upload` - Upload file
- `POST /detect-language` - Detect language
- `GET /languages` - Get supported languages
- `POST /download-pdf` - Download as PDF
- `POST /download-text` - Download as text

### History API
- `GET /api/history` - Get user's history (paginated)
- `GET /api/history/<id>` - Get specific history item
- `DELETE /api/history/<id>` - Delete history item
- `POST /api/history/<id>/favorite` - Toggle favorite

### Admin Endpoints
- `GET /admin` - Admin dashboard
- `GET /api/admin/statistics` - System statistics
- `GET /api/admin/users` - All users
- `GET /api/admin/users/<id>` - User details
- `GET /api/admin/summaries` - All summaries
- `GET /api/admin/summaries/<id>` - Summary details
- `GET /api/admin/activity` - Recent activity
- `GET /api/admin/export/users` - Export users CSV
- `GET /api/admin/export/summaries` - Export summaries CSV
- `GET /api/admin/export/user/<id>` - Export user data CSV

## 🛠️ Troubleshooting

### Database Issues
```bash
# Reset database
rm smartnotes.db
python init_db.py
```

### Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

### Admin Access
- Default admin username: `admin`
- Default admin password: `admin123`
- Change admin password after first login!

### File Upload Issues
- Max file size: 16MB
- Supported formats: PDF, TXT, DOCX, DOC, PPTX, PPT
- Check file permissions in temp directory

## 🎨 Customization

### Change Admin Credentials
Edit `init_db.py` to change default admin credentials:
```python
test_user = User(
    username='your_admin_name',
    email='your_admin@email.com'
)
test_user.set_password('your_secure_password')
```

### Add More Admins
You can add multiple admin users by creating additional users with specific usernames, or modify the `admin_required` decorator in `app.py` to check for an `is_admin` flag in the User model.

### Theme Customization
Edit `static/css/style.css` to change colors, fonts, and layout.

## 📝 Usage Examples

### Creating a Summary
1. Login to your account
2. Type or upload text
3. Select summary options
4. Click "Summarize Notes"
5. View results and download if needed

### Viewing History
1. Click history icon in navigation
2. Browse your past summaries
3. Use search to find specific summaries
4. Filter by date or favorites
5. Click on any summary to view details

### Admin Tasks
1. Login as admin
2. Navigate to admin dashboard
3. View statistics on dashboard
4. Switch between tabs (Users, Summaries, Activity, Analytics)
5. Export data as needed
6. Monitor system usage

## 🔄 Updates & Maintenance

### Regular Maintenance
- Backup database regularly: `cp smartnotes.db smartnotes_backup_$(date +%Y%m%d).db`
- Monitor disk space for uploaded files
- Review user activity logs
- Clean up old summaries if needed

### Adding New Features
- All routes should be added to `app.py`
- Frontend files go in `static/` and `templates/`
- Update `requirements.txt` for new dependencies

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review error logs in console
3. Verify all files are in correct locations
4. Ensure all dependencies are installed

## 🎉 You're All Set!

Your SmartNotes AI application now has:
✅ User authentication
✅ Summary history with search and filters
✅ Admin dashboard with full system overview
✅ User management capabilities
✅ Data export features
✅ Activity monitoring
✅ Multi-language support
✅ File upload support

Happy summarizing! 🚀