from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash
from flask_cors import CORS
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
import json
from summarizer import NoteSummarizer
from pdf_handler import PDFHandler, TextProcessor
from url_processor import WebsiteProcessor, estimate_reading_time, get_domain_name
from models import db, User, SummaryHistory
import logging
import tempfile
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///smartnotes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Allowed file extensions
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'doc', 'pptx', 'ppt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize components
try:
    summarizer = NoteSummarizer()
    pdf_handler = PDFHandler()
    text_processor = TextProcessor()
    website_processor = WebsiteProcessor()
    logger.info("All components initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize components: {e}")
    summarizer = None
    pdf_handler = None
    text_processor = None
    website_processor = None

# Create database tables
with app.app_context():
    db.create_all()
    logger.info("Database tables created successfully")

# ==================== AUTHENTICATION ROUTES ====================

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        data = request.get_json()
        
        username = data.get('username', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not username or not email or not password:
            return jsonify({
                'success': False,
                'error': 'All fields are required'
            }), 400
        
        if len(username) < 3:
            return jsonify({
                'success': False,
                'error': 'Username must be at least 3 characters'
            }), 400
        
        if len(password) < 6:
            return jsonify({
                'success': False,
                'error': 'Password must be at least 6 characters'
            }), 400
        
        if User.query.filter_by(username=username).first():
            return jsonify({
                'success': False,
                'error': 'Username already exists'
            }), 400
        
        if User.query.filter_by(email=email).first():
            return jsonify({
                'success': False,
                'error': 'Email already registered'
            }), 400
        
        try:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            logger.info(f"New user registered: {username}")
            
            return jsonify({
                'success': True,
                'message': 'Registration successful! Please log in.'
            })
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Registration error: {e}")
            return jsonify({
                'success': False,
                'error': 'Registration failed. Please try again.'
            }), 500
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        data = request.get_json()
        
        username_or_email = data.get('username', '').strip().lower()
        password = data.get('password', '')
        remember = data.get('remember', False)
        
        if not username_or_email or not password:
            return jsonify({
                'success': False,
                'error': 'Username/email and password are required'
            }), 400
        
        user = User.query.filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()
        
        if user and user.check_password(password):
            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"User logged in: {user.username}")
            
            return jsonify({
                'success': True,
                'message': 'Login successful!',
                'username': user.username
            })
        
        return jsonify({
            'success': False,
            'error': 'Invalid username/email or password'
        }), 401
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """User logout"""
    username = current_user.username
    logout_user()
    logger.info(f"User logged out: {username}")
    return redirect(url_for('login'))

# ==================== MAIN ROUTES ====================

@app.route('/')
@login_required
def index():
    """Render the main page"""
    return render_template('index.html', user=current_user)

@app.route('/languages', methods=['GET'])
@login_required
def get_languages():
    """Get list of supported languages"""
    try:
        if not summarizer:
            return jsonify({
                'error': 'Summarizer not available',
                'success': False
            }), 500
        
        languages = summarizer.get_supported_languages()
        return jsonify({
            'languages': languages,
            'success': True
        })
        
    except Exception as e:
        logger.error(f"Error getting languages: {e}")
        return jsonify({
            'error': f'Error retrieving languages: {str(e)}',
            'success': False
        }), 500

# ==================== URL PROCESSING ROUTE ====================

@app.route('/process-url', methods=['POST'])
@login_required
def process_url():
    """Process website URL and extract content"""
    try:
        if not website_processor:
            return jsonify({
                'error': 'Content processor not available',
                'success': False
            }), 500
        
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({
                'error': 'Please provide a URL',
                'success': False
            }), 400
        
        logger.info(f"Processing URL: {url}")
        
        result = website_processor.extract_content(url)
        
        if not result.get('success'):
            return jsonify(result), 400
        
        result['reading_time'] = estimate_reading_time(result['word_count'])
        result['domain'] = get_domain_name(url)
        result['content_type'] = 'url'
        
        logger.info(f"Successfully processed URL: {result['title']}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error processing URL: {e}")
        return jsonify({
            'error': f'Failed to process URL: {str(e)}',
            'success': False
        }), 500

