from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationship with summaries
    summaries = db.relationship('SummaryHistory', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def get_summary_count(self):
        """Get total number of summaries for this user"""
        return self.summaries.count()
    
    def get_total_words_processed(self):
        """Calculate total words processed by user"""
        total = db.session.query(db.func.sum(SummaryHistory.original_word_count)).filter_by(user_id=self.id).scalar()
        return total or 0
    
    def __repr__(self):
        return f'<User {self.username}>'

class SummaryHistory(db.Model):
    """Summary history model - Text, PDF, URL support only"""
    __tablename__ = 'summary_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Summary details
    title = db.Column(db.String(200))
    original_text = db.Column(db.Text, nullable=False)
    summary_text = db.Column(db.Text, nullable=False)
    key_points = db.Column(db.JSON)  # Store as JSON array
    
    # Metadata
    original_word_count = db.Column(db.Integer)
    summary_word_count = db.Column(db.Integer)
    compression_ratio = db.Column(db.Float)
    
    # File information
    filename = db.Column(db.String(255))
    file_type = db.Column(db.String(20))
    
    # Language information
    detected_language = db.Column(db.String(10))
    language_name = db.Column(db.String(50))
    target_language = db.Column(db.String(10))
    
    # Summary settings
    summary_type = db.Column(db.String(20))  # brief, balanced, detailed
    
    # Content source type (text, file, url only - NO youtube)
    content_type = db.Column(db.String(20), default='text')  # text, file, url
    content_source = db.Column(db.String(500))  # URL or filename
    
    # URL metadata (for websites)
    url_domain = db.Column(db.String(200))  # Domain name
    url_author = db.Column(db.String(200))  # Article author if available
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Tags and favorites
    tags = db.Column(db.String(255))  # Comma-separated tags
    is_favorite = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        """Convert to dictionary for JSON response"""
        return {
            'id': self.id,
            'title': self.title,
            'original_text': self.original_text[:200] + '...' if self.original_text and len(self.original_text) > 200 else self.original_text,
            'summary_text': self.summary_text,
            'key_points': self.key_points if self.key_points else [],
            'original_word_count': self.original_word_count,
            'summary_word_count': self.summary_word_count,
            'compression_ratio': self.compression_ratio,
            'filename': self.filename,
            'file_type': self.file_type,
            'detected_language': self.detected_language,
            'language_name': self.language_name,
            'summary_type': self.summary_type,
            'content_type': self.content_type,
            'content_source': self.content_source,
            'url_domain': self.url_domain,
            'url_author': self.url_author,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_favorite': self.is_favorite,
            'tags': self.tags.split(',') if self.tags else []
        }
    
    def __repr__(self):
        return f'<SummaryHistory {self.id} - User {self.user_id} - {self.content_type}>'