# ==================== FILE UPLOAD ROUTE ====================

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """Handle file uploads and extract text"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'error': 'No file uploaded',
                'success': False
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'error': 'No file selected',
                'success': False
            }), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            
            file.save(filepath)
            
            try:
                file_extension = filename.rsplit('.', 1)[1].lower()
                
                if file_extension == 'pdf':
                    text_content = pdf_handler.extract_text_from_pdf(filepath)
                elif file_extension in ['txt']:
                    text_content = text_processor.read_text_file(filepath)
                elif file_extension in ['docx', 'doc']:
                    text_content = text_processor.extract_text_from_docx(filepath)
                elif file_extension in ['pptx', 'ppt']:
                    text_content = text_processor.extract_text_from_pptx(filepath)
                else:
                    return jsonify({
                        'error': 'Unsupported file type',
                        'success': False
                    }), 400
                
                file_size = os.path.getsize(filepath)
                os.remove(filepath)
                
                if not text_content.strip():
                    return jsonify({
                        'error': 'No text could be extracted',
                        'success': False
                    }), 400
                
                detected_lang = 'en'
                language_name = 'English'
                if summarizer:
                    try:
                        detected_lang = summarizer.detect_language(text_content)
                        languages = summarizer.get_supported_languages()
                        language_name = languages.get(detected_lang, 'Unknown')
                    except:
                        pass
                
                word_count = len(text_content.split())
                
                return jsonify({
                    'text': text_content,
                    'filename': filename,
                    'word_count': word_count,
                    'file_type': file_extension,
                    'file_size': file_size,
                    'detected_language': detected_lang,
                    'language_name': language_name,
                    'success': True
                })
                
            except Exception as e:
                if os.path.exists(filepath):
                    os.remove(filepath)
                raise e
        
        return jsonify({
            'error': 'File type not allowed',
            'success': False
        }), 400
        
    except Exception as e:
        logger.error(f"Error in file upload: {e}")
        return jsonify({
            'error': f'File processing error: {str(e)}',
            'success': False
        }), 500

# ==================== SUMMARIZATION ROUTES ====================

@app.route('/summarize', methods=['POST'])
@login_required
def summarize():
    """Handle summarization requests"""
    try:
        if not summarizer:
            return jsonify({
                'error': 'Summarizer not available',
                'success': False
            }), 500
        
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({
                'error': 'No text provided for summarization',
                'success': False
            }), 400
        
        text = data['text'].strip()
        
        if not text:
            return jsonify({
                'error': 'Empty text provided',
                'success': False
            }), 400
        
        max_length = data.get('max_length', 150)
        min_length = data.get('min_length', 50)
        summary_type = data.get('summary_type', 'balanced')
        target_language = data.get('target_language', None)
        save_to_history = data.get('save_to_history', True)
        
        content_type = data.get('content_type', 'text')
        content_source = data.get('content_source', None)
        
        logger.info(f"Summarizing {content_type} content for user {current_user.username}")
        
        result = summarizer.summarize_text(
            text=text,
            max_length=max_length,
            min_length=min_length,
            summary_type=summary_type,
            target_language=target_language
        )
        
        if save_to_history and result.get('summary'):
            try:
                history_entry = SummaryHistory(
                    user_id=current_user.id,
                    title=data.get('title', f"Summary - {datetime.now().strftime('%Y-%m-%d %H:%M')}"),
                    original_text=text,
                    summary_text=result['summary'],
                    key_points=data.get('key_points', []),
                    original_word_count=result.get('original_length'),
                    summary_word_count=result.get('summary_length'),
                    compression_ratio=result.get('compression_ratio'),
                    filename=data.get('filename'),
                    file_type=data.get('file_type'),
                    detected_language=result.get('detected_language'),
                    language_name=result.get('language_name'),
                    target_language=result.get('target_language'),
                    summary_type=summary_type,
                    content_type=content_type,
                    content_source=content_source,
                    url_domain=data.get('url_domain'),
                    url_author=data.get('url_author')
                )
                
                db.session.add(history_entry)
                db.session.commit()
                result['history_id'] = history_entry.id
                logger.info(f"Summary saved to history for user {current_user.username}")
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error saving to history: {e}")
        
        result['success'] = True
        result['timestamp'] = datetime.now().isoformat()
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in summarization: {e}")
        return jsonify({
            'error': f'Summarization failed: {str(e)}',
            'success': False
        }), 500

@app.route('/key-points', methods=['POST'])
@login_required
def extract_key_points():
    """Extract key points from text"""
    try:
        if not summarizer:
            return jsonify({
                'error': 'Summarizer not available',
                'success': False
            }), 500
        
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({
                'error': 'No text provided',
                'success': False
            }), 400
        
        text = data['text'].strip()
        num_points = data.get('num_points', 5)
        target_language = data.get('target_language', None)
        
        if not text:
            return jsonify({
                'error': 'Empty text provided',
                'success': False
            }), 400
        
        logger.info(f"Extracting {num_points} key points from text")
        
        key_points = summarizer.extract_key_points(text, num_points, target_language)
        
        return jsonify({
            'key_points': key_points,
            'num_points': len(key_points),
            'timestamp': datetime.now().isoformat(),
            'success': True
        })
        
    except Exception as e:
        logger.error(f"Error in key points endpoint: {e}")
        return jsonify({
            'error': f'Internal server error: {str(e)}',
            'success': False
        }), 500

# ==================== DOWNLOAD ROUTES ====================

@app.route('/download-pdf', methods=['POST'])
@login_required
def download_pdf():
    """Generate and download PDF report"""
    try:
        if not pdf_handler:
            return jsonify({
                'error': 'PDF handler not available',
                'success': False
            }), 500
        
        data = request.get_json()
        
        required_fields = ['original_text', 'summary', 'key_points']
        if not data or not all(field in data for field in required_fields):
            return jsonify({
                'error': 'Missing required data for PDF generation',
                'success': False
            }), 400
        
        pdf_path = pdf_handler.generate_summary_report(
            original_text=data['original_text'],
            summary=data['summary'],
            key_points=data['key_points'],
            metadata=data.get('metadata', {}),
            filename=data.get('filename', 'summary_report.pdf')
        )
        
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=f"smartnotes_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mimetype='application/pdf'
        )
        
    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        return jsonify({
            'error': f'PDF generation error: {str(e)}',
            'success': False
        }), 500

@app.route('/download-text', methods=['POST'])
@login_required
def download_text():
    """Generate and download text report"""
    try:
        data = request.get_json()
        
        required_fields = ['summary', 'key_points']
        if not data or not all(field in data for field in required_fields):
            return jsonify({
                'error': 'Missing required data for text generation',
                'success': False
            }), 400
        
        report_content = text_processor.generate_text_report(
            summary=data['summary'],
            key_points=data['key_points'],
            metadata=data.get('metadata', {}),
            original_filename=data.get('original_filename', 'Unknown')
        )
        
        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.txt',
            delete=False,
            encoding='utf-8'
        )
        temp_file.write(report_content)
        temp_file.close()
        
        return send_file(
            temp_file.name,
            as_attachment=True,
            download_name=f"smartnotes_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mimetype='text/plain'
        )
        
    except Exception as e:
        logger.error(f"Error generating text report: {e}")
        return jsonify({
            'error': f'Text generation error: {str(e)}',
            'success': False
        }), 500

# ==================== HISTORY ROUTES ====================

@app.route('/history')
@login_required
def history_page():
    """Render the history page"""
    return render_template('history.html', user=current_user)

@app.route('/api/history')
@login_required
def get_history():
    """Get user's summary history"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '')
        
        query = SummaryHistory.query.filter_by(user_id=current_user.id)
        
        if search:
            query = query.filter(
                (SummaryHistory.title.contains(search)) |
                (SummaryHistory.original_text.contains(search)) |
                (SummaryHistory.summary_text.contains(search))
            )
        
        query = query.order_by(SummaryHistory.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'success': True,
            'summaries': [item.to_dict() for item in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        })
        
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        return jsonify({
            'error': 'Failed to retrieve history',
            'success': False
        }), 500

@app.route('/api/history/<int:history_id>')
@login_required
def get_history_item(history_id):
    """Get specific history item"""
    try:
        item = SummaryHistory.query.filter_by(
            id=history_id,
            user_id=current_user.id
        ).first()
        
        if not item:
            return jsonify({
                'error': 'History item not found',
                'success': False
            }), 404
        
        return jsonify({
            'success': True,
            'summary': item.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error getting history item: {e}")
        return jsonify({
            'error': 'Failed to retrieve history item',
            'success': False
        }), 500

@app.route('/api/history/<int:history_id>', methods=['DELETE'])
@login_required
def delete_history_item(history_id):
    """Delete a history item"""
    try:
        item = SummaryHistory.query.filter_by(
            id=history_id,
            user_id=current_user.id
        ).first()
        
        if not item:
            return jsonify({
                'error': 'History item not found',
                'success': False
            }), 404
        
        db.session.delete(item)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'History item deleted'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting history item: {e}")
        return jsonify({
            'error': 'Failed to delete history item',
            'success': False
        }), 500

@app.route('/api/history/<int:history_id>/favorite', methods=['POST'])
@login_required
def toggle_favorite(history_id):
    """Toggle favorite status of a history item"""
    try:
        item = SummaryHistory.query.filter_by(
            id=history_id,
            user_id=current_user.id
        ).first()
        
        if not item:
            return jsonify({
                'error': 'History item not found',
                'success': False
            }), 404
        
        item.is_favorite = not item.is_favorite
        db.session.commit()
        
        return jsonify({
            'success': True,
            'is_favorite': item.is_favorite
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error toggling favorite: {e}")
        return jsonify({
            'error': 'Failed to update favorite status',
            'success': False
        }), 500

# ==================== ADMIN ROUTES ====================

def admin_required(f):
    """Decorator to require admin access"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if current_user.username != 'admin':
            flash('Access denied. Admin privileges required.')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Render admin dashboard"""
    return render_template('admin.html', user=current_user)

@app.route('/api/admin/statistics')
@admin_required
def admin_statistics():
    """Get system statistics for admin dashboard"""
    try:
        from sqlalchemy import func
        
        total_users = User.query.count()
        total_summaries = SummaryHistory.query.count()
        
        today = datetime.utcnow().date()
        today_activity = SummaryHistory.query.filter(
            func.date(SummaryHistory.created_at) == today
        ).count()
        
        avg_compression = db.session.query(
            func.avg(SummaryHistory.compression_ratio)
        ).scalar() or 0
        
        total_words = db.session.query(
            func.sum(SummaryHistory.original_word_count)
        ).scalar() or 0
        
        avg_summary_length = db.session.query(
            func.avg(SummaryHistory.summary_word_count)
        ).scalar() or 0
        
        most_active = db.session.query(
            User.username,
            func.count(SummaryHistory.id).label('count')
        ).join(SummaryHistory).group_by(User.id).order_by(
            func.count(SummaryHistory.id).desc()
        ).first()
        
        most_active_user = most_active[0] if most_active else '-'
        
        popular_lang = db.session.query(
            SummaryHistory.language_name,
            func.count(SummaryHistory.id).label('count')
        ).filter(
            SummaryHistory.language_name.isnot(None)
        ).group_by(SummaryHistory.language_name).order_by(
            func.count(SummaryHistory.id).desc()
        ).first()
        
        popular_language = popular_lang[0] if popular_lang else '-'
        
        return jsonify({
            'success': True,
            'total_users': total_users,
            'total_summaries': total_summaries,
            'today_activity': today_activity,
            'avg_compression': round(avg_compression, 1),
            'total_words': total_words,
            'avg_summary_length': round(avg_summary_length, 0),
            'most_active_user': most_active_user,
            'popular_language': popular_language
        })
        
    except Exception as e:
        logger.error(f"Error getting admin statistics: {e}")
        return jsonify({
            'error': 'Failed to load statistics',
            'success': False
        }), 500

@app.route('/api/admin/users')
@admin_required
def admin_get_users():
    """Get all users for admin dashboard"""
    try:
        users = User.query.order_by(User.created_at.desc()).all()
        
        users_data = []
        for user in users:
            users_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'created_at': user.created_at.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'summary_count': user.get_summary_count(),
                'total_words_processed': user.get_total_words_processed(),
                'is_active': user.last_login is not None
            })
        
        return jsonify({
            'success': True,
            'users': users_data
        })
        
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        return jsonify({
            'error': 'Failed to load users',
            'success': False
        }), 500

@app.route('/api/admin/summaries')
@admin_required
def admin_get_summaries():
    """Get all summaries for admin dashboard"""
    try:
        summaries = db.session.query(
            SummaryHistory,
            User.username
        ).join(User).order_by(SummaryHistory.created_at.desc()).limit(100).all()
        
        summaries_data = []
        for summary, username in summaries:
            summaries_data.append({
                'id': summary.id,
                'title': summary.title,
                'username': username,
                'created_at': summary.created_at.isoformat(),
                'original_word_count': summary.original_word_count,
                'summary_word_count': summary.summary_word_count,
                'compression_ratio': summary.compression_ratio,
                'language_name': summary.language_name,
                'file_type': summary.file_type
            })
        
        return jsonify({
            'success': True,
            'summaries': summaries_data
        })
        
    except Exception as e:
        logger.error(f"Error getting summaries: {e}")
        return jsonify({
            'error': 'Failed to load summaries',
            'success': False
        }), 500

@app.route('/api/admin/activity')
@admin_required
def admin_get_activity():
    """Get recent activity for admin dashboard"""
    try:
        recent_summaries = db.session.query(
            SummaryHistory,
            User.username
        ).join(User).order_by(SummaryHistory.created_at.desc()).limit(20).all()
        
        activities = []
        for summary, username in recent_summaries:
            activities.append({
                'type': 'summary',
                'description': f'Created summary: {summary.title or "Untitled"}',
                'username': username,
                'details': f'{summary.original_word_count} words',
                'timestamp': summary.created_at.isoformat()
            })
        
        recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
        for user in recent_users:
            activities.append({
                'type': 'register',
                'description': f'New user registered',
                'username': user.username,
                'details': user.email,
                'timestamp': user.created_at.isoformat()
            })
        
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify({
            'success': True,
            'activities': activities[:30]
        })
        
    except Exception as e:
        logger.error(f"Error getting activity: {e}")
        return jsonify({
            'error': 'Failed to load activity',
            'success': False
        }), 500

# ==================== HEALTH CHECK ====================

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'summarizer_available': summarizer is not None,
        'pdf_handler_available': pdf_handler is not None,
        'website_processor_available': website_processor is not None,
        'supported_formats': list(ALLOWED_EXTENSIONS),
        'features': {
            'file_upload': True,
            'website_urls': website_processor is not None,
            'multilingual': True,
            'authentication': True
        }
    })
# ==================== ADDITIONAL ADMIN ROUTES ====================

@app.route('/api/admin/users/<int:user_id>')
@admin_required
def admin_get_user_details(user_id):
    """Get detailed information about a specific user"""
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'error': 'User not found',
                'success': False
            }), 404
        
        # Get user's summaries
        summaries = SummaryHistory.query.filter_by(user_id=user_id).all()
        
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'created_at': user.created_at.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'summary_count': len(summaries),
            'total_words_processed': user.get_total_words_processed(),
            'recent_summaries': [
                {
                    'id': s.id,
                    'title': s.title,
                    'created_at': s.created_at.isoformat(),
                    'word_count': s.original_word_count
                }
                for s in summaries[:5]  # Last 5 summaries
            ]
        }
        
        return jsonify({
            'success': True,
            'user': user_data
        })
        
    except Exception as e:
        logger.error(f"Error getting user details: {e}")
        return jsonify({
            'error': 'Failed to load user details',
            'success': False
        }), 500

@app.route('/api/admin/summaries/<int:summary_id>')
@admin_required
def admin_get_summary_details(summary_id):
    """Get detailed information about a specific summary"""
    try:
        summary = db.session.query(
            SummaryHistory,
            User.username
        ).join(User).filter(SummaryHistory.id == summary_id).first()
        
        if not summary:
            return jsonify({
                'error': 'Summary not found',
                'success': False
            }), 404
        
        summary_obj, username = summary
        
        summary_data = {
            'id': summary_obj.id,
            'title': summary_obj.title,
            'username': username,
            'created_at': summary_obj.created_at.isoformat(),
            'original_word_count': summary_obj.original_word_count,
            'summary_word_count': summary_obj.summary_word_count,
            'compression_ratio': summary_obj.compression_ratio,
            'language_name': summary_obj.language_name,
            'summary_text': summary_obj.summary_text,
            'original_text': summary_obj.original_text[:500] + '...' if len(summary_obj.original_text) > 500 else summary_obj.original_text,
            'key_points': summary_obj.key_points,
            'file_type': summary_obj.file_type,
            'content_type': summary_obj.content_type
        }
        
        return jsonify({
            'success': True,
            'summary': summary_data
        })
        
    except Exception as e:
        logger.error(f"Error getting summary details: {e}")
        return jsonify({
            'error': 'Failed to load summary details',
            'success': False
        }), 500

@app.route('/api/admin/export/users')
@admin_required
def export_users_csv():
    """Export all users as CSV"""
    try:
        import csv
        import io
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['ID', 'Username', 'Email', 'Created At', 'Last Login', 'Summary Count', 'Total Words'])
        
        # Get all users
        users = User.query.order_by(User.created_at.desc()).all()
        
        # Write data
        for user in users:
            writer.writerow([
                user.id,
                user.username,
                user.email,
                user.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'Never',
                user.get_summary_count(),
                user.get_total_words_processed()
            ])
        
        # Create response
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'smartnotes_users_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
        
    except Exception as e:
        logger.error(f"Error exporting users: {e}")
        return jsonify({
            'error': 'Failed to export users',
            'success': False
        }), 500

@app.route('/api/admin/export/summaries')
@admin_required
def export_summaries_csv():
    """Export all summaries as CSV"""
    try:
        import csv
        import io
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['ID', 'Title', 'Username', 'Created At', 'Original Words', 'Summary Words', 'Compression %', 'Language', 'Type'])
        
        # Get all summaries with usernames
        summaries = db.session.query(
            SummaryHistory,
            User.username
        ).join(User).order_by(SummaryHistory.created_at.desc()).all()
        
        # Write data
        for summary, username in summaries:
            writer.writerow([
                summary.id,
                summary.title or 'Untitled',
                username,
                summary.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                summary.original_word_count or 0,
                summary.summary_word_count or 0,
                summary.compression_ratio or 0,
                summary.language_name or '-',
                summary.content_type or 'text'
            ])
        
        # Create response
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'smartnotes_summaries_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
        
    except Exception as e:
        logger.error(f"Error exporting summaries: {e}")
        return jsonify({
            'error': 'Failed to export summaries',
            'success': False
        }), 500

@app.route('/api/admin/export/user/<int:user_id>')
@admin_required
def export_user_data_csv(user_id):
    """Export specific user's data as CSV"""
    try:
        import csv
        import io
        
        # Get user
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'error': 'User not found',
                'success': False
            }), 404
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write user info header
        writer.writerow(['USER INFORMATION'])
        writer.writerow(['Username', user.username])
        writer.writerow(['Email', user.email])
        writer.writerow(['Created', user.created_at.strftime('%Y-%m-%d %H:%M:%S')])
        writer.writerow(['Last Login', user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'Never'])
        writer.writerow([])
        
        # Write summaries header
        writer.writerow(['SUMMARIES'])
        writer.writerow(['ID', 'Title', 'Created At', 'Original Words', 'Summary Words', 'Compression %', 'Language'])
        
        # Get user's summaries
        summaries = SummaryHistory.query.filter_by(user_id=user_id).order_by(SummaryHistory.created_at.desc()).all()
        
        # Write summary data
        for summary in summaries:
            writer.writerow([
                summary.id,
                summary.title or 'Untitled',
                summary.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                summary.original_word_count or 0,
                summary.summary_word_count or 0,
                summary.compression_ratio or 0,
                summary.language_name or '-'
            ])
        
        # Create response
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'smartnotes_user_{user.username}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
        
    except Exception as e:
        logger.error(f"Error exporting user data: {e}")
        return jsonify({
            'error': 'Failed to export user data',
            'success': False
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting SmartNotes AI server on port {port}")
    logger.info(f"Features: Files, URLs, Multilingual")
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)